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
    DATA_SENSOR_STATUS,
    DATA_STATUS_WORD,
    DOMAIN,
    MANUFACTURER,
    MODEL,
    SENSOR_STATUS_BIT_BMS,
    SENSOR_STATUS_BIT_EXHAUST,
    SENSOR_STATUS_BIT_OUTDOOR,
    SENSOR_STATUS_BIT_ROOM,
    SENSOR_STATUS_BIT_SUPPLY,
    SENSOR_STATUS_BIT_WATER_RETURN,
    STATUS_BIT_ERROR_INDICATION,
    STATUS_BIT_EXCHANGER_HEATING,
    STATUS_BIT_RUNNING,
    STATUS_BIT_WATER_PUMP,
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


def _status_bit_problem(key: str, bit: int) -> Callable[[DaphneHRVData], bool]:
    """Return a predicate that treats a set bit as a diagnostic problem."""

    return _status_bit_is_set(key, bit)


def _nonzero_value(key: str) -> Callable[[DaphneHRVData], bool]:
    """Return a predicate that is true when an integer value is non-zero."""

    def _read(data: DaphneHRVData) -> bool:
        value = data.get(key)
        return isinstance(value, int) and value != 0

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
        is_on_fn=_nonzero_value(DATA_ERROR_WORD),
    ),
    DaphneBinarySensorDescription(
        key="error_indication",
        translation_key="error_indication",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
        is_on_fn=_status_bit_is_set(DATA_STATUS_WORD, STATUS_BIT_ERROR_INDICATION),
    ),
    DaphneBinarySensorDescription(
        key="exchanger_heating",
        translation_key="exchanger_heating",
        entity_category=EntityCategory.DIAGNOSTIC,
        is_on_fn=_status_bit_is_set(DATA_STATUS_WORD, STATUS_BIT_EXCHANGER_HEATING),
    ),
    DaphneBinarySensorDescription(
        key="water_pump",
        translation_key="water_pump",
        entity_category=EntityCategory.DIAGNOSTIC,
        is_on_fn=_status_bit_is_set(DATA_STATUS_WORD, STATUS_BIT_WATER_PUMP),
    ),
    DaphneBinarySensorDescription(
        key="outdoor_sensor_problem",
        translation_key="outdoor_sensor_problem",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
        is_on_fn=_status_bit_problem(DATA_SENSOR_STATUS, SENSOR_STATUS_BIT_OUTDOOR),
    ),
    DaphneBinarySensorDescription(
        key="exhaust_sensor_problem",
        translation_key="exhaust_sensor_problem",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
        is_on_fn=_status_bit_problem(DATA_SENSOR_STATUS, SENSOR_STATUS_BIT_EXHAUST),
    ),
    DaphneBinarySensorDescription(
        key="supply_sensor_problem",
        translation_key="supply_sensor_problem",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
        is_on_fn=_status_bit_problem(DATA_SENSOR_STATUS, SENSOR_STATUS_BIT_SUPPLY),
    ),
    DaphneBinarySensorDescription(
        key="water_return_sensor_problem",
        translation_key="water_return_sensor_problem",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
        is_on_fn=_status_bit_problem(
            DATA_SENSOR_STATUS, SENSOR_STATUS_BIT_WATER_RETURN
        ),
    ),
    DaphneBinarySensorDescription(
        key="room_sensor_problem",
        translation_key="room_sensor_problem",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
        is_on_fn=_status_bit_problem(DATA_SENSOR_STATUS, SENSOR_STATUS_BIT_ROOM),
    ),
    DaphneBinarySensorDescription(
        key="bms_sensor_problem",
        translation_key="bms_sensor_problem",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
        is_on_fn=_status_bit_problem(DATA_SENSOR_STATUS, SENSOR_STATUS_BIT_BMS),
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
