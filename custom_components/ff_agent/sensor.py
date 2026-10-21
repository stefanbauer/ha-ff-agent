"""Last locally sent personal reply for an FF Agent alarm."""

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity

from .entity import FFAgentEntity


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    """Expose one reply status for each organization."""
    async_add_entities([FFAgentReply(entry.runtime_data)])


class FFAgentReply(FFAgentEntity, SensorEntity):
    """Track HTTP-delivered decisions, not a polled provider status."""

    _attr_translation_key = "reply_status"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = ["pending", "accepted", "rejected"]
    _attr_icon = "mdi:account-check"

    @property
    def native_value(self) -> str:
        """Return the local reply state; failures never manufacture success."""
        return self.coordinator.reply_status
