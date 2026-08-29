"""Stone Connect heater driver.

Pairing flow:
- The `manual_ip` view collects the heater's host+port and emits `ip_entered`.
- `ip_entered` calls /info to verify connectivity and stash host, port, MAC.
- `list_devices` returns a single device descriptor keyed by MAC. Homey's
  built-in `add_devices` step then handles the zone/icon picker.
"""

import sys
from pathlib import Path

# Vendored heater client lives at drivers/heater/lib/stone_connect/. Add that
# folder to sys.path so `import stone_connect` resolves regardless of how the
# runtime imports this module. Anchored to __file__ to avoid assumptions about
# the runtime's working dir or package layout.
_LIB = str(Path(__file__).resolve().parent / "lib")
if _LIB not in sys.path:
    sys.path.insert(0, _LIB)

from typing import Any, Dict, List, Mapping

from homey.driver import Driver

from stone_connect import OperationMode, StoneConnectError, StoneConnectHeater

DEFAULT_PORT = 443


class HeaterDriver(Driver):
    async def on_init(self) -> None:
        await super().on_init()

        activate_boost = self.homey.flow.get_action_card("activate_boost")

        async def on_activate_boost(
            args: Mapping[str, Any], **_trigger_kwargs: Any
        ) -> None:
            device = args["device"]
            minutes = args.get("minutes")
            response = await device._send_boost(minutes)
            await device._notify_setpoint_echo(response)

        activate_boost.register_run_listener(on_activate_boost)

        set_heater_mode = self.homey.flow.get_action_card("set_heater_mode")

        async def on_set_heater_mode(
            args: Mapping[str, Any], **_trigger_kwargs: Any
        ) -> None:
            device = args["device"]
            mode_id = args.get("mode")
            try:
                mode = OperationMode(mode_id)
            except ValueError:
                raise ValueError(f"Unknown heater mode: {mode_id}")
            response = await device.set_mode(mode)
            await device._notify_setpoint_echo(response)

        set_heater_mode.register_run_listener(on_set_heater_mode)

        self.log("HeaterDriver initialized")

    async def on_pair(self, session: Any) -> None:
        state: Dict[str, Any] = {
            "host": None,
            "port": DEFAULT_PORT,
            "name": None,
            "device_id": None,
        }

        async def on_ip_entered(payload: Any) -> bool:
            # Accept either a bare IP string (legacy) or {host, port} from the view.
            if isinstance(payload, dict):
                host = (payload.get("host") or "").strip()
                port = int(payload.get("port") or DEFAULT_PORT)
            else:
                host = (payload or "").strip()
                port = DEFAULT_PORT
            if not host:
                raise ValueError("Please enter an IP address.")

            async with StoneConnectHeater(host=host, port=port) as client:
                try:
                    raw_info = await client._request("GET", "info")
                    info = await client.get_info()
                except StoneConnectError as e:
                    raise RuntimeError(
                        f"Could not connect to heater at {host}:{port}: {e}"
                    )

            self.log(
                f"/info raw keys={sorted(raw_info.keys()) if isinstance(raw_info, dict) else type(raw_info).__name__}"
            )
            self.log(
                f"/info parsed: client_id={info.client_id!r} "
                f"mac={info.mac_address!r} appliance_sn={info.appliance_sn!r} "
                f"housing_sn={info.housing_sn!r}"
            )

            # Prefer hardware identifiers in order of stability. Client_ID is
            # always present (the upstream client uses it for PUT /setpoint).
            device_id = (
                info.mac_address
                or info.appliance_sn
                or info.housing_sn
                or info.client_id
            )
            if not device_id:
                seen_keys = (
                    sorted(raw_info.keys())
                    if isinstance(raw_info, dict)
                    else f"<{type(raw_info).__name__}>"
                )
                raise RuntimeError(
                    "Heater /info response had no usable hardware identifier "
                    f"(MAC, serial, or Client_ID). Raw keys: {seen_keys}"
                )

            state["host"] = host
            state["port"] = port
            state["device_id"] = device_id
            state["name"] = (
                info.appliance_name or info.zone_name or "Stone Connect Heater"
            )
            return True

        async def on_list_devices(_data: Any = None) -> List[Dict[str, Any]]:
            if not state["host"] or not state["device_id"]:
                return []
            return [
                {
                    "name": state["name"],
                    "data": {"id": state["device_id"]},
                    "settings": {
                        "host": state["host"],
                        "port": state["port"],
                        "poll_interval": 30,
                    },
                }
            ]

        session.set_handler("ip_entered", on_ip_entered)
        session.set_handler("list_devices", on_list_devices)


homey_export = HeaterDriver
