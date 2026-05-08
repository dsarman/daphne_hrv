"""DataUpdateCoordinator for the 2VV Daphne HRV.

Performs three bulk Modbus reads per polling cycle (input registers and two
disjoint holding-register blocks) and exposes the parsed values as a
dictionary keyed by ``DATA_*`` constants from :mod:`.const`.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady, HomeAssistantError
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
from pymodbus.client import AsyncModbusTcpClient
from pymodbus.exceptions import ModbusException

from .const import (
    CONF_SLAVE,
    DATA_BYPASS_POSITION,
    DATA_ERROR_WORD,
    DATA_EXHAUST_TEMP,
    DATA_EXTRACT_TEMP,
    DATA_FAN_SPEED,
    DATA_FILTER_CONDITION,
    DATA_FILTER_HOURS,
    DATA_FILTER_HOURS_LIMIT,
    DATA_FILTER_WEAR,
    DATA_HEATER_OUTPUT,
    DATA_NIGHT_MODE,
    DATA_OUTDOOR_TEMP,
    DATA_POWER,
    DATA_ROOM_TEMP,
    DATA_SENSOR_STATUS,
    DATA_STATUS_WORD,
    DATA_SUPPLY_TEMP,
    DATA_TEMP_SETPOINT,
    DATA_WATER_RETURN_TEMP,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SLAVE,
    DOMAIN,
    HOLDING_BLOCK_21K_COUNT,
    HOLDING_BLOCK_21K_START,
    HOLDING_BLOCK_25K_COUNT,
    HOLDING_BLOCK_25K_START,
    INPUT_BLOCK_15K_COUNT,
    INPUT_BLOCK_15K_START,
    INPUT_BLOCK_18K_COUNT,
    INPUT_BLOCK_18K_START,
    REG_BYPASS_POSITION,
    REG_ERROR_WORD,
    REG_EXHAUST_TEMP,
    REG_EXTRACT_TEMP,
    REG_FAN_SPEED,
    REG_FILTER_CONDITION,
    REG_FILTER_HOURS,
    REG_FILTER_HOURS_LIMIT,
    REG_FILTER_WEAR,
    REG_HEATER_OUTPUT,
    REG_NIGHT_MODE,
    REG_OUTDOOR_TEMP,
    REG_POWER,
    REG_ROOM_TEMP,
    REG_SENSOR_STATUS,
    REG_STATUS_WORD,
    REG_SUPPLY_TEMP,
    REG_TEMP_SETPOINT,
    REG_WATER_RETURN_TEMP,
)

_LOGGER = logging.getLogger(__name__)


def _to_int16(value: int) -> int:
    """Convert an unsigned 16-bit Modbus register value to signed int16."""
    return value - 0x10000 if value >= 0x8000 else value


class DaphneHRVCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator that bulk-reads all known Daphne registers per poll."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialise the coordinator and underlying Modbus client."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            config_entry=entry,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self._host: str = entry.data[CONF_HOST]
        self._port: int = entry.data[CONF_PORT]
        self._slave: int = entry.data.get(CONF_SLAVE, DEFAULT_SLAVE)
        self._client = AsyncModbusTcpClient(host=self._host, port=self._port)
        # Serialise all Modbus operations - pymodbus 3.x clients are not
        # safe for concurrent calls on the same TCP socket.
        self._lock = asyncio.Lock()

    @property
    def host(self) -> str:
        """Return the configured Modbus host (used for unique IDs)."""
        return self._host

    @property
    def slave(self) -> int:
        """Return the configured Modbus slave/unit ID."""
        return self._slave

    async def _async_setup(self) -> None:
        """Open the TCP connection on first refresh.

        Called automatically by ``async_config_entry_first_refresh``. Raising
        :class:`ConfigEntryNotReady` here makes HA retry setup later.
        """
        if not await self._client.connect():
            raise ConfigEntryNotReady(
                f"Cannot connect to Daphne at {self._host}:{self._port}"
            )

    async def async_shutdown(self) -> None:
        """Close the Modbus connection on entry unload."""
        await super().async_shutdown()
        self._client.close()

    async def _async_update_data(self) -> dict[str, Any]:
        """Bulk-read all configured registers and return a parsed dict."""
        async with self._lock:
            try:
                if not self._client.connected:
                    await self._client.connect()

                inputs_15k = await self._read_input_registers(
                    INPUT_BLOCK_15K_START, INPUT_BLOCK_15K_COUNT
                )
                inputs_18k = await self._read_input_registers(
                    INPUT_BLOCK_18K_START, INPUT_BLOCK_18K_COUNT
                )
                holdings_21k = await self._read_holding_registers(
                    HOLDING_BLOCK_21K_START, HOLDING_BLOCK_21K_COUNT
                )
                holdings_25k = await self._read_holding_registers(
                    HOLDING_BLOCK_25K_START, HOLDING_BLOCK_25K_COUNT
                )
            except ModbusException as err:
                raise UpdateFailed(f"Modbus error: {err}") from err

        return self._parse(inputs_15k, inputs_18k, holdings_21k, holdings_25k)

    async def _read_input_registers(self, address: int, count: int) -> list[int]:
        result = await self._client.read_input_registers(
            address=address, count=count, device_id=self._slave
        )
        if result.isError():
            raise UpdateFailed(f"read_input_registers({address}) failed: {result}")
        return list(result.registers)

    async def _read_holding_registers(self, address: int, count: int) -> list[int]:
        result = await self._client.read_holding_registers(
            address=address, count=count, device_id=self._slave
        )
        if result.isError():
            raise UpdateFailed(f"read_holding_registers({address}) failed: {result}")
        return list(result.registers)

    def _parse(
        self,
        inputs_15k: list[int],
        inputs_18k: list[int],
        h21k: list[int],
        h25k: list[int],
    ) -> dict[str, Any]:
        """Map the three raw register blocks into the coordinator data dict."""

        def i15(reg: int) -> int:
            return inputs_15k[reg - INPUT_BLOCK_15K_START]

        def i18(reg: int) -> int:
            return inputs_18k[reg - INPUT_BLOCK_18K_START]

        def h21(reg: int) -> int:
            return h21k[reg - HOLDING_BLOCK_21K_START]

        def h25(reg: int) -> int:
            return h25k[reg - HOLDING_BLOCK_25K_START]

        return {
            # Status / diagnostics
            DATA_STATUS_WORD: i15(REG_STATUS_WORD),
            DATA_ERROR_WORD: i18(REG_ERROR_WORD),
            DATA_SENSOR_STATUS: i18(REG_SENSOR_STATUS),
            DATA_BYPASS_POSITION: i15(REG_BYPASS_POSITION),
            # Temperatures (signed, ÷10 → °C)
            DATA_OUTDOOR_TEMP: _to_int16(i18(REG_OUTDOOR_TEMP)) / 10.0,
            DATA_EXHAUST_TEMP: _to_int16(i18(REG_EXHAUST_TEMP)) / 10.0,
            DATA_SUPPLY_TEMP: _to_int16(i18(REG_SUPPLY_TEMP)) / 10.0,
            DATA_EXTRACT_TEMP: _to_int16(i18(REG_EXTRACT_TEMP)) / 10.0,
            DATA_WATER_RETURN_TEMP: _to_int16(i18(REG_WATER_RETURN_TEMP)) / 10.0,
            DATA_ROOM_TEMP: _to_int16(i18(REG_ROOM_TEMP)) / 10.0,
            # Outputs / wear
            DATA_HEATER_OUTPUT: i18(REG_HEATER_OUTPUT),
            DATA_FILTER_CONDITION: i18(REG_FILTER_CONDITION),
            DATA_FILTER_WEAR: i18(REG_FILTER_WEAR),
            # Setpoints / mode
            DATA_POWER: bool(h21(REG_POWER)),
            DATA_FAN_SPEED: h21(REG_FAN_SPEED) / 10.0,  # ‰ → %
            DATA_TEMP_SETPOINT: _to_int16(h21(REG_TEMP_SETPOINT)),
            DATA_NIGHT_MODE: bool(h21(REG_NIGHT_MODE)),
            # Filter counters
            DATA_FILTER_HOURS: h25(REG_FILTER_HOURS),
            DATA_FILTER_HOURS_LIMIT: h25(REG_FILTER_HOURS_LIMIT),
        }

    # ─── Write helpers, called by switch / number platforms ──────────────────

    async def async_write_register(self, address: int, value: int) -> None:
        """Write a single holding register and refresh the coordinator data."""
        async with self._lock:
            try:
                if not self._client.connected:
                    await self._client.connect()
                result = await self._client.write_register(
                    address=address, value=value, device_id=self._slave
                )
            except ModbusException as err:
                raise HomeAssistantError(
                    f"Modbus write to {address} failed: {err}"
                ) from err
        if result.isError():
            raise HomeAssistantError(
                f"Modbus write to {address} returned error: {result}"
            )
        await self.async_request_refresh()

    async def async_set_power(self, on: bool) -> None:
        await self.async_write_register(REG_POWER, 1 if on else 0)

    async def async_set_night_mode(self, on: bool) -> None:
        await self.async_write_register(REG_NIGHT_MODE, 1 if on else 0)

    async def async_set_fan_speed_percent(self, percent: float) -> None:
        """Write fan speed as 0-100 %, scaling to the unit's 0-1000 ‰ range."""
        clamped = max(0.0, min(100.0, float(percent)))
        await self.async_write_register(REG_FAN_SPEED, int(round(clamped * 10)))

    async def async_set_temp_setpoint(self, value: float) -> None:
        """Write the temperature setpoint in whole degrees Celsius."""
        await self.async_write_register(REG_TEMP_SETPOINT, int(round(value)))
