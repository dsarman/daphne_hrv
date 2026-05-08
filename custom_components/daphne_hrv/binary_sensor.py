"""Binary sensor platform for the 2VV Daphne HRV integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import override, cast

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import DaphneHRVConfigEntry
from .const import (
    DATA_ERROR_WORD,
    DATA_STATUS_WORD,
    DOMAIN,
    MANUFACTURER,
    MODEL,
    STATUS_BIT_RUNNING,
)
from .coordinator import DaphneHRVCoordinator, DaphneHRVData


@dataclass(frozen=True, kw_only=True)
class DaphneBinarySensorDescription(BinarySensorEntityDescription):
    """Binary sensor description with a predicate over coordinator data."""

    is_on_fn: Callable[[DaphneHRVData], bool | None]


def _status_bit_is_set(key: str, bit: int) -> Callable[[DaphneHRVData], bool]:
    """Return a predicate that checks a bit in an integer coordinator value."""

    def _read(data: DaphneHRVData) -> bool:
        value = data.get(key)
        return isinstance(value, int) and bool(value & bit)

    return _read


BINARY_SENSORS: tuple[DaphneBinarySensorDescription, ...] = (
    DaphneBinarySensorDescription(
        key="running",
        translation_key="running",
        device_class=BinarySensorDeviceClass.RUNNING,
        is_on_fn=_status_bit_is_set(DATA_STATUS_WORD, STATUS_BIT_RUNNING),
    ),
    DaphneBinarySensorDescription(
        key="error",
        translation_key="error",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
        is_on_fn=lambda d: (d.get(DATA_ERROR_WORD) or 0) != 0,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: DaphneHRVConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Daphne HRV binary sensors from a config entry."""
    _ = hass
    coordinator = entry.runtime_data
    async_add_entities(
        DaphneBinarySensor(coordinator, desc) for desc in BINARY_SENSORS
    )


class DaphneBinarySensor(BinarySensorEntity):
    """A Daphne binary sensor backed by the coordinator."""

    coordinator: DaphneHRVCoordinator
    entity_description: BinarySensorEntityDescription
    _description: DaphneBinarySensorDescription

    def __init__(
        self,
        coordinator: DaphneHRVCoordinator,
        description: DaphneBinarySensorDescription,
    ) -> None:
        super().__init__()
        self.coordinator = coordinator
        self.entity_description = cast(BinarySensorEntityDescription, description)
        self._description = description
        self._attr_has_entity_name: bool = True
        self._attr_should_poll: bool = False
        self._attr_available: bool = coordinator.last_update_success
        entry = coordinator.config_entry
        self._attr_unique_id: str | None = f"{entry.entry_id}_{description.key}"
        self._attr_device_info: DeviceInfo | None = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer=MANUFACTURER,
            model=MODEL,
            configuration_url=f"http://{coordinator.host}",
        )
        self._update_is_on()

    def _update_is_on(self) -> None:
        self._attr_is_on: bool | None = self._description.is_on_fn(
            self.coordinator.data or {}
        )

    @override
    async def async_added_to_hass(self) -> None:
        """Subscribe to coordinator updates when Home Assistant adds the entity."""
        await super().async_added_to_hass()
        self.async_on_remove(self.coordinator.async_add_listener(self._handle_update))

    async def async_update(self) -> None:
        """Refresh coordinator data when Home Assistant requests an entity update."""
        await self.coordinator.async_request_refresh()

    def _handle_update(self) -> None:
        """Handle a coordinator update callback."""
        self._attr_available = self.coordinator.last_update_success
        self._update_is_on()
        self.async_write_ha_state()
