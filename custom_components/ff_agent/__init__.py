"""FF Agent integration scaffold; no provider functionality yet."""

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Load the development scaffold without registering any functionality."""
    return True
