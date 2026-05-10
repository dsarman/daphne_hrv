"""Number platform for the 2VV Daphne HRV integration."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import override, cast

from homeassistant.components.number import (
    NumberDeviceClass,
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.const import PERCENTAGE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import DaphneHRVConfigEntry
from .const import (
    DATA_FAN_SPEED,
    DATA_TEMP_SETPOINT,
    DOMAIN,
    MAX_FAN_SPEED_PERCENT,
    MANUFACTURER,
    MIN_FAN_SPEED_PERCENT,
    MODEL,
)
from .coordinator import DaphneHRVCoordinator, DaphneHRVData


@dataclass(frozen=True, kw_only=True)
class DaphneNumberDescription(NumberEntityDescription):
    """Number description with read + write callbacks."""

    value_fn: Callable[[DaphneHRVData], float | None]
    set_fn: Callable[[DaphneHRVCoordinator, float], Awaitable[None]]


NUMBERS: tuple[DaphneNumberDescription, ...] = (
    DaphneNumberDescription(
        key="fan_speed",
        translation_key="fan_speed",
        native_unit_of_measurement=PERCENTAGE,
        native_min_value=MIN_FAN_SPEED_PERCENT,
        native_max_value=MAX_FAN_SPEED_PERCENT,
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
    _ = hass
    coordinator = entry.runtime_data
    async_add_entities(DaphneNumber(coordinator, desc) for desc in NUMBERS)


class DaphneNumber(NumberEntity):
    """A Daphne writable number backed by a holding register."""

    coordinator: DaphneHRVCoordinator
    entity_description: NumberEntityDescription
    _description: DaphneNumberDescription

    def __init__(
        self,
        coordinator: DaphneHRVCoordinator,
        description: DaphneNumberDescription,
    ) -> None:
        super().__init__()
        self.coordinator = coordinator
        self.entity_description = cast(NumberEntityDescription, description)
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
        self._update_native_value()

    def _update_native_value(self) -> None:
        self._attr_native_value: float | None = self._description.value_fn(
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
        self._update_native_value()
        self.async_write_ha_state()

    @override
    async def async_set_native_value(self, value: float) -> None:
        await self._description.set_fn(self.coordinator, value)
