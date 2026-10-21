"""Smoke test the scaffold with the same Home Assistant as the dev instance."""

import tempfile
import unittest
from pathlib import Path

from homeassistant import loader
from homeassistant.config_entries import ConfigEntries
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component


class SetupTest(unittest.IsolatedAsyncioTestCase):
    """Exercise Home Assistant's public integration setup boundary."""

    async def test_scaffold_loads_without_entities_or_actions(self) -> None:
        """The scaffold loads from the mount but adds no FF-Agent behavior."""
        with tempfile.TemporaryDirectory() as config_dir:
            # Use the mounted integration with isolated, disposable HA state.
            Path(config_dir, "custom_components").symlink_to(
                "/config/custom_components", target_is_directory=True
            )
            hass = HomeAssistant(config_dir)
            hass.config_entries = ConfigEntries(hass, {})
            loader.async_setup(hass)
            try:
                self.assertTrue(await async_setup_component(hass, "ff_agent", {}))
                self.assertIn("ff_agent", hass.config.components)
                self.assertEqual(hass.states.async_entity_ids("ff_agent"), [])
                self.assertNotIn("ff_agent", hass.services.async_services())
            finally:
                await hass.async_stop()
