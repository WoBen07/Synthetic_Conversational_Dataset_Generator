"""Build the home of one conversation, once its entities exist.

The conversation's own devices are always part of it, everything else is drawn
at random, so every datapoint has another home and the model has to read the
list in the system message instead of learning one home. A scenario can ask
for more in a ``home`` block::

    home:
      require: {room: [heating]}     # entity -> devices in its room
      room_absent: {room: [blinds]}  # entity -> devices not in its room
      absent: [vacuum]               # not anywhere in the home
      min_light_rooms: 2             # more than one room to mean
      require_some: [heating]        # in at least one room of the home
      require_home: [alarm]          # a whole-home device
      single_room: true              # a home of one room
"""

import random

from .generators.devices import (
    AUTOMATIONS,
    INDOOR_ROOMS,
    LOCKS,
    NAMED_LIGHTS,
    OUTDOOR_ROOMS,
    ROBOT_NAMES,
    ROOMS,
    SAME_ROOM,
    SCENES,
    SWITCHES,
    UNNAMED_ROBOT_SHARE,
)


MAX_ROOMS = 7

# Share of rooms with a device, when nothing requires it
ROOM_DEVICES = {"heating": 0.85, "blinds": 0.4, "media": 0.25}

SENSORS = {"humidity": "Luftfeuchtigkeit", "window": "Fenster"}

SENSOR_SHARE = 0.3

# Share of homes with a device
HOME_DEVICES = {"vacuum": 0.8, "alarm": 0.3, "garage": 0.25}


def _entities(context):
    return [entity for entity in context.values() if isinstance(entity, dict)]


def _new_room():
    return {
        "lights": set(),
        "has_light": False,
        "heating": False,
        "blinds": False,
        "media": False,
        "sensors": set(),
        "switches": set(),
    }


def _room_list(names):

    names = list(names)

    if len(names) == 1:
        return names[0]

    return f"{', '.join(names[:-1])} und {names[-1]}"


def _draw_rooms(rooms, unavailable, spec):

    wanted = 1 if spec.get("single_room") else random.randint(2, MAX_ROOMS)

    candidates = [name for name in ROOMS if name not in unavailable]

    random.shuffle(candidates)

    for name in candidates:

        if len(rooms) >= wanted:
            break

        if SAME_ROOM.get(name) not in rooms:
            rooms.setdefault(name, _new_room())


def _draw_room_devices(rooms, spec, room_absent):

    absent = set(spec.get("absent") or [])

    used_lights = {name for room in rooms.values() for name in room["lights"]}
    used_switches = {name for room in rooms.values() for name in room["switches"]}

    required_lights_only = spec.get("single_room")

    for name, room in rooms.items():

        banned = room_absent.get(name, set()) | absent

        indoor = name not in OUTDOOR_ROOMS

        if "light" not in banned and (room["has_light"] or random.random() < 0.9):

            room["has_light"] = True

            if not required_lights_only and indoor:

                for light_name, _, _, allowed in random.sample(NAMED_LIGHTS, random.choice([0, 0, 1, 1, 2])):

                    if light_name not in used_lights and (allowed is None or name in allowed):
                        used_lights.add(light_name)
                        room["lights"].add(light_name)

        if indoor:

            for device, share in ROOM_DEVICES.items():

                if device not in banned and random.random() < share:
                    room[device] = True

            for sensor in SENSORS:

                if sensor not in banned and random.random() < SENSOR_SHARE:
                    room["sensors"].add(sensor)

            if "switch" not in banned and random.random() < 0.3:

                switch_name, _ = random.choice(SWITCHES)

                if switch_name not in used_switches and switch_name not in spec["_absent_switches"]:
                    used_switches.add(switch_name)
                    room["switches"].add(switch_name)


def _room_line(name, room):

    parts = []

    if room["has_light"]:
        parts.append(f"Licht ({', '.join(sorted(room['lights']))})" if room["lights"] else "Licht")

    if room["heating"]:
        parts.append("Heizung")

    if room["blinds"]:
        parts.append("Rollläden")

    if room["media"]:
        parts.append("Musik")

    if room["sensors"]:
        parts.append(f"Sensoren ({', '.join(SENSORS[s] for s in sorted(room['sensors']))})")

    if room["switches"]:
        parts.append(f"Schalter ({', '.join(sorted(room['switches']))})")

    return f"- {name}: {', '.join(parts) or 'keine Geräte'}"


