"""Binary sensor platform for the 2VV Daphne HRV integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import DaphneHRVConfigEntry
from .const import DATA_ERROR_WORD, DATA_STATUS_WORD, STATUS_BIT_RUNNING
from .entity import DaphneEntity


@dataclass(frozen=True, kw_only=True)
class DaphneBinarySensorDescription(BinarySensorEntityDescription):
    """Binary sensor description with a predicate over coordinator data."""

    is_on_fn: Callable[[dict[str, Any]], bool | None]


BINARY_SENSORS: tuple[DaphneBinarySensorDescription, ...] = (
    DaphneBinarySensorDescription(
        key="running",
        translation_key="running",
        device_class=BinarySensorDeviceClass.RUNNING,
        is_on_fn=lambda d: bool(
            (d.get(DATA_STATUS_WORD) or 0) & STATUS_BIT_RUNNING
        ),
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
    coordinator = entry.runtime_data
    async_add_entities(
        DaphneBinarySensor(coordinator, desc) for desc in BINARY_SENSORS
    )


class DaphneBinarySensor(DaphneEntity, BinarySensorEntity):
    """A Daphne binary sensor backed by the coordinator."""

    entity_description: DaphneBinarySensorDescription

    def __init__(self, coordinator, description: DaphneBinarySensorDescription) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def is_on(self) -> bool | None:
        data = self.coordinator.data
        if data is None:
            return None
        return self.entity_description.is_on_fn(data)
