"""The variant home_assistant@hass: the same conversations with Home
Assistant's built-in intents as tools, see variants/hass/.

Names and slots come from https://github.com/OHF-Voice/intents (intents.yaml).
HA has no intent for some of what the domain's own tools can do, such as
pausing the vacuum, mopping or asking what a light can do. Templates built on
those are removed in variants/hass/domain.yaml; for a tool that can do both,
a draw that has no intent is redrawn (ValueError).
"""


TURN = {"on": "HassTurnOn", "off": "HassTurnOff"}

MEDIA = {
    "play": "HassMediaUnpause",
    "pause": "HassMediaPause",
    "next": "HassMediaNext",
}


def _target(arguments, domain):
    """HA's slots for a room and an optional device name."""

    slots = {"area": arguments["room"], "domain": domain}

    if arguments.get("light"):
        slots["name"] = arguments["light"]

    return slots


def _no_intent(name, arguments):
    raise ValueError(f"No Home Assistant intent for {name} {arguments}")


def _map_call(name, arguments):

    if name == "set_light_power":
        return TURN[arguments["state"]], _target(arguments, "light")

    if name == "set_all_lights_power":
        return TURN[arguments["state"]], {"domain": "light"}

    if name == "set_light_brightness":
        return "HassLightSet", {**_target(arguments, "light"), "brightness": arguments["brightness_pct"]}

    if name == "set_light_color":
        return "HassLightSet", {**_target(arguments, "light"), "color": arguments["color"]}

    if name == "get_light_state":
        return "HassGetState", _target(arguments, "light")

    if name == "set_room_temperature":
        return "HassClimateSetTemperature", {"area": arguments["room"], "temperature": arguments["temperature"]}

    if name == "get_room_temperature":
        return "HassClimateGetTemperature", {"area": arguments["room"]}

    if name == "start_cleaning":

        if arguments["mode"] != "vacuum":
            _no_intent(name, arguments)

        if arguments.get("room"):
            return "HassVacuumCleanArea", {"area": arguments["room"]}

        return "HassVacuumStart", {}

    if name == "control_vacuum":

        if arguments["action"] == "start":
            return "HassVacuumStart", {}

        if arguments["action"] == "return_to_dock":
            return "HassVacuumReturnToBase", {}

        _no_intent(name, arguments)

    if name == "set_blinds":

        if arguments.get("position_pct") is not None:
            return "HassSetPosition", {"area": arguments["room"], "device_class": "blind", "position": arguments["position_pct"]}

        if arguments["action"] == "open":
            return "HassTurnOn", {"area": arguments["room"], "device_class": "blind"}

        if arguments["action"] == "close":
            return "HassTurnOff", {"area": arguments["room"], "device_class": "blind"}

        _no_intent(name, arguments)

    if name == "set_switch_power":
        return TURN[arguments["state"]], {"name": arguments["switch"], "area": arguments["room"]}

    if name == "activate_scene":
        return "HassTurnOn", {"name": arguments["scene"], "domain": "scene"}

    if name == "run_automation":
        return "HassTurnOn", {"name": arguments["automation"], "domain": "script"}

    if name == "control_media":

        if arguments["action"] in MEDIA:
            return MEDIA[arguments["action"]], {"area": arguments["room"]}

        _no_intent(name, arguments)

    if name == "play_media":
        return "HassMediaSearchAndPlay", {"area": arguments["room"], "search_query": arguments["query"]}

    if name == "get_sensor":
        return "HassGetState", {"area": arguments["room"], "device_class": arguments["sensor"]}

    _no_intent(name, arguments)


def to_home_assistant_intents(datapoint):
    """Rewrite every tool call and the name on its result. HA has no way to
    ask what a light can do, so that step is dropped; a light that cannot do
    a colour reports an error instead, and those templates are removed."""

    datapoint["messages"] = [
        message for message in datapoint["messages"]
        if (message.get("tool_call") or {}).get("name") != "get_light_capabilities"
        and message.get("name") != "get_light_capabilities"
    ]

    current = None

    for message in datapoint["messages"]:

        call = message.get("tool_call")

        if call:
            current, call["arguments"] = _map_call(call["name"], call["arguments"])
            call["name"] = current

        elif message.get("role") == "tool":
            message["name"] = current
