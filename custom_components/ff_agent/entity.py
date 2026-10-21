"""Shared organization identity for FF Agent entities."""

from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import FFAgentCoordinator


class FFAgentEntity(CoordinatorEntity[FFAgentCoordinator]):
    """Group both states under their own organization, not the HA instance."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: FFAgentCoordinator) -> None:
        """Use stable identity independent of organization name or reply UUID."""
        super().__init__(coordinator)
        entry = coordinator.entry
        self._attr_unique_id = f"{entry.entry_id}_{self._attr_translation_key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="FF-Agent",
            entry_type=DeviceEntryType.SERVICE,
        )
