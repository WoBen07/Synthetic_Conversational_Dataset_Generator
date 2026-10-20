import json


PYTHON_TYPES = {
    "string": str,
    "enum": str,
    "integer": int,
    "number": (int, float),
    "boolean": bool,
    "object": dict,
    "list": list,
}


def _type_error(spec, value):
    """Return a description of why value does not fit spec, or None."""

    if value is None:
        return None if spec.get("nullable") else "is null"

    kind = spec.get("type", "string")

    expected = PYTHON_TYPES.get(kind)

    # bool is an int subclass in Python - keep the two apart
    if expected and (
        not isinstance(value, expected)
        or (kind in ("integer", "number") and isinstance(value, bool))
    ):
        return f"should be {kind}, got {type(value).__name__}"

    if kind == "enum" and value not in spec.get("values", []):
        return f"{value!r} is not one of {spec.get('values')}"

    return None


class ToolSchemaValidator:
    """Check every tool call and tool result against the domain's tool
    schemas (domains/<name>/tools/).

    Calls: the tool exists; every argument is declared; required
    arguments are present; requires_one_of is met; types and enum values
    fit. Results: every field is declared in the tool's output and has
    the declared type and enum value.
    """

    def __init__(self, tools):

        # {tool name: schema} of the domain
        self.tools = tools


    def validate(self, datapoint):

        tools = self.tools

        errors = []

        for index, message in enumerate(datapoint.get("messages", [])):

            if message.get("role") == "assistant":

                for call in self._tool_calls(message):
                    errors.extend(self._check_call(index, call, tools))

            elif message.get("role") == "tool":

                errors.extend(self._check_result(index, message, tools))

        return errors


    def _check_call(self, index, call, tools):

        name = call.get("name")

        schema = tools.get(name)

        if schema is None:
            return [f"Tool call at {index}: unknown tool {name!r}"]

        arguments = call.get("arguments") or {}

        if isinstance(arguments, str):
            arguments = json.loads(arguments)

        inputs = schema.get("input") or {}

        errors = []

        for key, value in arguments.items():

            if key not in inputs:
                errors.append(f"{name} at {index}: unknown argument {key!r}")
                continue

            problem = _type_error(inputs[key], value)

            if problem:
                errors.append(f"{name} at {index}: argument {key!r} {problem}")

        for key, spec in inputs.items():

            if spec.get("required") and key not in arguments:
                errors.append(f"{name} at {index}: missing argument {key!r}")

        one_of = schema.get("requires_one_of")

        if one_of and not any(key in arguments for key in one_of):
            errors.append(f"{name} at {index}: needs one of {one_of}")

        return errors


    def _check_result(self, index, message, tools):

        name = message.get("name")

        schema = tools.get(name)

        if schema is None:
            return [f"Tool result at {index}: unknown tool {name!r}"]

        content = message.get("content")

        if isinstance(content, str):
            try:
                content = json.loads(content)
            except json.JSONDecodeError:
                return []

        if not isinstance(content, dict):
            return []

        outputs = schema.get("output") or {}

        errors = []

        for key, value in content.items():

            if key not in outputs:
                errors.append(f"{name} result at {index}: undeclared field {key!r}")
                continue

            problem = _type_error(outputs[key], value)

            if problem:
                errors.append(f"{name} result at {index}: field {key!r} {problem}")

        return errors


    def _tool_calls(self, message):

        plural = message.get("tool_calls")

        if plural:
            return list(plural) if isinstance(plural, list) else [plural]

        singular = message.get("tool_call")

        return [singular] if singular else []
