from __future__ import annotations

from typing import Final
import asyncio

import RPi.GPIO as GPIO

from computer_room_control.core.constants import (
    OPEN_WINDOW_FIRST_ROOM_PIN,
    OPEN_WINDOW_SECOND_ROOM_PIN,
    CLOSE_WINDOW_FIRST_ROOM_PIN,
    CLOSE_WINDOW_SECOND_ROOM_PIN,
    DOCTOR_ROOM,
    COMPUTER_ROOM,
    WINDOW_OPENING_TIME,
    WINDOW_CLOSING_TIME,
)


class InvalidRoomNumberError(Exception):
    MESSAGE: Final[
        str
    ] = """
You are trying to set a room number to a room number that does not exist.
Please use/modify the room number from core/constants.py.
"""

    def __init__(self) -> None:
        super().__init__(self.MESSAGE)


async def open_window(
    opening_time: int | float = WINDOW_OPENING_TIME, *, room: int = DOCTOR_ROOM
) -> None:
    """
    Args:
    _____
    opening_time: Opening window time. Notice that closing_time - opening_time must be equal 1.5 !
    room: Room to open the window.

    Raises:
    _______
    InvalidRoomNumberError: Raises when room is not equal Doctor or Computer room number.
    """
    if room == DOCTOR_ROOM:
        open_window_pin = OPEN_WINDOW_FIRST_ROOM_PIN
    elif room == COMPUTER_ROOM:
        open_window_pin = OPEN_WINDOW_SECOND_ROOM_PIN
    else:
        raise InvalidRoomNumberError

    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(open_window_pin, GPIO.OUT)
    GPIO.output(open_window_pin, GPIO.LOW)
    await asyncio.sleep(opening_time)
    GPIO.output(open_window_pin, GPIO.HIGH)


async def close_window(
    closing_time: int = WINDOW_CLOSING_TIME, *, room: int = DOCTOR_ROOM
) -> None:
    """
    Args:
    _____
    closing_time: Closing window time. Notice that closing_time - opening_time must be equal 1.5 !
    room: Room to close the window.

    Raises:
    _______
    InvalidRoomNumberError: Raises when room is not equal Doctor or Computer room number.
    """
    if room == DOCTOR_ROOM:
        close_window_pin = CLOSE_WINDOW_FIRST_ROOM_PIN
    elif room == COMPUTER_ROOM:
        close_window_pin = CLOSE_WINDOW_SECOND_ROOM_PIN
    else:
        raise InvalidRoomNumberError

    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)

    GPIO.setup(close_window_pin, GPIO.OUT)
    GPIO.output(close_window_pin, GPIO.LOW)
    await asyncio.sleep(closing_time)
    GPIO.output(close_window_pin, GPIO.HIGH)
