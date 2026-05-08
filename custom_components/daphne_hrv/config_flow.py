"""Config flow for the 2VV Daphne HRV integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT
from pymodbus.client import AsyncModbusTcpClient
from pymodbus.exceptions import ModbusException

from .const import (
    CONF_SLAVE,
    DEFAULT_NAME,
    DEFAULT_PORT,
    DEFAULT_SLAVE,
    DOMAIN,
    INPUT_BLOCK_18K_START,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME, default=DEFAULT_NAME): str,
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=65535)
        ),
        vol.Required(CONF_SLAVE, default=DEFAULT_SLAVE): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=247)
        ),
    }
)


async def _async_test_connection(host: str, port: int, slave: int) -> None:
    """Open a TCP connection and read one register to verify the device responds."""
    client = AsyncModbusTcpClient(host=host, port=port, timeout=5)
    try:
        if not await client.connect():
            raise CannotConnect(f"TCP connect to {host}:{port} failed")
        result = await client.read_input_registers(
            address=INPUT_BLOCK_18K_START, count=1, device_id=slave
        )
        if result.isError():
            raise InvalidDevice(f"Modbus probe returned error: {result}")
    except ModbusException as err:
        raise CannotConnect(str(err)) from err
    finally:
        client.close()


class DaphneHRVConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Daphne HRV."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial UI step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST]
            port = user_input[CONF_PORT]
            slave = user_input[CONF_SLAVE]

            await self.async_set_unique_id(f"{host}:{port}:{slave}")
            self._abort_if_unique_id_configured()

            try:
                await _async_test_connection(host, port, slave)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidDevice:
                errors["base"] = "invalid_device"
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Unexpected error during config flow validation")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=user_input[CONF_NAME], data=user_input
                )

        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(
                STEP_USER_DATA_SCHEMA, user_input
            ),
            errors=errors,
        )


class CannotConnect(Exception):
    """Raised when the Modbus TCP connection cannot be established."""


class InvalidDevice(Exception):
    """Raised when the device responds but with a Modbus exception."""
