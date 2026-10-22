"""FF Agent service configuration and minimal alarm webhook reception."""

from pathlib import Path

from aiohttp import web
from homeassistant.components import frontend, webhook
from homeassistant.components.http import StaticPathConfig
from homeassistant.components.lovelace.const import LOVELACE_DATA
from homeassistant.components.lovelace.resources import ResourceStorageCollection
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_WEBHOOK_ID, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.storage import Store
from homeassistant.helpers.typing import ConfigType
from homeassistant.loader import async_get_integration

from .const import DOMAIN, EVENT_ALARM
from .coordinator import FFAgentCoordinator

CONFIG_SCHEMA = cv.empty_config_schema(DOMAIN)
PLATFORMS = [Platform.BINARY_SENSOR, Platform.SENSOR]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Serve and load one bundled card, shared by all organizations."""
    root = Path(__file__).parent
    await hass.http.async_register_static_paths(
        [
            StaticPathConfig(
                "/ff_agent/ff-agent-card.js",
                str(root / "frontend" / "ff-agent-card.js"),
                True,
            ),
            StaticPathConfig(
                "/ff_agent/icon.png", str(root / "brand" / "icon.png"), True
            ),
        ]
    )
    integration = await async_get_integration(hass, DOMAIN)
    card_path = "/ff_agent/ff-agent-card.js"
    card_url = f"{card_path}?v={integration.version}"
    frontend.add_extra_js_url(hass, card_url)

    # Lovelace also loads resources independently of the initial HTML document.
    # Keep YAML-managed resources untouched; the extra module still loads there.
    resources = hass.data[LOVELACE_DATA].resources
    if isinstance(resources, ResourceStorageCollection):
        await resources.async_get_info()
        existing = next(
            (
                item
                for item in resources.async_items()
                if item["url"].split("?", 1)[0] == card_path
            ),
            None,
        )
        if existing is None:
            await resources.async_create_item({"res_type": "module", "url": card_url})
        elif existing["url"] != card_url or existing["type"] != "module":
            await resources.async_update_item(
                existing["id"], {"res_type": "module", "url": card_url}
            )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Restore organization state, expose entities and register its GET webhook."""
    coordinator = FFAgentCoordinator(hass, entry)
    entry.runtime_data = coordinator
    await coordinator.async_initialize()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    async def handle_alarm(
        hass: HomeAssistant, webhook_id: str, request: web.Request
    ) -> web.Response:
        coordinator.async_alarm()
        hass.bus.async_fire(EVENT_ALARM, {"config_entry_id": entry.entry_id})
        return web.Response(
            text="Alarm signal received by FF Agent.",
            headers={"Cache-Control": "no-store"},
        )

    webhook.async_register(
        hass,
        DOMAIN,
        entry.title,
        entry.data[CONF_WEBHOOK_ID],
        handle_alarm,
        allowed_methods={"GET"},
        local_only=False,
    )
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Disable the webhook when its service is unloaded or removed."""
    if unloaded := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        webhook.async_unregister(hass, entry.data[CONF_WEBHOOK_ID])
    return unloaded


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Remove only the deleted organization's persisted local alarm state."""
    await Store(hass, 1, f"{DOMAIN}.{entry.entry_id}").async_remove()
