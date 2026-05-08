"""Sensor platform for the 2VV Daphne HRV integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, EntityCategory, UnitOfTemperature, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import DaphneHRVConfigEntry
from .const import (
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
    DATA_SUB_STATUS,
    DATA_SUPPLY_TEMP,
    DATA_WATER_RETURN_TEMP,
)
from .entity import DaphneEntity


@dataclass(frozen=True, kw_only=True)
class DaphneSensorDescription(SensorEntityDescription):
    """Sensor description with a value extractor over coordinator data."""

    value_fn: Callable[[dict[str, Any]], Any]


def _temp(key: str) -> Callable[[dict[str, Any]], float | None]:
    def _read(data: dict[str, Any]) -> float | None:
        return data.get(key)

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
        value_fn=_temp(DATA_OUTDOOR_TEMP),
    ),
    DaphneSensorDescription(
        key="exhaust_temp",
        translation_key="exhaust_temp",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        suggested_display_precision=1,
        value_fn=_temp(DATA_EXHAUST_TEMP),
    ),
    DaphneSensorDescription(
        key="supply_temp",
        translation_key="supply_temp",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        suggested_display_precision=1,
        value_fn=_temp(DATA_SUPPLY_TEMP),
    ),
    DaphneSensorDescription(
        key="extract_temp",
        translation_key="extract_temp",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        suggested_display_precision=1,
        value_fn=_temp(DATA_EXTRACT_TEMP),
    ),
    DaphneSensorDescription(
        key="water_return_temp",
        translation_key="water_return_temp",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        suggested_display_precision=1,
        entity_registry_enabled_default=False,  # only present with water heater
        value_fn=_temp(DATA_WATER_RETURN_TEMP),
    ),
    DaphneSensorDescription(
        key="room_temp",
        translation_key="room_temp",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        suggested_display_precision=1,
        entity_registry_enabled_default=False,  # only present with CT-ROOM sensor
        value_fn=_temp(DATA_ROOM_TEMP),
    ),
    # Outputs
    DaphneSensorDescription(
        key="heater_output",
        translation_key="heater_output",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        entity_registry_enabled_default=False,  # only meaningful with a heater
        value_fn=lambda d: d.get(DATA_HEATER_OUTPUT),
    ),
    # Filter
    DaphneSensorDescription(
        key="filter_condition",
        translation_key="filter_condition",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        value_fn=lambda d: d.get(DATA_FILTER_CONDITION),
    ),
    DaphneSensorDescription(
        key="filter_wear",
        translation_key="filter_wear",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        value_fn=lambda d: d.get(DATA_FILTER_WEAR),
    ),
    DaphneSensorDescription(
        key="filter_hours",
        translation_key="filter_hours",
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfTime.HOURS,
        device_class=SensorDeviceClass.DURATION,
        value_fn=lambda d: d.get(DATA_FILTER_HOURS),
    ),
    DaphneSensorDescription(
        key="filter_hours_limit",
        translation_key="filter_hours_limit",
        native_unit_of_measurement=UnitOfTime.HOURS,
        device_class=SensorDeviceClass.DURATION,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.get(DATA_FILTER_HOURS_LIMIT),
    ),
    # Diagnostics — raw register values exposed for users to decode bitmasks.
    DaphneSensorDescription(
        key="status_word",
        translation_key="status_word",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.get(DATA_STATUS_WORD),
    ),
    DaphneSensorDescription(
        key="error_word",
        translation_key="error_word",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.get(DATA_ERROR_WORD),
    ),
    DaphneSensorDescription(
        key="sensor_status",
        translation_key="sensor_status",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.get(DATA_SENSOR_STATUS),
    ),
    DaphneSensorDescription(
        key="sub_status",
        translation_key="sub_status",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.get(DATA_SUB_STATUS),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: DaphneHRVConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Daphne HRV sensors from a config entry."""
    coordinator = entry.runtime_data
    async_add_entities(DaphneSensor(coordinator, desc) for desc in SENSORS)


class DaphneSensor(DaphneEntity, SensorEntity):
    """A Daphne sensor backed by the bulk-read coordinator."""

    entity_description: DaphneSensorDescription

    def __init__(
        self,
        coordinator,
        description: DaphneSensorDescription,
    ) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> Any:
        return self.entity_description.value_fn(self.coordinator.data or {})
