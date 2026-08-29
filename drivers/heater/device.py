"""Stone Connect heater device.

Wraps the StoneConnectHeater async client. Polls /status on a configurable
interval and reflects state into Homey capabilities. Capability writes
(onoff, target_temperature, boost_duration) are forwarded to the heater
via PUT /setpoint. The full mode enum (Comfort/Eco/Antifreeze/High/Medium/
Low/Manual) is not exposed as a UI capability — it's driven from Homey Flow
via the `set_heater_mode` action registered in the driver.
"""

import sys
from pathlib import Path

# See driver.py — make drivers/heater/lib/ importable so vendored stone_connect
# is reachable.
_LIB = str(Path(__file__).resolve().parent / "lib")
if _LIB not in sys.path:
    sys.path.insert(0, _LIB)

import asyncio
from typing import Any, Dict

from homey.device import Device

from stone_connect import (
    OperationMode,
    SetpointResponse,
    StoneConnectError,
    StoneConnectHeater,
    StoneConnectValidationError,
)


class HeaterDevice(Device):
    # Set_Point > 30 on the heater is interpreted as a boost timer in minutes
    # (max 120), only valid alongside Operative_Mode=BOOST. Values below
    # BOOST_MINUTES_MIN on the slider mean "boost off".
    BOOST_MINUTES_DEFAULT = 120
    BOOST_MINUTES_MIN = 30
    BOOST_MINUTES_MAX = 120

    # Mode used when the user turns the heater on from the UI, when they set a
    # temperature (which is only meaningful in MANUAL), and when boost ends.
    # Other modes are reachable via the `set_heater_mode` flow action.
    DEFAULT_ON_MODE = OperationMode.MANUAL

    async def on_init(self) -> None:
        await super().on_init()

        self._client: StoneConnectHeater | None = None
        self._poll_task: asyncio.Task | None = None
        self._supports_power: bool = False

        await self._migrate_capabilities()

        self.register_capability_listener("onoff", self._on_onoff)
        self.register_capability_listener(
            "target_temperature", self._on_target_temperature
        )
        self.register_capability_listener("boost_duration", self._on_boost_duration)

        await self._connect()
        self._poll_task = asyncio.create_task(self._poll_loop())

    async def _migrate_capabilities(self) -> None:
        # v1.1.0 dropped the heater_mode picker in favor of onoff + a flow
        # action for the advanced modes.
        if self.has_capability("heater_mode"):
            await self.remove_capability("heater_mode")
        if not self.has_capability("onoff"):
            await self.add_capability("onoff")
        # v1.1.0 replaced the power_boost button with the boost_duration slider.
        if not self.has_capability("boost_duration"):
            await self.add_capability("boost_duration")
            await self.set_capability_value("boost_duration", 0)
        if self.has_capability("power_boost"):
            await self.remove_capability("power_boost")

    async def on_uninit(self) -> None:
        if self._poll_task is not None:
            self._poll_task.cancel()
            try:
                await self._poll_task
            except asyncio.CancelledError:
                pass
        if self._client is not None:
            await self._client.close()
            self._client = None
        await super().on_uninit()

    async def on_settings(
        self,
        *,
        old_settings: Dict[str, Any],
        new_settings: Dict[str, Any],
        changed_keys: list,
    ) -> None:
        if any(k in changed_keys for k in ("host", "port")):
            await self._connect()

    async def _connect(self) -> None:
        if self._client is not None:
            await self._client.close()
        settings = self.get_settings()
        self._client = StoneConnectHeater(
            host=settings["host"],
            port=int(settings.get("port") or 443),
        )
        try:
            self._supports_power = await self._client.has_power_measurement_support()
        except StoneConnectError as e:
            self.error(f"could not query power support: {e}")
            self._supports_power = False

    def _poll_interval(self) -> float:
        return float(self.get_settings().get("poll_interval") or 30)

    async def _poll_loop(self) -> None:
        while True:
            try:
                await self._refresh()
            except asyncio.CancelledError:
                raise
            except StoneConnectError as e:
                self.error(f"poll failed: {e}")
            except Exception as e:
                self.error(f"unexpected poll error: {e}")
            await asyncio.sleep(self._poll_interval())

    async def _refresh(self) -> None:
        assert self._client is not None
        status = await self._client.get_status()

        in_boost = status.operative_mode == OperationMode.BOOST

        if status.operative_mode is not None:
            await self.set_capability_value(
                "onoff", status.operative_mode != OperationMode.STANDBY
            )

        if status.set_point is not None and not in_boost:
            # During BOOST, Set_Point is the remaining timer in minutes, not
            # the target temperature — don't clobber the slider with it.
            await self.set_capability_value(
                "target_temperature", float(status.set_point)
            )

        if in_boost:
            remaining = int(status.set_point) if status.set_point is not None else 0
            remaining = self._snap_boost_value(remaining)
            await self.set_capability_value("boost_duration", float(remaining))
        else:
            await self.set_capability_value("boost_duration", 0)

        if status.error_code is not None:
            await self.set_capability_value("alarm_generic", status.error_code != 0)

        if self._supports_power:
            if status.power_consumption_watt is not None:
                await self.set_capability_value(
                    "measure_power", float(status.power_consumption_watt)
                )
            # daily_energy is reported in Wh; convert to kWh for meter_power
            if status.daily_energy is not None:
                await self.set_capability_value(
                    "meter_power", float(status.daily_energy) / 1000.0
                )

    def _snap_boost_value(self, minutes: int) -> int:
        # Slider step is 30; snap arbitrary heater-reported values onto the
        # nearest allowed preset so the UI doesn't display an out-of-step tick.
        if minutes < self.BOOST_MINUTES_MIN:
            return 0
        minutes = min(self.BOOST_MINUTES_MAX, minutes)
        return int(round(minutes / 30) * 30)

    async def _send_boost(self, minutes: int | None = None) -> SetpointResponse:
        assert self._client is not None
        if minutes is None:
            minutes = self.BOOST_MINUTES_DEFAULT
        minutes = max(self.BOOST_MINUTES_MIN, min(self.BOOST_MINUTES_MAX, int(minutes)))
        info = await self._client.get_info()
        body = {
            "Client_ID": info.client_id,
            "Operative_Mode": OperationMode.BOOST.value,
            "Set_Point": minutes,
        }
        data = await self._client._request("PUT", "setpoint", body)
        return SetpointResponse.from_dict(data)

    async def _cancel_boost(self) -> SetpointResponse:
        # The heater has no explicit "end boost" command; drop back to the
        # default on-mode. Any prior mode set via flow is not preserved — the
        # user can re-trigger it if needed.
        return await self._change_mode(self.DEFAULT_ON_MODE)

    async def set_mode(self, mode: OperationMode) -> SetpointResponse:
        """Send an operation-mode change. Used by the driver's flow action."""
        return await self._change_mode(mode)

    async def _change_mode(self, mode: OperationMode) -> SetpointResponse:
        # Never route mode changes through client.set_operation_mode() for
        # non-preset modes: that helper reads the heater's current Set_Point
        # to reuse as a temperature, and during BOOST Set_Point is the
        # remaining timer in minutes (e.g. 86) — which then fails the client's
        # 0-30°C temperature validation. Instead, source a safe temperature
        # from our target_temperature capability, which the poll loop
        # deliberately leaves at the pre-boost value while boost is running.
        # Preset modes (Comfort/Eco/Antifreeze) go via the client so we honor
        # the heater's configured preset setpoints; power modes (High/Medium/
        # Low) don't use the setpoint at all.
        assert self._client is not None
        if mode.is_preset_mode():
            return await self._client.set_operation_mode(mode)
        current_temp = self.get_capability_value("target_temperature")
        temp = float(current_temp) if current_temp is not None else 20.0
        return await self._client.set_temperature_and_mode(temp, mode)

    async def _notify_setpoint_echo(self, response: SetpointResponse) -> None:
        mode = response.operative_mode.value if response.operative_mode else "?"
        set_point = response.set_point if response.set_point is not None else "?"
        message = (
            f"**{self.get_name()}** ack: mode=**{mode}**, Set_Point=**{set_point}**"
        )
        try:
            await self.homey.notifications.create_notification(message)
        except Exception as e:
            self.error(f"failed to post timeline notification: {e}")

    async def _on_onoff(
        self, value: bool, opts: Dict[str, Any] | None = None
    ) -> None:
        mode = self.DEFAULT_ON_MODE if value else OperationMode.STANDBY
        response = await self._change_mode(mode)
        if not value and self.get_capability_value("boost_duration"):
            await self.set_capability_value("boost_duration", 0)
        await self._notify_setpoint_echo(response)

    async def _on_target_temperature(
        self, value: float, opts: Dict[str, Any] | None = None
    ) -> None:
        # Setting a temperature only makes sense in MANUAL — the presets have
        # their own fixed setpoints on the heater.
        assert self._client is not None
        try:
            response = await self._client.set_temperature_and_mode(
                value, self.DEFAULT_ON_MODE
            )
        except StoneConnectValidationError as e:
            raise ValueError(str(e))
        # Sending any non-BOOST mode ends the boost timer on the heater; snap
        # the slider back to 0 now so the UI matches without waiting for the
        # next /status poll.
        if self.get_capability_value("boost_duration"):
            await self.set_capability_value("boost_duration", 0)
        await self._notify_setpoint_echo(response)

    async def _on_boost_duration(
        self, value: float, opts: Dict[str, Any] | None = None
    ) -> None:
        minutes = int(value)
        if minutes < self.BOOST_MINUTES_MIN:
            response = await self._cancel_boost()
        else:
            response = await self._send_boost(minutes)
        await self._notify_setpoint_echo(response)


homey_export = HeaterDevice
