"""Local alarm lifetime and explicit personal FF-Agent replies."""

import asyncio
import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers.event import async_track_point_in_utc_time
from homeassistant.helpers.httpx_client import get_async_client
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util
from httpx import RequestError

from .const import CONF_REPLY_ID, CONF_TRANSPORT, DOMAIN

_LOGGER = logging.getLogger(__name__)
ALARM_DURATION = timedelta(hours=4)


class FFAgentCoordinator(DataUpdateCoordinator[None]):
    """Own one organization's push state, persisted deadline and reply actions."""

    def __init__(self, hass: HomeAssistant, entry) -> None:
        """Initialize without polling or sending any request."""
        super().__init__(hass, _LOGGER, config_entry=entry, name=entry.title)
        self.entry = entry
        self.expires_at = None
        self.reply_status = "pending"
        self._store = Store(hass, 1, f"{DOMAIN}.{entry.entry_id}")
        self._cancel_expiry = None
        self._reply_lock = asyncio.Lock()
        self._unloaded = False

    @property
    def alarm_active(self) -> bool:
        """Never consider an expired alarm active, even before its timer runs."""
        return (
            not self._unloaded
            and self.expires_at is not None
            and self.expires_at > dt_util.utcnow()
        )

    async def async_initialize(self) -> None:
        """Restore the original deadline rather than starting another four hours."""
        if data := await self._store.async_load():
            self.reply_status = data["reply_status"]
            if data["expires_at"]:
                self.expires_at = dt_util.parse_datetime(data["expires_at"])
        if self.alarm_active:
            self._schedule_expiry()
        else:
            self.expires_at = None
        self.entry.async_on_unload(self.async_unload)

    async def async_unload(self) -> None:
        """Flush state before a reload can restore it and stop the old timer."""
        self._unloaded = True
        self.async_cancel_expiry()
        await self._store.async_save(self._stored_state())

    @callback
    def async_alarm(self) -> None:
        """Start a bounded alarm; repeated hooks do not erase a sent decision."""
        if self.alarm_active:
            return
        self.expires_at = dt_util.utcnow() + ALARM_DURATION
        self.reply_status = "pending"
        self._schedule_expiry()
        self._publish()

    @callback
    def _schedule_expiry(self) -> None:
        self.async_cancel_expiry()
        self._cancel_expiry = async_track_point_in_utc_time(
            self.hass, self.async_end_alarm, self.expires_at
        )

    @callback
    def async_cancel_expiry(self) -> None:
        """Cancel the timer when unloading or ending the alarm."""
        if self._cancel_expiry:
            self._cancel_expiry()
            self._cancel_expiry = None

    @callback
    def async_end_alarm(self, _now=None) -> None:
        """End only the local alarm, retaining the last reply and sending nothing."""
        self.async_cancel_expiry()
        self.expires_at = None
        self._publish()

    @callback
    def _stored_state(self) -> dict:
        return {
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "reply_status": self.reply_status,
        }

    @callback
    def _publish(self) -> None:
        self._store.async_delay_save(self._stored_state)
        self.async_update_listeners()

    async def async_reply(self, decision: str) -> None:
        """Send once, with no redirects/retries or optimistic status changes."""
        deadline = self.expires_at
        async with self._reply_lock:
            if not self.alarm_active:
                raise ServiceValidationError(
                    translation_domain=DOMAIN, translation_key="no_local_alarm"
                )
            if self.expires_at != deadline:
                raise ServiceValidationError(
                    translation_domain=DOMAIN, translation_key="alarm_changed"
                )
            params = None
            if decision == "accept":
                params = {
                    "transport": self.entry.data[CONF_TRANSPORT],
                    "lat": self.hass.config.latitude,
                    "lng": self.hass.config.longitude,
                }
            url = (
                "https://www.ff-agent.com/app2/missionreplies/"
                f"{self.entry.data[CONF_REPLY_ID]}/{decision}"
            )
            try:
                async with asyncio.timeout(5):
                    response = await get_async_client(self.hass).get(
                        url, params=params, timeout=5, follow_redirects=False
                    )
            except (RequestError, TimeoutError):
                raise HomeAssistantError(
                    translation_domain=DOMAIN, translation_key="reply_unconfirmed"
                ) from None
            body = response.text.strip()
            if (
                200 <= response.status_code < 300
                and body == "Updated MissionStatus: kein passender Einsatz aktiv"
            ):
                raise ServiceValidationError(
                    translation_domain=DOMAIN, translation_key="no_active_incident"
                )
            if not 200 <= response.status_code < 300:
                raise HomeAssistantError(
                    translation_domain=DOMAIN, translation_key="reply_unconfirmed"
                )
            if self.expires_at != deadline or not self.alarm_active:
                raise HomeAssistantError(
                    translation_domain=DOMAIN, translation_key="alarm_changed"
                )
            self.reply_status = "accepted" if decision == "accept" else "rejected"
            if decision == "reject":
                self.async_end_alarm()
            else:
                self._publish()
