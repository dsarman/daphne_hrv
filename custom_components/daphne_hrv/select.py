"""Select platform for the 2VV Daphne HRV integration."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import override, cast

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import DaphneHRVConfigEntry
from .const import (
    DATA_TEMP_SENSOR_SELECTION,
    DOMAIN,
    MANUFACTURER,
    MODEL,
    TEMP_SENSOR_SELECTION_OPTIONS,
)
from .coordinator import DaphneHRVCoordinator, DaphneHRVData


@dataclass(frozen=True, kw_only=True)
class DaphneSelectDescription(SelectEntityDescription):
    """Select description with read + write callbacks."""

    option_by_value: dict[int, str]
    value_fn: Callable[[DaphneHRVData], int | None]
    set_fn: Callable[[DaphneHRVCoordinator, int], Awaitable[None]]


def _int_value(key: str) -> Callable[[DaphneHRVData], int | None]:
    """Return a reader for an integer coordinator value."""

    def _read(data: DaphneHRVData) -> int | None:
        value = data.get(key)
        return value if isinstance(value, int) and not isinstance(value, bool) else None

    return _read


SELECTS: tuple[DaphneSelectDescription, ...] = (
    DaphneSelectDescription(
        key="temp_sensor_selection",
        translation_key="temp_sensor_selection",
        options=list(TEMP_SENSOR_SELECTION_OPTIONS.values()),
        option_by_value=TEMP_SENSOR_SELECTION_OPTIONS,
        value_fn=_int_value(DATA_TEMP_SENSOR_SELECTION),
        set_fn=lambda c, value: c.async_set_temp_sensor_selection(value),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: DaphneHRVConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Daphne HRV select entities from a config entry."""
    _ = hass
    coordinator = entry.runtime_data
    async_add_entities(DaphneSelect(coordinator, desc) for desc in SELECTS)


class DaphneSelect(SelectEntity):
    """A Daphne select backed by a holding register."""

    coordinator: DaphneHRVCoordinator
    entity_description: SelectEntityDescription
    _description: DaphneSelectDescription

    def __init__(
        self,
        coordinator: DaphneHRVCoordinator,
        description: DaphneSelectDescription,
    ) -> None:
        super().__init__()
        self.coordinator = coordinator
        self.entity_description = cast(SelectEntityDescription, description)
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
        self._update_current_option()

    def _update_current_option(self) -> None:
        value = self._description.value_fn(self.coordinator.data or {})
        self._attr_current_option: str | None = (
            self._description.option_by_value.get(value) if value is not None else None
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
        self._update_current_option()
        self.async_write_ha_state()

    @override
    async def async_select_option(self, option: str) -> None:
        """Write the selected temperature regulation sensor."""
        value_by_option = {v: k for k, v in self._description.option_by_value.items()}
        value = value_by_option.get(option)
        if value is None:
            raise ValueError(f"Unknown temperature control source option: {option}")
        await self._description.set_fn(self.coordinator, value)
