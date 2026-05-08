"""Number platform for the 2VV Daphne HRV integration."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.number import (
    NumberDeviceClass,
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.const import PERCENTAGE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import DaphneHRVConfigEntry
from .const import DATA_FAN_SPEED, DATA_TEMP_SETPOINT
from .coordinator import DaphneHRVCoordinator
from .entity import DaphneEntity


@dataclass(frozen=True, kw_only=True)
class DaphneNumberDescription(NumberEntityDescription):
    """Number description with read + write callbacks."""

    value_fn: Callable[[dict[str, Any]], float | None]
    set_fn: Callable[[DaphneHRVCoordinator, float], Awaitable[None]]


NUMBERS: tuple[DaphneNumberDescription, ...] = (
    DaphneNumberDescription(
        key="fan_speed",
        translation_key="fan_speed",
        native_unit_of_measurement=PERCENTAGE,
        native_min_value=0,
        native_max_value=100,
        native_step=5,
        mode=NumberMode.SLIDER,
        value_fn=lambda d: d.get(DATA_FAN_SPEED),
        set_fn=lambda c, v: c.async_set_fan_speed_percent(v),
    ),
    DaphneNumberDescription(
        key="temp_setpoint",
        translation_key="temp_setpoint",
        device_class=NumberDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        native_min_value=10,
        native_max_value=30,
        native_step=1,
        mode=NumberMode.BOX,
        value_fn=lambda d: d.get(DATA_TEMP_SETPOINT),
        set_fn=lambda c, v: c.async_set_temp_setpoint(v),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: DaphneHRVConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Daphne HRV number entities from a config entry."""
    coordinator = entry.runtime_data
    async_add_entities(DaphneNumber(coordinator, desc) for desc in NUMBERS)


class DaphneNumber(DaphneEntity, NumberEntity):
    """A Daphne writable number backed by a holding register."""

    entity_description: DaphneNumberDescription

    def __init__(
        self,
        coordinator: DaphneHRVCoordinator,
        description: DaphneNumberDescription,
    ) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> float | None:
        data = self.coordinator.data
        if data is None:
            return None
        return self.entity_description.value_fn(data)

    async def async_set_native_value(self, value: float) -> None:
        await self.entity_description.set_fn(self.coordinator, value)
