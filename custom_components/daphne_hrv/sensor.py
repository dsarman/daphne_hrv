"""Sensor platform for the 2VV Daphne HRV integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal
from typing import cast

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.components.sensor.const import SensorDeviceClass, SensorStateClass
from homeassistant.const import PERCENTAGE, EntityCategory, UnitOfTemperature, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

from . import DaphneHRVConfigEntry
from .const import (
    DATA_BYPASS_POSITION,
    DATA_ERROR_WORD,
    DATA_EXHAUST_TEMP,
    DATA_EXTRACT_TEMP,
    DATA_FILTER_CONDITION,
    DATA_FILTER_HOURS,
    DATA_FILTER_HOURS_LIMIT,
    DATA_FILTER_WEAR,
    DATA_HEATER_OUTPUT,
    DATA_OUTDOOR_TEMP,
    DATA_ROOM_TEMP,
    DATA_SENSOR_STATUS,
    DATA_STATUS_WORD,
    DATA_SUPPLY_TEMP,
    DATA_WATER_RETURN_TEMP,
    DOMAIN,
    MANUFACTURER,
    MODEL,
)
from .coordinator import DaphneHRVCoordinator


@dataclass(frozen=True, kw_only=True)
class DaphneSensorDescription(SensorEntityDescription):
    """Sensor description with a value extractor over coordinator data."""

    value_fn: Callable[[dict[str, object]], StateType | Decimal]


def _native_value(key: str) -> Callable[[dict[str, object]], StateType | Decimal]:
    def _read(data: dict[str, object]) -> StateType | Decimal:
        value = data.get(key)
        if isinstance(value, str | int | float | Decimal):
            return value
        return None

    return _read


SENSORS: tuple[DaphneSensorDescription, ...] = (
    # Temperatures
    DaphneSensorDescription(
        key="outdoor_temp",
        translation_key="outdoor_temp",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        suggested_display_precision=1,
        value_fn=_native_value(DATA_OUTDOOR_TEMP),
    ),
    DaphneSensorDescription(
        key="exhaust_temp",
        translation_key="exhaust_temp",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        suggested_display_precision=1,
        value_fn=_native_value(DATA_EXHAUST_TEMP),
    ),
    DaphneSensorDescription(
        key="supply_temp",
        translation_key="supply_temp",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        suggested_display_precision=1,
        value_fn=_native_value(DATA_SUPPLY_TEMP),
    ),
    DaphneSensorDescription(
        key="extract_temp",
        translation_key="extract_temp",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        suggested_display_precision=1,
        value_fn=_native_value(DATA_EXTRACT_TEMP),
    ),
    DaphneSensorDescription(
        key="water_return_temp",
        translation_key="water_return_temp",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        suggested_display_precision=1,
        entity_registry_enabled_default=False,  # only present with water heater
        value_fn=_native_value(DATA_WATER_RETURN_TEMP),
    ),
    DaphneSensorDescription(
        key="room_temp",
        translation_key="room_temp",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        suggested_display_precision=1,
        entity_registry_enabled_default=False,  # only present with CT-ROOM sensor
        value_fn=_native_value(DATA_ROOM_TEMP),
    ),
    # Outputs
    DaphneSensorDescription(
        key="bypass_position",
        translation_key="bypass_position",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        value_fn=_native_value(DATA_BYPASS_POSITION),
    ),
    DaphneSensorDescription(
        key="heater_output",
        translation_key="heater_output",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        entity_registry_enabled_default=False,  # only meaningful with a heater
        value_fn=_native_value(DATA_HEATER_OUTPUT),
    ),
    # Filter
    DaphneSensorDescription(
        key="filter_condition",
        translation_key="filter_condition",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        value_fn=_native_value(DATA_FILTER_CONDITION),
    ),
    DaphneSensorDescription(
        key="filter_wear",
        translation_key="filter_wear",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        value_fn=_native_value(DATA_FILTER_WEAR),
    ),
    DaphneSensorDescription(
        key="filter_hours",
        translation_key="filter_hours",
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfTime.HOURS,
        device_class=SensorDeviceClass.DURATION,
        value_fn=_native_value(DATA_FILTER_HOURS),
    ),
    DaphneSensorDescription(
        key="filter_hours_limit",
        translation_key="filter_hours_limit",
        native_unit_of_measurement=UnitOfTime.HOURS,
        device_class=SensorDeviceClass.DURATION,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_native_value(DATA_FILTER_HOURS_LIMIT),
    ),
    # Diagnostics — raw register values exposed for users to decode bitmasks.
    DaphneSensorDescription(
        key="status_word",
        translation_key="status_word",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_native_value(DATA_STATUS_WORD),
    ),
    DaphneSensorDescription(
        key="error_word",
        translation_key="error_word",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_native_value(DATA_ERROR_WORD),
    ),
    DaphneSensorDescription(
        key="sensor_status",
        translation_key="sensor_status",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_native_value(DATA_SENSOR_STATUS),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: DaphneHRVConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Daphne HRV sensors from a config entry."""
    _ = hass
    coordinator = entry.runtime_data
    async_add_entities(DaphneSensor(coordinator, desc) for desc in SENSORS)


class DaphneSensor(SensorEntity):
    """A Daphne sensor backed by the bulk-read coordinator."""

    coordinator: DaphneHRVCoordinator
    _description: DaphneSensorDescription

    def __init__(
        self,
        coordinator: DaphneHRVCoordinator,
        description: DaphneSensorDescription,
    ) -> None:
        super().__init__()
        self.coordinator = coordinator
        self.entity_description = cast(SensorEntityDescription, description)
        self._description = description
        self._attr_has_entity_name = True
        self._attr_should_poll = False
        self._attr_available = coordinator.last_update_success
        entry = coordinator.config_entry
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer=MANUFACTURER,
            model=MODEL,
            configuration_url=f"http://{coordinator.host}",
        )
        self._update_native_value()

    def _update_native_value(self) -> None:
        self._attr_native_value = self._description.value_fn(self.coordinator.data or {})

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
        self._update_native_value()
        self.async_write_ha_state()
