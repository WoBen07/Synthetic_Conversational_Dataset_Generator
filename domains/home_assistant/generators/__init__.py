"""Generators of the home_assistant domain (added to the shared ones)."""

from .devices import (
    automation,
    brightness_pct,
    generic_light,
    home,
    indoor_generic_light,
    impossible_brightness,
    impossible_temperature,
    indoor_room,
    light,
    light_color,
    lock,
    missing_room,
    missing_scene,
    missing_switch,
    named_light,
    non_white_light_color,
    room,
    scene,
    switch,
    target_temperature,
    vacuum,
)


GENERATORS = {

    "home": home,

    "room": room,
    "indoor_room": indoor_room,
    "missing_room": missing_room,

    "light": light,
    "generic_light": generic_light,
    "indoor_light": indoor_generic_light,
    "named_light": named_light,

    "light_color": light_color,
    "non_white_light_color": non_white_light_color,

    "brightness_pct": brightness_pct,
    "impossible_brightness": impossible_brightness,

    "target_temperature": target_temperature,
    "impossible_temperature": impossible_temperature,

    "vacuum": vacuum,

    "switch": switch,
    "missing_switch": missing_switch,

    "scene": scene,
    "missing_scene": missing_scene,

    "automation": automation,

    "lock": lock,
}
