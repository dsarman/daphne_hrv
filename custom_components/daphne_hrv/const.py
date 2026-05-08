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
REG_STATUS_WORD: Final = 15007  # STATUS_AHU Status_DO; bit 2 = run indication
REG_BYPASS_POSITION: Final = 15040  # uint16, 0-100 % (STATUS_AHU)
REG_ERROR_WORD: Final = 18001  # bitmask: any non-zero = error
REG_SENSOR_STATUS: Final = 18003  # bitmask: bit per sensor OK/ERROR
REG_EXHAUST_TEMP: Final = 18005  # int16, ÷10 → °C (exhaust going outside)
REG_OUTDOOR_TEMP: Final = 18006  # int16, ÷10 → °C
REG_SUPPLY_TEMP: Final = 18007  # int16, ÷10 → °C (supply into house)
REG_EXTRACT_TEMP: Final = 18008  # int16, ÷10 → °C (extract from rooms)
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
REG_TEMP_SENSOR_SELECTION: Final = 25008  # 0=supply, 1=extract, 2=room, 3=thermostat, 4=room BMS
REG_FILTER_HOURS: Final = 25018  # uint16: hours
REG_FILTER_HOURS_LIMIT: Final = 25019  # uint16: hours

# ─────────────────────────────────────────────────────────────────────────────
# Bulk read configuration. The coordinator reads two contiguous register
# blocks per cycle to minimise TCP round-trips:
#   - Input 15k:    15007..15040 (34 regs)
#   - Input 18k:    18000..18016 (17 regs)
#   - Holding 21k:  21000..21009 (10 regs)
#   - Holding 25k:  25008..25019 (12 regs)
# ─────────────────────────────────────────────────────────────────────────────

INPUT_BLOCK_15K_START: Final = 15007
INPUT_BLOCK_15K_COUNT: Final = 34

INPUT_BLOCK_18K_START: Final = 18000
INPUT_BLOCK_18K_COUNT: Final = 17

HOLDING_BLOCK_21K_START: Final = 21000
HOLDING_BLOCK_21K_COUNT: Final = 10

HOLDING_BLOCK_25K_START: Final = 25008
HOLDING_BLOCK_25K_COUNT: Final = 12

# ─────────────────────────────────────────────────────────────────────────────
# Status-word bit definitions. Running is AirGENIO STATUS_AHU Status_DO bit 2,
# empirically verified against a real unit. Additional bits below come from the
# AirGENIO/TapHome status labels; raw word sensors stay exposed for validation.
# ─────────────────────────────────────────────────────────────────────────────

STATUS_BIT_RUNNING: Final = 1 << 2  # 0x0004 — verified
STATUS_BIT_ERROR_INDICATION: Final = 1 << 3  # 0x0008 — Status_DO_4_Error
STATUS_BIT_EXCHANGER_HEATING: Final = 1 << 4  # 0x0010 — Status_DO_5_Heat_cool
STATUS_BIT_WATER_PUMP: Final = 1 << 5  # 0x0020 — Status_DO_6_Water_pump

SENSOR_STATUS_BIT_OUTDOOR: Final = 1 << 0
SENSOR_STATUS_BIT_EXHAUST: Final = 1 << 1
SENSOR_STATUS_BIT_SUPPLY: Final = 1 << 2
SENSOR_STATUS_BIT_WATER_RETURN: Final = 1 << 3
SENSOR_STATUS_BIT_ROOM: Final = 1 << 4
SENSOR_STATUS_BIT_BMS: Final = 1 << 5

TEMP_SENSOR_SELECTION_SUPPLY: Final = 0
TEMP_SENSOR_SELECTION_EXTRACT: Final = 1
TEMP_SENSOR_SELECTION_ROOM: Final = 2
TEMP_SENSOR_SELECTION_THERMOSTAT: Final = 3
TEMP_SENSOR_SELECTION_ROOM_BMS: Final = 4

TEMP_SENSOR_SELECTION_OPTIONS: Final[dict[int, str]] = {
    TEMP_SENSOR_SELECTION_SUPPLY: "supply_duct",
    TEMP_SENSOR_SELECTION_EXTRACT: "extract_duct",
    TEMP_SENSOR_SELECTION_ROOM: "room",
    TEMP_SENSOR_SELECTION_THERMOSTAT: "thermostat",
    TEMP_SENSOR_SELECTION_ROOM_BMS: "room_bms",
}

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
DATA_TEMP_SENSOR_SELECTION: Final = "temp_sensor_selection"
DATA_FILTER_HOURS: Final = "filter_hours"
DATA_FILTER_HOURS_LIMIT: Final = "filter_hours_limit"
