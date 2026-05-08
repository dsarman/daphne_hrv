"""Constants for the 2VV Daphne HRV integration."""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "daphne_hrv"
MANUFACTURER: Final = "2VV"
MODEL: Final = "Daphne (AirGENIO)"

DEFAULT_NAME: Final = "Daphne HRV"
DEFAULT_PORT: Final = 502
DEFAULT_SLAVE: Final = 1
DEFAULT_SCAN_INTERVAL: Final = 30  # seconds

CONF_SLAVE: Final = "slave"

# ─────────────────────────────────────────────────────────────────────────────
# Modbus register map (raw 0-based addresses, as used by HA's modbus integration
# and pymodbus). PDF/manual addresses are 1-based PLC addresses; we use the
# raw form documented by the TapHome integration template, which has been
# empirically validated against a real Daphne unit.
# ─────────────────────────────────────────────────────────────────────────────

# Input registers (function code 0x04, read-only)
REG_BYPASS_POSITION: Final = 15040  # uint16, 0-100 % (STATUS_AHU)
REG_STATUS_WORD: Final = 18000  # bitmask: bit 0 = unit running
REG_ERROR_WORD: Final = 18001  # bitmask: any non-zero = error
REG_SENSOR_STATUS: Final = 18003  # bitmask: bit per sensor OK/ERROR
REG_EXHAUST_TEMP: Final = 18005  # int16, ÷10 → °C (exhaust going outside)
REG_OUTDOOR_TEMP: Final = 18006  # int16, ÷10 → °C
REG_EXTRACT_TEMP: Final = 18007  # int16, ÷10 → °C (extract from rooms)
REG_SUPPLY_TEMP: Final = 18008  # int16, ÷10 → °C (supply into house)
REG_WATER_RETURN_TEMP: Final = 18010  # int16, ÷10 → °C (only if water heater)
REG_ROOM_TEMP: Final = 18011  # int16, ÷10 → °C (only if CT-ROOM sensor)
REG_HEATER_OUTPUT: Final = 18013  # uint16, 0-100 %
REG_FILTER_CONDITION: Final = 18015  # uint16, 0-100 %
REG_FILTER_WEAR: Final = 18016  # uint16, 0-100 %

# Holding registers (function code 0x03 read / 0x06 write)
REG_POWER: Final = 21000  # bool: 0=off, 1=on
REG_FAN_SPEED: Final = 21001  # uint16: 0-1000 ‰ (we expose as 0-100 %)
REG_TEMP_SETPOINT: Final = 21002  # int16: °C
REG_NIGHT_MODE: Final = 21009  # bool: 0=day, 1=night
REG_FILTER_HOURS: Final = 25018  # uint16: hours
REG_FILTER_HOURS_LIMIT: Final = 25019  # uint16: hours

# ─────────────────────────────────────────────────────────────────────────────
# Bulk read configuration. The coordinator reads two contiguous register
# blocks per cycle to minimise TCP round-trips:
#   - Input 15k:    15040..15040 (1 reg)
#   - Input 18k:    18000..18016 (17 regs)
#   - Holding 21k:  21000..21009 (10 regs)
#   - Holding 25k:  25018..25019 (2 regs)
# ─────────────────────────────────────────────────────────────────────────────

INPUT_BLOCK_15K_START: Final = 15040
INPUT_BLOCK_15K_COUNT: Final = 1

INPUT_BLOCK_18K_START: Final = 18000
INPUT_BLOCK_18K_COUNT: Final = 17

HOLDING_BLOCK_21K_START: Final = 21000
HOLDING_BLOCK_21K_COUNT: Final = 10

HOLDING_BLOCK_25K_START: Final = 25018
HOLDING_BLOCK_25K_COUNT: Final = 2

# ─────────────────────────────────────────────────────────────────────────────
# Status-word bit definitions. Bit 0 (running) is empirically verified against
# a real unit. Other bits remain best-guess until validated; we expose the raw
# status word as a sensor so users can decode their own.
# ─────────────────────────────────────────────────────────────────────────────

STATUS_BIT_RUNNING: Final = 1 << 0  # 0x0001 — verified

# Coordinator data keys (kept in one place to avoid typos across platforms).
DATA_STATUS_WORD: Final = "status_word"
DATA_ERROR_WORD: Final = "error_word"
DATA_SENSOR_STATUS: Final = "sensor_status"
DATA_BYPASS_POSITION: Final = "bypass_position"
DATA_OUTDOOR_TEMP: Final = "outdoor_temp"
DATA_EXHAUST_TEMP: Final = "exhaust_temp"
DATA_SUPPLY_TEMP: Final = "supply_temp"
DATA_EXTRACT_TEMP: Final = "extract_temp"
DATA_WATER_RETURN_TEMP: Final = "water_return_temp"
DATA_ROOM_TEMP: Final = "room_temp"
DATA_HEATER_OUTPUT: Final = "heater_output"
DATA_FILTER_CONDITION: Final = "filter_condition"
DATA_FILTER_WEAR: Final = "filter_wear"
DATA_POWER: Final = "power"
DATA_FAN_SPEED: Final = "fan_speed"
DATA_TEMP_SETPOINT: Final = "temp_setpoint"
DATA_NIGHT_MODE: Final = "night_mode"
DATA_FILTER_HOURS: Final = "filter_hours"
DATA_FILTER_HOURS_LIMIT: Final = "filter_hours_limit"
