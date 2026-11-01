"""Generators of the home_assistant domain (added to the shared ones)."""

from .devices import (
    brightness_pct,
    light,
    light_color,
    non_white_light_color,
    room,
    target_temperature,
    vacuum_name,
)


GENERATORS = {

    "room": room,
    "light": light,

    "light_color": light_color,
    "non_white_light_color": non_white_light_color,

    "brightness_pct": brightness_pct,
    "target_temperature": target_temperature,

    "vacuum_name": vacuum_name,
}
