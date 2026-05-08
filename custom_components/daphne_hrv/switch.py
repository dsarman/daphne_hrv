"""Switch platform for the 2VV Daphne HRV integration."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import override, cast

from homeassistant.components.switch import (
    SwitchDeviceClass,
    SwitchEntity,
    SwitchEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import DaphneHRVConfigEntry
from .const import DATA_NIGHT_MODE, DATA_POWER, DOMAIN, MANUFACTURER, MODEL
from .coordinator import DaphneHRVCoordinator, DaphneHRVData


@dataclass(frozen=True, kw_only=True)
class DaphneSwitchDescription(SwitchEntityDescription):
    """Switch description with read + write callbacks."""

    is_on_fn: Callable[[DaphneHRVData], bool | None]
    set_fn: Callable[[DaphneHRVCoordinator, bool], Awaitable[None]]


def _bool_value(key: str) -> Callable[[DaphneHRVData], bool | None]:
    """Return a predicate for a boolean coordinator value."""

    def _read(data: DaphneHRVData) -> bool | None:
        value = data.get(key)
        return value if isinstance(value, bool) else None

    return _read


SWITCHES: tuple[DaphneSwitchDescription, ...] = (
    DaphneSwitchDescription(
        key="power",
        translation_key="power",
        device_class=SwitchDeviceClass.SWITCH,
        is_on_fn=_bool_value(DATA_POWER),
        set_fn=lambda c, on: c.async_set_power(on),
    ),
    DaphneSwitchDescription(
        key="night_mode",
        translation_key="night_mode",
        is_on_fn=_bool_value(DATA_NIGHT_MODE),
        set_fn=lambda c, on: c.async_set_night_mode(on),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: DaphneHRVConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Daphne HRV switches from a config entry."""
    _ = hass
    coordinator = entry.runtime_data
    async_add_entities(DaphneSwitch(coordinator, desc) for desc in SWITCHES)


class DaphneSwitch(SwitchEntity):
    """A Daphne on/off switch backed by a holding register."""

    coordinator: DaphneHRVCoordinator
    entity_description: SwitchEntityDescription
    _description: DaphneSwitchDescription

    def __init__(
        self,
        coordinator: DaphneHRVCoordinator,
        description: DaphneSwitchDescription,
    ) -> None:
        super().__init__()
        self.coordinator = coordinator
        self.entity_description = cast(SwitchEntityDescription, description)
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

    @override
    async def async_turn_on(self, **kwargs: object) -> None:
        await self._description.set_fn(self.coordinator, True)

    @override
    async def async_turn_off(self, **kwargs: object) -> None:
        await self._description.set_fn(self.coordinator, False)
