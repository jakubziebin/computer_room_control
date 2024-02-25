from __future__ import annotations

import sys
import os
import csv
import aiohttp
import asyncio
from typing import Final
from datetime import datetime, timedelta

from textual import on, work
from textual.containers import Horizontal
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Button, Static
from textual.reactive import var
from DFRobot_SCD4X import *
import RPi.GPIO as GPIO
import Adafruit_DHT

from computer_room_control.window_functions.window_functions import (
    open_window,
    close_window,
)
from computer_room_control.core.constants import (
    WINDOW_OPEN_POSITION,
    WINDOW_CLOSE_POSITION,
    DOCTOR_ROOM,
    COMPUTER_ROOM,
    DHT_PIN
)

sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))


class ComputerRoomApp(App):
    DEFAULT_CSS = """
    Button {
        height: 12;
        width: 20;
        margin-left: 2;
        margin-right: 2;
    }

    Horizontal {
        align: center middle;
        width: 1fr;
    }

    Static {
        align: center middle;
        width: 1fr;
        text-style: bold;
        text-align: center;
        background: rgb(123, 20, 31);
    }
    """

    def __init__(self):
        """
        Initialize control app.

        Attributes:
        ___________
        _temperature_first_room: Temperature in the Doctor room measure by DHT22.
        _temperature_second_room: Temperature in the computer room measure by Dfrobot sensor.
        _co2_second_room: CO2 value in the computer room measure by Dfrobot sensor.
        _temperature_outside: Outdoor temperature taken from the public API.
        _window_position_first_room: Position of the window in the first (Doctor) room.
        _window_position_second_room: Position of the window in the second (computer) room.
        _is_auto_mode_first_room: Is auto mode was activated in the first room.
        _is_auto_mode_second_room: Is auto mode was activated in the second room.
        """
        super().__init__()
        # Measurement parameters
        self._temperature_first_room = var(0)
        """Used to detect when auto mode script first room must be executed."""
        self._temperature_second_room = var(0)
        """Used to detect when auto mode script second room must be executed."""
        self._co2_second_room = 0
        self._temperature_outside = 0

        # Control parameters
        self._window_position_first_room = WINDOW_CLOSE_POSITION
        self._window_position_second_room = WINDOW_CLOSE_POSITION
        self._is_auto_mode_first_room = False
        self._is_auto_mode_second_room = False

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("First room")
        yield Static(
            f"Auto mode: {self._auto_mode_first_room}", id="mode-display-first-room"
        )
        with Horizontal():
            yield Button("Close", id="close-window-first-room-button")
            yield Button("Open", id="open-window-first-room-button")
            yield Button("Change mode", id="change-mode-first-room-button")
        yield Static("Second room")
        yield Static(
            f"Auto mode: {self.auto_mode_second}", id="mode-display-second-room"
        )
        with Horizontal():
            yield Button("Close", id="close-window-second-room-button")
            yield Button("Open", id="open-window-second-room-button")
            yield Button("Change mode", id="change-mode-second-room-button")
        yield Footer()

    def on_mount(self) -> None:
        self._check_last_window_positions()
        self.set_interval(60, self.measurements)
        self.watch(self, "_temperature_first_room", self.auto_mode_script_first_room)
        self.watch(self, "_temperature_second_room", self.auto_mode_script_second_room)

    def _check_last_window_positions(self) -> None:
        """On activating application read last window position before closer app"""
        try:
            with open("data.csv", "r") as file:
                reader = csv.DictReader(file)
                last_row = None
                for row in reader:
                    last_row = row
                if last_row:
                    self._window_position_first_room = int(
                        last_row["window_position_first_room"]
                    )
                    self._window_position_second_room = int(
                        last_row["window_position_second_room"]
                    )
                    self.notify(
                        f"Actual window position first: {self._window_position_first_room}, "
                        f"second: {self._window_position_second_room}"
                    )
                else:
                    pass
        except FileNotFoundError:
            pass

    @on(Button.Pressed, "#close-window-first-room-button")
    async def close_window_first_room(self) -> None:
        if self._is_auto_mode_first_room:
            return

        if self._window_position_first_room == WINDOW_CLOSE_POSITION:
            return

        self._window_position_first_room = WINDOW_CLOSE_POSITION
        self.save_data()
        await close_window(room=DOCTOR_ROOM)

    @on(Button.Pressed, "#open-window-first-room-button")
    async def open_window_first_room(self) -> None:
        if self._is_auto_mode_first_room:
            return

        if self._window_position_first_room == WINDOW_OPEN_POSITION:
            return

        self._window_position_first_room = WINDOW_OPEN_POSITION
        self.save_data()
        await open_window(room=DOCTOR_ROOM)

    @on(Button.Pressed, "#close-window-second-room-button")
    async def close_window_second_room(self) -> None:
        if self._is_auto_mode_second_room:
            return

        if self._window_position_second_room == WINDOW_CLOSE_POSITION:
            return

        self._window_position_second_room = WINDOW_CLOSE_POSITION
        self.save_data()
        await close_window(room=COMPUTER_ROOM)

    @on(Button.Pressed, "#open-window-second-room-button")
    async def open_window_second_room(self) -> None:
        if self._is_auto_mode_second_room:
            return

        if self._window_position_second_room == WINDOW_OPEN_POSITION:
            return

        self._window_position_second_room = WINDOW_OPEN_POSITION
        self.save_data()
        await open_window(room=COMPUTER_ROOM)

    @on(Button.Pressed, "#change-mode-first-room-button")
    async def change_mode_first_room(self) -> None:
        if self._window_position_first_room == WINDOW_OPEN_POSITION:
            self._window_position_first_room = WINDOW_CLOSE_POSITION
            await close_window(room=DOCTOR_ROOM)

        self._is_auto_mode_first_room = not self._is_auto_mode_first_room

        await self.query_one("#mode-display-first").update(
            f"Auto mode: {self._is_auto_mode_first_room}"
        )
        self.save_data()

    @on(Button.Pressed, "#change-mode-second-room-button")
    async def change_mode_second_room(self) -> None:
        if self._window_position_second_room == WINDOW_OPEN_POSITION:
            self._window_position_second_room = WINDOW_CLOSE_POSITION
            await close_window(room=COMPUTER_ROOM)

        self._is_auto_mode_second_room = not self._is_auto_mode_second_room

        await self.app.query_one("#mode-display-second").update(
            f"Auto mode: {self._is_auto_mode_second_room}"
        )
        self.save_data()

    async def auto_mode_script_first_room(self) -> None:
        max_temperature: Final[int] = 23
        min_temperature: Final[int] = 20
        min_temperature_outside: Final[int] = 15

        if not self._is_auto_mode_first_room:
            return

        dt = self._temperature_first_room - self._temperature_outside

        if self._temperature_outside < min_temperature_outside or dt < 2:
            if self._window_position_first_room == WINDOW_OPEN_POSITION:
                self._window_position_first_room = WINDOW_CLOSE_POSITION
                await close_window(room=DOCTOR_ROOM)
                return

        if (
            self._window_position_first_room == WINDOW_CLOSE_POSITION
            and self._temperature_first_room > max_temperature
        ):
            self._window_position_first_room = WINDOW_OPEN_POSITION
            await open_window(room=DOCTOR_ROOM)
            return

        if (
            self._window_position_first_room == WINDOW_OPEN_POSITION
            and self._temperature_first_room < min_temperature
        ):
            self._window_position_first_room = WINDOW_CLOSE_POSITION
            await close_window(room=DOCTOR_ROOM)
            return

    async def auto_mode_script_second_room(self) -> None:
        min_temperature: Final[int] = 20
        max_temperature: Final[int] = 23
        min_temperature_outside: Final[int] = 5

        min_co2: Final[int] = 800
        max_co2: Final[int] = 1000

        # Window reason open: 0 -> Unknown, 1 -> temperature, 2 -> co2

        if not self._is_auto_mode_second_room:
            return

        dt = self._temperature_second_room - self._temperature_outside

        if self._temperature_outside < min_temperature_outside:
            if self._window_position_second_room == WINDOW_OPEN_POSITION:
                self._window_position_second_room = WINDOW_CLOSE_POSITION
                await close_window(room=COMPUTER_ROOM)
                self.save_data()
                return
            return

        if (
            self._window_position_second_room == WINDOW_CLOSE_POSITION
            and self._temperature_second_room > max_temperature
            and dt > 2
        ):
            self._window_position_second_room = WINDOW_OPEN_POSITION
            window_reason_open = 1
            await open_window(room=COMPUTER_ROOM)
            self.save_data(why_open=window_reason_open)
            return

        if (
            self._window_position_second_room == WINDOW_CLOSE_POSITION
            and self._co2_second_room > max_co2
        ):
            self._window_position_second_room = WINDOW_OPEN_POSITION
            window_reason_open = 2
            await open_window(room=COMPUTER_ROOM)
            self.save_data(why_open=window_reason_open)
            return

        if (
            self._window_position_second_room == WINDOW_OPEN_POSITION
            and self._temperature_second_room < min_temperature
        ):
            self._window_position_second_room = WINDOW_CLOSE_POSITION
            await close_window(room=COMPUTER_ROOM)
            self.save_data()
            return

        if (
            self._window_position_second_room == WINDOW_OPEN_POSITION
            and self._co2_second_room < min_co2
        ):
            self._window_position_second_room = WINDOW_CLOSE_POSITION
            await close_window(room=COMPUTER_ROOM)
            self.save_data()
            return

    @work(name="measurements worker")
    async def measurements(self) -> None:
        co2, temperature, humidity = await self.read_values_from_co2_sensor()
        self.notify(f"{co2} ppm {temperature} C {humidity} %")
        self._co2_second_room = co2
        self._temperature_second_room = temperature
        # Humidity is not used, so it is not assigned to anything.

        humidity, temperature = await Adafruit_DHT.read_retry(
            Adafruit_DHT.DHT22, DHT_PIN
        )

        if humidity is None or temperature is None:
            self._temperature_first_room = 20.0
            # in case of DHT emergency
        else:
            self._temperature_first_room = float(temperature)

        self._temperature_outside = await self.read_values_from_api()
        self.save_data()
        self.clean_data_file()

    def save_data(self, why_open: int = 0) -> None:
        is_file_exists = os.path.isfile("data.csv")
        if is_file_exists:
            self.clean_data_file()

        headers = (
            "temp_outside",
            "temp_first_room",
            "window_position_first_room",
            "temp_second_room",
            "co2",
            "window_position_second_room",
            "why_open",
        )

        data_to_write = {
            "temp_outside": self._temperature_outside,
            "temp_first_room": self._temperature_first_room,
            "window_position_first_room": self._window_position_first_room,
            "temp_second_room": self._temperature_second_room,
            "co2": self._co2_second_room,
            "window_position_second_room": self._window_position_second_room,
            "why_open": why_open,
        }

        with open("data.csv", "a", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=headers)
            if not is_file_exists:
                writer.writeheader()
            self.notify(f"savings data! {data_to_write}")
            writer.writerow(data_to_write)

    async def read_values_from_api(self) -> float:
        api_key = "0f0110a503e17bdf9c9c074b5c4b6e08"
        location = "Gliwice,PL"
        url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={api_key}"

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                data = await response.json()

                temperature_k = data["main"]["temp"]
                temperature_c = round(temperature_k - 273.15, 2)
                return float(temperature_c)

    async def read_values_from_co2_sensor(self) -> tuple[float, ...]:
        sensor = DFRobot_SCD4X(i2c_addr=SCD4X_I2C_ADDR, bus=1)

        while not await sensor.begin:
            await asyncio.sleep(3)

        await sensor.enable_period_measure(SCD4X_STOP_PERIODIC_MEASURE)
        if 0 != await sensor.perform_self_test:
            await sensor.set_sleep_mode(SCD4X_WAKE_UP)

        average_co2_ppm = 0
        average_temperature = 0
        average_humidity = 0
        for i in range(0, 6):
            await sensor.measure_single_shot(SCD4X_MEASURE_SINGLE_SHOT)
            while not sensor.get_data_ready_status:
                await asyncio.sleep(0.1)

            co2_ppm, temp, humidity = sensor.read_measurement
            if (
                0 != i
            ):  # Discard the first set of data, because the chip datasheet indicates they are invalid
                average_co2_ppm += co2_ppm
                average_temperature += temp
                average_humidity += humidity

        return average_co2_ppm / 5, average_temperature / 5, average_humidity / 5

    def clean_data_file(self) -> None:
        """Clean data that is older than 2 weeks."""
        file_path: Final[str] = "data.csv"
        two_weeks_ago = datetime.now() - timedelta(weeks=2)

        if os.path.exists(file_path):
            file_modified_time = datetime.fromtimestamp(os.path.getmtime(file_path))

            if file_modified_time < two_weeks_ago:
                with open(file_path, "w", newline="") as file:
                    file.truncate()
                self.notify("Data file cleaned !")


try:
    app = ComputerRoomApp()
    asyncio.run(app.run_async())
except KeyboardInterrupt:
    GPIO.cleanup()
