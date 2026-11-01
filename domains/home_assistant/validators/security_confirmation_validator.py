# Tool -> actions that let someone in or switch protection off
NEEDS_CONFIRMATION = {
    "set_lock": {"unlock"},
    "set_alarm": {"disarm"},
    "set_garage_door": {"open"},
}


class SecurityConfirmationValidator:
    """Opening up needs a yes first: the assistant has just asked, and the
    user has answered. Locking up needs none."""

    def validate(self, datapoint):

        errors = []

        messages = datapoint.get("messages", [])

        for index, message in enumerate(messages):

            call = message.get("tool_call")

            if not call:
                continue

            actions = NEEDS_CONFIRMATION.get(call.get("name"), ())

            if (call.get("arguments") or {}).get("action") not in actions:
                continue

            asked = (
                index >= 2
                and messages[index - 1].get("role") == "user"
                and messages[index - 2].get("role") == "assistant"
                and str(messages[index - 2].get("content", "")).rstrip().endswith("?")
            )

            if not asked:
                errors.append(f"{call['name']} at {index} without asking first")

        return errors