def finish_context(context, scenario):

    home = context.get("home")

    if home is None:
        return

    spec = dict(scenario.get("home") or {})

    absent = set(spec.get("absent") or [])

    rooms = {}

    # Rooms that must not be there, and what shares their name
    unavailable = set()

    for entity in _entities(context):

        if entity.get("absent"):
            unavailable.add(entity["home_room"])
            unavailable.add(SAME_ROOM.get(entity["home_room"]))

    for entity in _entities(context):

        if entity.get("absent") or "home_room" not in entity:
            continue

        name = entity["home_room"]

        # Two entities of one conversation may not need both names of a room,
        # or a room another entity says the home does not have.
        if SAME_ROOM.get(name) in rooms or name in unavailable:
            raise ValueError(f"{name} does not fit this home")

        room = rooms.setdefault(name, _new_room())

        if "home_light" in entity:

            room["has_light"] = True

            if entity["home_light"]:
                room["lights"].add(entity["home_light"])

        if entity.get("home_switch"):
            room["switches"].add(entity["home_switch"])

    for key, devices in (spec.get("require") or {}).items():

        name = context[key]["home_room"]

        room = rooms.setdefault(name, _new_room())

        for device in devices:

            if device == "light":
                room["has_light"] = True

            elif device in SENSORS:
                room["sensors"].add(device)

            else:
                room[device] = True

    room_absent = {
        context[key]["home_room"]: set(devices)
        for key, devices in (spec.get("room_absent") or {}).items()
    }

    spec["_absent_switches"] = {
        entity["home_absent_switch"]
        for entity in _entities(context)
        if "home_absent_switch" in entity
    }

    _draw_rooms(rooms, unavailable, spec)

    _draw_room_devices(rooms, spec, room_absent)

    # A request that names no room has to be a real question.
    missing = spec.get("min_light_rooms", 0) - sum(room["has_light"] for room in rooms.values())

    if missing > 0:

        for room in rooms.values():

            if missing and not room["has_light"]:
                room["has_light"] = True
                missing -= 1

        for name in random.sample(INDOOR_ROOMS, len(INDOOR_ROOMS)):

            if missing and name not in rooms and name not in unavailable and SAME_ROOM.get(name) not in rooms:
                rooms[name] = _new_room()
                rooms[name]["has_light"] = True
                missing -= 1

    # Requests for the whole home: the device has to exist somewhere.
    for device in spec.get("require_some") or []:

        field = "has_light" if device == "light" else device

        if any(room[field] for name, room in rooms.items() if device == "light" or name not in OUTDOOR_ROOMS):
            continue

        indoor = [name for name in rooms if name not in OUTDOOR_ROOMS]

        if not indoor:
            indoor = [next(
                name for name in random.sample(INDOOR_ROOMS, len(INDOOR_ROOMS))
                if name not in unavailable and SAME_ROOM.get(name) not in rooms
            )]
            rooms.setdefault(indoor[0], _new_room())

        rooms[random.choice(indoor)][field] = True

    names = list(rooms)

    random.shuffle(names)

    lines = [_room_line(name, rooms[name]) for name in names]

    # The whole-home devices
    vacuum = next((e for e in _entities(context) if "home_vacuum" in e), None)

    if vacuum is not None:
        robot = vacuum["home_vacuum"]

    elif "vacuum" not in absent and random.random() < HOME_DEVICES["vacuum"]:
        robot = "" if random.random() < UNNAMED_ROBOT_SHARE else random.choice(ROBOT_NAMES)[0]

    else:
        robot = None

    if robot is not None:
        lines.append(f"- Saugroboter: {robot}" if robot else "- Saugroboter")

    for label, pool, field, absent_field, kind, most in (
        ("Szenen", SCENES, "home_scene", "home_absent_scene", "scenes", 4),
        ("Automationen", AUTOMATIONS, "home_automation", None, "automations", 3),
        ("Schlösser", [name for name, _ in LOCKS], "home_lock", None, "locks", 2),
    ):

        chosen = {e[field] for e in _entities(context) if field in e}

        banned = {e[absent_field] for e in _entities(context) if absent_field in e} if absent_field else set()

        if kind not in absent:

            extra = [name for name in pool if name not in banned and name not in chosen]

            chosen |= set(random.sample(extra, random.randint(0, most)))

        if chosen:
            lines.append(f"- {label}: {', '.join(sorted(chosen))}")

    required_home = set(spec.get("require_home") or [])

    if "alarm" in required_home or ("alarm" not in absent and random.random() < HOME_DEVICES["alarm"]):
        lines.append("- Alarmanlage")

    if "garage" in required_home or ("garage" not in absent and random.random() < HOME_DEVICES["garage"]):
        lines.append("- Garagentor")

    home["inventory"] = "\n".join(lines)

    home["room_list"] = _room_list(names)
