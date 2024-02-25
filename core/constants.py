from __future__ import annotations

from typing import Final

DOCTOR_ROOM: Final[int] = 0
COMPUTER_ROOM: Final[int] = 1

# First room (Doctor room) constants
OPEN_WINDOW_FIRST_ROOM_PIN: Final[int] = 13
CLOSE_WINDOW_FIRST_ROOM_PIN: Final[int] = 16

# Second room (computer room) constants
OPEN_WINDOW_SECOND_ROOM_PIN: Final[int] = 5
CLOSE_WINDOW_SECOND_ROOM_PIN: Final[int] = 26

# Control constants
WINDOW_CLOSE_POSITION: Final[int] = 0
WINDOW_OPEN_POSITION: Final[int] = 1

WINDOW_OPENING_TIME: Final[int] = 9
WINDOW_CLOSING_TIME: Final[float] = 10.5

# Measurement constants
DHT_PIN: Final[int] = 6
