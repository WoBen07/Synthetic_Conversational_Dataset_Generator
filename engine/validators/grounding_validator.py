import json
import re


WHITESPACE = re.compile(r"\s+")

ARTICLE = re.compile(r"^(the|a|an)\s", re.IGNORECASE)


def _text(content):

    if content is None:
        return ""

    if isinstance(content, str):
        return content

    return json.dumps(content, ensure_ascii=False)


def _normalize(text):

    return WHITESPACE.sub(" ", str(text)).strip().strip(".!?").lower()


def _occurs(value, text):
    """value appears in text as a whole token (IDs, room numbers)."""

    return re.search(
        rf"(?<![\w-]){re.escape(value)}(?![\w-])",
        text
    ) is not None


class GroundingValidator:
    """Reject tool arguments the robot could not know.

    The rules come from the domain's tool schemas (domains/<name>/tools/), so the
    validator works for any domain. Per argument:

    - ``source: known`` - the exact value (an ID, a room number) must
      have appeared before, in the system context, a user message or a
      tool result;
    - ``source: mentioned`` - every word of the value must have appeared
      before in those places (a first and last name given in separate
      turns count, and so does a room taken from an earlier result);
    - ``source: own_words`` - the value summarises the request and must
      not repeat a user message word for word;
    - ``format: name`` - a bare name, no leading article ("Sunroom",
      not "the Sunroom").

    The robot's own messages never count as a source: it cannot ground
    an argument in something it made up itself.
    """

    def __init__(self, tools):

        # {tool name: schema} of the domain
        self.tools = tools


    def validate(self, datapoint):

        tools = self.tools

        errors = []

        known_text = ""
        user_messages = []

        for index, message in enumerate(datapoint.get("messages", [])):

            role = message.get("role")

            for call in self._tool_calls(message):

                errors.extend(
                    self._check_call(index, call, tools, known_text, user_messages)
                )

            if role in ("system", "user", "tool"):

                known_text += "\n" + _text(message.get("content"))

                if role == "user":
                    user_messages.append(_normalize(_text(message.get("content"))))

        return errors


    def _check_call(self, index, call, tools, known_text, user_messages):

        name = call.get("name")

        schema = tools.get(name) or {}

        inputs = schema.get("input") or {}

        arguments = call.get("arguments") or {}

        if isinstance(arguments, str):
            arguments = json.loads(arguments)

        errors = []

        for key, value in arguments.items():

            spec = inputs.get(key) or {}

            source = spec.get("source")

            value = str(value)

            if source == "known" and not _occurs(value, known_text):

                errors.append(
                    f"{name} at {index} uses {key}={value!r}, "
                    f"which never appeared before"
                )

            elif source == "mentioned" and not all(
                word in known_text.lower() for word in value.lower().split()
            ):

                errors.append(
                    f"{name} at {index} uses {key}={value!r}, "
                    f"which nobody mentioned"
                )

            elif source == "own_words" and _normalize(value) in user_messages:

                errors.append(
                    f"{name} at {index} copies a user message into {key}"
                )

            if spec.get("format") == "name" and ARTICLE.match(value):

                errors.append(
                    f"{name} at {index} has an article in {key}={value!r}"
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
