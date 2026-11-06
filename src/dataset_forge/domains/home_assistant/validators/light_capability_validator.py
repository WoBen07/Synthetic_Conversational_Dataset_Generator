# Tool -> capability get_light_capabilities must have confirmed for that
# light before the tool may be called.
REQUIRED_CAPABILITY = {
    "set_light_color": "supports_color",
    "adjust_light_color_temperature": "supports_color_temperature",
}


class LightCapabilityValidator:
    """Colours and colour temperature need a check first.

    Not every light is a colour light, so the assistant has to look up what
    a light can do before changing either, and must not call the tool when
    the light cannot do it.
    """

    def validate(self, datapoint):

        errors = []

        # {(room, light): capabilities from get_light_capabilities}
        known = {}

        pending = None

        for index, message in enumerate(datapoint.get("messages", [])):

            if message.get("role") == "tool":

                if message.get("name") == "get_light_capabilities" and pending:
                    known[pending] = message.get("content") or {}

                pending = None

                continue

            call = message.get("tool_call")

            if not call:
                continue

            arguments = call.get("arguments") or {}

            target = (arguments.get("room"), arguments.get("light"))

            if call.get("name") == "get_light_capabilities":
                pending = target

            capability = REQUIRED_CAPABILITY.get(call.get("name"))

            if capability and not known.get(target, {}).get(capability):

                errors.append(
                    f"{call['name']} at {index} without {capability} "
                    f"confirmed for {target}"
                )

        return errors
