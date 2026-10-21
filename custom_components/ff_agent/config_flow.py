"""Configure independent FF Agent services without contacting FF Agent."""

from ipaddress import ip_address
from uuid import UUID

import probatio as vol
from homeassistant import config_entries
from homeassistant.components import webhook
from homeassistant.components.http import current_request
from homeassistant.const import CONF_NAME, CONF_WEBHOOK_ID
from homeassistant.core import callback
from homeassistant.helpers.network import NoURLAvailableError, get_url
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)
from yarl import URL

from .const import CONF_REPLY_ID, CONF_TRANSPORT, DOMAIN


@callback
def webhook_details(hass, webhook_id: str) -> tuple[str, bool]:
    """Prefer external HTTPS; classify the displayed host, not its URL source."""
    path = webhook.async_generate_path(webhook_id)
    try:
        base_url = get_url(
            hass,
            require_ssl=True,
            allow_internal=False,
            allow_cloud=False,
            allow_ip=False,
        )
    except NoURLAvailableError:
        if request := current_request.get():
            base_url = str(request.url.origin())
        else:
            base_url = get_url(hass, allow_external=False, allow_cloud=False)
    host = URL(base_url).host.lower().rstrip(".")
    try:
        local_only = not ip_address(host).is_global
    except ValueError:
        local_only = "." not in host or host.endswith(
            (".localhost", ".local", ".lan", ".home", ".home.arpa", ".internal")
        )
    return f"{base_url}{path}", local_only


class FFAgentConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Create one entry and one stable webhook per organization."""

    VERSION = 1

    def __init__(self) -> None:
        """Keep uncommitted settings private to this flow."""
        self._settings: dict = {}
        self._webhook_id = webhook.async_generate_id()

    async def async_step_user(self, user_input=None):
        """Collect service settings."""
        return await self._async_settings(user_input, "user")

    async def async_step_reconfigure(self, user_input=None):
        """Edit settings without changing the service's webhook."""
        return await self._async_settings(user_input, "reconfigure")

    async def _async_settings(self, user_input, step_id):
        entry = self._get_reconfigure_entry() if step_id == "reconfigure" else None
        defaults = user_input or (entry.data if entry else {})
        errors = {}
        if user_input is not None:
            settings = dict(user_input)
            settings[CONF_NAME] = settings[CONF_NAME].strip()
            settings[CONF_TRANSPORT] = settings[CONF_TRANSPORT].upper()
            if not settings[CONF_NAME]:
                errors[CONF_NAME] = "name_required"
            try:
                reply_id = settings[CONF_REPLY_ID].strip()
                settings[CONF_REPLY_ID] = str(UUID(reply_id))
                if settings[CONF_REPLY_ID] != reply_id.lower():
                    raise ValueError("Use the UUID in hyphenated form")
            except ValueError:
                errors[CONF_REPLY_ID] = "invalid_reply_id"
            if not errors:
                if any(
                    other.entry_id != (entry.entry_id if entry else None)
                    and other.data[CONF_REPLY_ID] == settings[CONF_REPLY_ID]
                    for other in self._async_current_entries()
                ):
                    errors[CONF_REPLY_ID] = "already_configured"
                elif entry:
                    return self.async_update_reload_and_abort(
                        entry,
                        title=settings[CONF_NAME],
                        data={**entry.data, **settings},
                    )
                else:
                    self._settings = settings
                    return await self.async_step_webhook()

        return self.async_show_form(
            step_id=step_id,
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_NAME, default=defaults.get(CONF_NAME, "")
                    ): TextSelector(),
                    vol.Required(
                        CONF_REPLY_ID, default=defaults.get(CONF_REPLY_ID, "")
                    ): TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD)),
                    vol.Required(
                        CONF_TRANSPORT,
                        default=defaults.get(CONF_TRANSPORT, "CAR").lower(),
                    ): SelectSelector(
                        SelectSelectorConfig(
                            options=["car", "bicycle", "feet"],
                            mode=SelectSelectorMode.DROPDOWN,
                            translation_key="transport",
                        )
                    ),
                }
            ),
            errors=errors,
        )

    async def async_step_webhook(self, user_input=None):
        """Display the generated webhook before saving the service."""
        if user_input is not None:
            if any(
                entry.data[CONF_REPLY_ID] == self._settings[CONF_REPLY_ID]
                for entry in self._async_current_entries()
            ):
                return self.async_abort(reason="already_configured")
            return self.async_create_entry(
                title=self._settings[CONF_NAME],
                data={**self._settings, CONF_WEBHOOK_ID: self._webhook_id},
            )
        url, local_only = webhook_details(self.hass, self._webhook_id)
        return self.async_show_form(
            step_id="webhook_local" if local_only else "webhook",
            data_schema=vol.Schema({}),
            description_placeholders={"webhook_url": url},
            last_step=True,
        )

    async def async_step_webhook_local(self, user_input=None):
        """Complete setup after displaying the local-only warning."""
        return await self.async_step_webhook(user_input)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Allow the webhook to be viewed again without rotating its secret."""
        return FFAgentOptionsFlow()


class FFAgentOptionsFlow(config_entries.OptionsFlow):
    """Display the service's current webhook address."""

    async def async_step_init(self, user_input=None):
        """The native reconfigure action edits settings; options shows the hook."""
        if user_input is not None:
            return self.async_create_entry(data={})
        url, local_only = webhook_details(
            self.hass, self.config_entry.data[CONF_WEBHOOK_ID]
        )
        return self.async_show_form(
            step_id="local" if local_only else "init",
            data_schema=vol.Schema({}),
            description_placeholders={"webhook_url": url},
        )

    async def async_step_local(self, user_input=None):
        """Close the local-only webhook information."""
        return await self.async_step_init(user_input)
