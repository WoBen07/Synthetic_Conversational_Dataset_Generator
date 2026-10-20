import json
import re


PATIENT_ID = re.compile(r"\bp\d+\b")

WHITESPACE = re.compile(r"\s+")


def _text(content):

    if content is None:
        return ""

    if isinstance(content, str):
        return content

    return json.dumps(content, ensure_ascii=False)


def _normalize(text):

    return WHITESPACE.sub(" ", str(text)).strip().strip(".!?").lower()


class GroundingValidator:
    """Reject tool calls whose arguments the robot could not know.

    - every ``patient_id`` must have appeared earlier, in the system
      context, a user message or a tool response;
    - every ``find_patient`` argument must have been said by the user or
      stated in the system context (all of its words, so a first and
      last name given in separate turns still count);
    - ``reason`` / ``note`` must summarise the request, not repeat a
      user message word for word;
    - ``navigate_to`` targets are room names, not phrases ("the Sunroom").
    """

    def validate(self, datapoint):

        errors = []

        known_ids = set()
        heard = ""
        user_messages = []

        for index, message in enumerate(datapoint.get("messages", [])):

            role = message.get("role")
            text = _text(message.get("content"))

            for call in self._tool_calls(message):

                errors.extend(
                    self._check_call(
                        index,
                        call,
                        known_ids,
                        heard,
                        user_messages
                    )
                )

            if role in ("system", "user"):

                heard += " " + text.lower()
                known_ids.update(PATIENT_ID.findall(text))

                if role == "user":
                    user_messages.append(_normalize(text))

            elif role == "tool":

                known_ids.update(PATIENT_ID.findall(text))

        return errors


    def _check_call(self, index, call, known_ids, heard, user_messages):

        errors = []

        name = call.get("name")
        arguments = call.get("arguments") or {}

        if isinstance(arguments, str):
            arguments = json.loads(arguments)

        patient_id = arguments.get("patient_id")

        if patient_id and patient_id not in known_ids:

            errors.append(
                f"{name} at {index} uses patient_id {patient_id} "
                f"that never appeared before"
            )

        if name == "find_patient":

            for key, value in arguments.items():

                words = str(value).lower().split()

                if not all(word in heard for word in words):

                    errors.append(
                        f"find_patient at {index} searches "
                        f"{key}={value!r}, which nobody mentioned"
                    )

        for key in ("reason", "note"):

            if key in arguments and _normalize(arguments[key]) in user_messages:

                errors.append(
                    f"{name} at {index} copies a user message into {key}"
                )

        room = str(
            arguments.get("room") or arguments.get("room_number") or ""
        )

        if room.lower().startswith("the "):

            errors.append(
                f"{name} at {index} has an article in its room {room!r}"
            )

        return errors


    def _tool_calls(self, message):

        if message.get("role") != "assistant":
            return []

        plural = message.get("tool_calls")

        if plural:
            return list(plural) if isinstance(plural, list) else [plural]

        singular = message.get("tool_call")

        return [singular] if singular else []
