"""Base entity for the 2VV Daphne HRV integration."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER, MODEL
from .coordinator import DaphneHRVCoordinator


class DaphneEntity(CoordinatorEntity[DaphneHRVCoordinator]):
    """Common base: shared device_info, unique_id scheme and availability."""

    _attr_has_entity_name: bool = True

    def __init__(self, coordinator: DaphneHRVCoordinator, key: str) -> None:
        """Bind the entity to the coordinator and a stable key."""
        super().__init__(coordinator)
        self._key: str = key
        entry = coordinator.config_entry
        self._attr_unique_id: str | None = f"{entry.entry_id}_{key}"
        self._attr_device_info: DeviceInfo | None = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer=MANUFACTURER,
            model=MODEL,
            configuration_url=f"http://{coordinator.host}",
        )
