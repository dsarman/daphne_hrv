# 2VV Daphne HRV — Home Assistant Integration

A Home Assistant custom integration for **[2VV Daphne](https://www.2vv.cz/en/products/daphne/)** heat-recovery ventilation units, controlled over **Modbus TCP** through the unit's built-in AirGENIO controller.

> **Status:** v0.1 — core entities only. No external add-ons or YAML required; configures from the UI.

## Features

- **Power switch** — turn the unit on/off
- **Fan speed** — 0–100 % slider (the unit's native 0–1000 ‰ range, scaled)
- **Temperature setpoint** — 10–30 °C
- **Night mode** switch
- **Sensors** — outdoor / supply / exhaust / extract / room / water-return temperatures, filter wear & hours, heater output
- **Diagnostics** — running state, error state, raw status registers for advanced bitmask decoding
- Single-poll coordinator (one bulk Modbus read per cycle, ~3 round-trips total)
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

## Status-word decoding

The Daphne exposes some state as bitmasks in registers `18000` (`status_word`) and `18005` (`sub_status`). Bit 0 of `status_word` is verified as **running**. Other bits are not yet documented for this firmware — capture the raw value while toggling features on the controller and share your findings via an issue/PR.

## Roadmap

- v0.2: `select` entity for temperature-control source, decoded bitmask binary sensors
- v0.3: `climate` entity (once mode register behaviour is validated)
- v0.4: BMS outdoor-temp override, schedules
- v1.0: HACS default store submission

## Disclaimer

Not affiliated with 2VV. The register map is based on the publicly distributed **AirGENIO Modbus RTU/TCP Manual** and the [TapHome Daphne template](https://taphome.com/en/compatibility/2vv-daphne/), validated empirically against a Daphne Flat unit.

## License

MIT — see [LICENSE](LICENSE).
