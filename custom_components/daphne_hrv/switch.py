"""Switch platform for the 2VV Daphne HRV integration."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.switch import (
    SwitchDeviceClass,
    SwitchEntity,
    SwitchEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import DaphneHRVConfigEntry
from .const import DATA_NIGHT_MODE, DATA_POWER
from .coordinator import DaphneHRVCoordinator
from .entity import DaphneEntity


@dataclass(frozen=True, kw_only=True)
class DaphneSwitchDescription(SwitchEntityDescription):
    """Switch description with read + write callbacks."""

    is_on_fn: Callable[[dict[str, Any]], bool | None]
    set_fn: Callable[[DaphneHRVCoordinator, bool], Awaitable[None]]


SWITCHES: tuple[DaphneSwitchDescription, ...] = (
    DaphneSwitchDescription(
        key="power",
        translation_key="power",
        device_class=SwitchDeviceClass.SWITCH,
        is_on_fn=lambda d: d.get(DATA_POWER),
        set_fn=lambda c, on: c.async_set_power(on),
    ),
    DaphneSwitchDescription(
        key="night_mode",
        translation_key="night_mode",
        is_on_fn=lambda d: d.get(DATA_NIGHT_MODE),
        set_fn=lambda c, on: c.async_set_night_mode(on),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: DaphneHRVConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Daphne HRV switches from a config entry."""
    coordinator = entry.runtime_data
    async_add_entities(DaphneSwitch(coordinator, desc) for desc in SWITCHES)


class DaphneSwitch(DaphneEntity, SwitchEntity):
    """A Daphne on/off switch backed by a holding register."""

    entity_description: DaphneSwitchDescription

    def __init__(
        self,
        coordinator: DaphneHRVCoordinator,
        description: DaphneSwitchDescription,
    ) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def is_on(self) -> bool | None:
        data = self.coordinator.data
        if data is None:
            return None
        return self.entity_description.is_on_fn(data)

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.entity_description.set_fn(self.coordinator, True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.entity_description.set_fn(self.coordinator, False)
