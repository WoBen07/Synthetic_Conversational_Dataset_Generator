"""Export the tool schemas as function definitions for the model.

Chat templates (Qwen, Llama, Mistral, ...) take the available tools as a
list of JSON-schema function definitions (``tokenizer.apply_chat_template(
messages, tools=...)``). Training with the same list the model gets at
inference teaches it to pick from the tools it is offered, instead of
memorising tool names.

Each domain has its own tools. The merger writes ``tools.json`` next to
train.jsonl as {domain: [definitions]}, and the model-specific
preprocessors attach the list of each example's domain. Generator-
internal keys (``source``, ``format``, ``side_effects``) are not
exported.

Run directly to print the definitions::

    python -m synthetic_data_generator.engine.tool_definitions [domain]
"""

import json
import sys

from synthetic_data_generator.engine.domain import resolve_domain


JSON_TYPES = {
    "string": "string",
    "enum": "string",
    "integer": "integer",
    "number": "number",
    "boolean": "boolean",
    "object": "object",
    "list": "array",
}


def _clean(text):
    return " ".join(str(text).split())


def parameter(spec):

    exported = {"type": JSON_TYPES[spec.get("type", "string")]}

    if spec.get("type") == "enum":
        exported["enum"] = list(spec["values"])

    if spec.get("description"):
        exported["description"] = _clean(spec["description"])

    return exported


def function_definition(schema):

    inputs = schema.get("input") or {}

    description = _clean(schema.get("description", ""))

    # JSON schema's anyOf is not understood by many chat templates, so
    # "at least one of" is stated in words instead.
    one_of = schema.get("requires_one_of")

    if one_of and "at least one of" not in description.lower():
        description += f" Give at least one of: {', '.join(one_of)}."

    return {
        "type": "function",
        "function": {
            "name": schema["tool"],
            "description": description,
            "parameters": {
                "type": "object",
                "properties": {
                    name: parameter(spec)
                    for name, spec in inputs.items()
                },
                "required": [
                    name for name, spec in inputs.items()
                    if spec.get("required")
                ],
            },
        },
    }


def tool_definitions(domain=None, names=None):
    """Definitions of a domain's tools (default: all of them)."""

    tools = resolve_domain(domain).tools

    return [
        function_definition(tools[name])
        for name in (names or sorted(tools))
    ]


if __name__ == "__main__":
    json.dump(tool_definitions(sys.argv[1] if len(sys.argv) > 1 else None), sys.stdout, indent=2, ensure_ascii=False)
    print()
