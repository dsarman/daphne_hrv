"""Climate platform for the 2VV Daphne HRV integration."""

from __future__ import annotations

from typing import override

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.const import ATTR_TEMPERATURE, PRECISION_WHOLE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import DaphneHRVConfigEntry
from .const import (
    DATA_EXTRACT_TEMP,
    DATA_HEATER_OUTPUT,
    DATA_POWER,
    DATA_ROOM_TEMP,
    DATA_SUPPLY_TEMP,
    DATA_TEMP_SENSOR_SELECTION,
    DATA_TEMP_SETPOINT,
    DOMAIN,
    MANUFACTURER,
    MODEL,
    TEMP_SENSOR_SELECTION_EXTRACT,
    TEMP_SENSOR_SELECTION_ROOM,
    TEMP_SENSOR_SELECTION_SUPPLY,
)
from .coordinator import DaphneHRVCoordinator, DaphneHRVData

CURRENT_TEMP_KEY_BY_SOURCE: dict[int, str] = {
    TEMP_SENSOR_SELECTION_SUPPLY: DATA_SUPPLY_TEMP,
    TEMP_SENSOR_SELECTION_EXTRACT: DATA_EXTRACT_TEMP,
    TEMP_SENSOR_SELECTION_ROOM: DATA_ROOM_TEMP,
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: DaphneHRVConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Daphne HRV climate entity from a config entry."""
    _ = hass
    async_add_entities([DaphneClimate(entry.runtime_data)])


def _float_value(data: DaphneHRVData, key: str) -> float | None:
    value = data.get(key)
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return float(value)
    return None


class DaphneClimate(ClimateEntity):
    """Main temperature-control entity for a Daphne HRV unit."""

    _attr_has_entity_name: bool = True
    _attr_name: str | None = None
    _attr_translation_key: str | None = "temperature_control"
    _attr_temperature_unit: str = UnitOfTemperature.CELSIUS
    _attr_precision: float = PRECISION_WHOLE
    _attr_target_temperature_step: float | None = 1.0
    _attr_min_temp: float = 10.0
    _attr_max_temp: float = 30.0
    _attr_hvac_modes: list[HVACMode] = [HVACMode.OFF, HVACMode.AUTO]
    _attr_supported_features: ClimateEntityFeature = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.TURN_OFF
        | ClimateEntityFeature.TURN_ON
    )

    coordinator: DaphneHRVCoordinator

    def __init__(self, coordinator: DaphneHRVCoordinator) -> None:
        super().__init__()
        self.coordinator = coordinator
        self._attr_should_poll: bool = False
        self._attr_available: bool = coordinator.last_update_success
        entry = coordinator.config_entry
        self._attr_unique_id: str | None = f"{entry.entry_id}_climate"
        self._attr_device_info: DeviceInfo | None = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer=MANUFACTURER,
            model=MODEL,
            configuration_url=f"http://{coordinator.host}",
        )
        self._update_attrs()

    def _update_attrs(self) -> None:
        data = self.coordinator.data or {}
        is_powered = data.get(DATA_POWER) is True
        self._attr_hvac_mode: HVACMode | None = (
            HVACMode.AUTO if is_powered else HVACMode.OFF
        )
        self._attr_target_temperature: float | None = _float_value(
            data, DATA_TEMP_SETPOINT
        )
        self._attr_current_temperature: float | None = self._current_temperature(data)
        self._attr_hvac_action: HVACAction | None = self._hvac_action(data, is_powered)

    @staticmethod
    def _current_temperature(data: DaphneHRVData) -> float | None:
        selected_source = data.get(DATA_TEMP_SENSOR_SELECTION)
        if not isinstance(selected_source, int) or isinstance(selected_source, bool):
            return None
        temp_key = CURRENT_TEMP_KEY_BY_SOURCE.get(selected_source)
        return _float_value(data, temp_key) if temp_key is not None else None

    @staticmethod
    def _hvac_action(data: DaphneHRVData, is_powered: bool) -> HVACAction:
        if not is_powered:
            return HVACAction.OFF
        heater_output = _float_value(data, DATA_HEATER_OUTPUT)
        return HVACAction.HEATING if heater_output is not None and heater_output > 0 else HVACAction.IDLE

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
        self._update_attrs()
        self.async_write_ha_state()

    @override
    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Turn the unit on or off from the climate entity."""
        if hvac_mode == HVACMode.OFF:
            await self.coordinator.async_set_power(False)
            return
        if hvac_mode == HVACMode.AUTO:
            await self.coordinator.async_set_power(True)
            return
        raise ValueError(f"Unsupported HVAC mode: {hvac_mode}")

    @override
    async def async_set_temperature(self, **kwargs: object) -> None:
        """Set the AirGENIO target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if not isinstance(temperature, int | float) or isinstance(temperature, bool):
            raise ValueError("Temperature is required")
        await self.coordinator.async_set_temp_setpoint(float(temperature))

    @override
    async def async_turn_on(self) -> None:
        """Turn the unit on."""
        await self.coordinator.async_set_power(True)

    @override
    async def async_turn_off(self) -> None:
        """Turn the unit off."""
        await self.coordinator.async_set_power(False)
