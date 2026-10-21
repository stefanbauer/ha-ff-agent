"""Alarm activity and explicit actions for each FF Agent organization."""

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.helpers import entity_platform

from .entity import FFAgentEntity


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    """Expose the alarm and targetable actions without extra button entities."""
    async_add_entities([FFAgentAlarm(entry.runtime_data)])
    platform = entity_platform.async_get_current_platform()
    platform.async_register_entity_service("accept", {}, "async_accept")
    platform.async_register_entity_service("reject", {}, "async_reject")
    platform.async_register_entity_service("end_alarm", {}, "async_end_alarm")


class FFAgentAlarm(FFAgentEntity, BinarySensorEntity):
    """Indicate a local alarm, independently of the personal reply."""

    _attr_translation_key = "alarm_active"
    _attr_icon = "mdi:alarm-light"

    @property
    def is_on(self) -> bool:
        """Return whether the alarm is still inside its original four hours."""
        return self.coordinator.alarm_active

    @property
    def extra_state_attributes(self) -> dict:
        """Expose the fixed deadline for automations and future cards."""
        return {"expires_at": self.coordinator.expires_at}

    async def async_accept(self) -> None:
        """Send acceptance with configured transport and HA home coordinates."""
        await self.coordinator.async_reply("accept")

    async def async_reject(self) -> None:
        """Send rejection without coordinates or transport."""
        await self.coordinator.async_reply("reject")

    async def async_end_alarm(self) -> None:
        """End the local alarm without sending a provider request."""
        self.coordinator.async_end_alarm()
