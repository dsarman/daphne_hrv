# 2VV Daphne HRV — Home Assistant Integration

A Home Assistant custom integration for **[2VV Daphne](https://www.2vv.cz/en/products/daphne/)** heat-recovery ventilation units, controlled over **Modbus TCP** through the unit's built-in AirGENIO controller.

## Features

- **Power switch** — turn the unit on/off
- **Climate entity** — control unit power, target temperature, and fan speed from Home Assistant's climate UI
- **Fan speed** — 20–100 % slider (the unit's native 0–1000 ‰ range, scaled)
- **Temperature setpoint** — 10–30 °C
- **Temperature control source** — choose supply duct, extract duct, room, thermostat, or room BMS
- **Night mode** switch
- **Sensors** — outdoor / supply / exhaust / extract / room / water-return temperatures, filter wear & hours, heater output
- **Diagnostics** — running state, error state, raw status registers for advanced bitmask decoding
- Single-poll coordinator (four Modbus block reads per cycle)
- Local polling, no cloud

## Requirements

- A 2VV Daphne unit with the **AirGENIO SUPERIOR / IC / SC (module-A)** control board (native Modbus TCP via RJ45). Verify by entering service code `1616` on the controller — if menu **21 - Network** exists, you have the right board.
- The unit's IP address (configurable in the same Network menu)
- Home Assistant **2024.10** or newer

If you have the **COMFORT (module-B)** board instead, you only have RS-485 (no native TCP). You can still use this integration via a Modbus RTU-to-TCP gateway (e.g. Waveshare RS485-to-ETH) — see [Hardware notes](#hardware-notes).

## Installation

### HACS (recommended)

1. In HACS, open the three-dot menu → **Custom repositories**
2. URL: `https://github.com/dsarman/daphne_hrv`
3. Category: **Integration** → **Add**
4. Find **2VV Daphne HRV** in the integration list and install
5. Restart Home Assistant
6. **Settings → Devices & Services → Add Integration → 2VV Daphne HRV**

### Manual

Copy `custom_components/daphne_hrv/` into your Home Assistant config directory's `custom_components/` folder, restart, then add the integration from the UI.

## Configuration

The setup form asks for:

| Field | Default | Notes |
|---|---|---|
| Name | `Daphne HRV` | Display name in HA |
| Host | — | IP address of the unit |
| Port | `502` | Standard Modbus TCP |
| Slave / unit ID | `1` | Set in the unit's service menu |

The integration will probe the connection during setup; if it fails, check the IP, port and that the unit is reachable on your network.

## Hardware notes

- **AirGENIO SUPERIOR** (module-A): native Modbus TCP, plug Ethernet into the controller's RJ45 and you're done. Default IP `192.168.0.100`.
- **AirGENIO COMFORT** (module-B): RS-485 only at 9600/8/ODD/1. Use a transparent TCP gateway (Waveshare RS485-to-ETH, USR-TCP232, etc.) — point it at the controller's RS-485 terminals (B=pin25, A=pin24, GND=pin23) and configure this integration with the gateway's IP.

## Temperature control source

The temperature control source select writes holding register `25008`:

- `0` — supply duct
- `1` — extract duct
- `2` — room
- `3` — thermostat
- `4` — room BMS

## Climate entity

The climate entity intentionally exposes only validated controls:

- `OFF` turns the unit off through holding register `21000`.
- `AUTO` turns the unit on through holding register `21000`.
- Target temperature writes the confirmed setpoint register `21002` in whole °C.
- Current temperature follows the selected temperature-control source when that source has a readable temperature sensor.
- Fan mode exposes the existing validated fan-speed control as 5% steps (`20%`, `25%`, …, `100%`) and writes the confirmed fan-speed register `21001`.

The separate fan-speed number entity remains available for dashboards or automations that prefer a slider.

The AirGENIO automatic/manual temperature-control mode register is documented as PLC `H:25033` / raw `H:25032`, but this integration does not write it yet because mode-write behaviour has not been validated on the live unit.

## Status-word decoding

The Daphne exposes state as bitmasks in `15007` (`status_word`), `18001` (`error_word`) and `18003` (`sensor_status`). `status_word` bit 2 is verified as **running**. The integration also exposes decoded diagnostic binary sensors for documented status and temperature-sensor problem bits, while keeping the raw word sensors available for validation.

## Disclaimer

Not affiliated with 2VV. The register map is based on the publicly distributed **AirGENIO Modbus RTU/TCP Manual** and the [TapHome Daphne template](https://taphome.com/en/compatibility/2vv-daphne/), validated empirically against a Daphne Flat unit.

## License

MIT — see [LICENSE](LICENSE).
