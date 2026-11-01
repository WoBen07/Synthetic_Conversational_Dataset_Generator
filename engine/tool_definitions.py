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

The merger also writes every definition to a JSON file of its own
(``tool_schemas/<domain>/<tool>.json``), for whatever executes the tools
at inference.

Run directly to print the definitions, or to write the JSON files to a
folder without generating anything::

    python -m synthetic_data_generator.engine.tool_definitions [domain] [output_dir]
"""

import json
import sys
from pathlib import Path

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

    for limit in ("minimum", "maximum"):

        if limit in spec:
            exported[limit] = spec[limit]

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


def write_tool_schemas(domain, output_dir):
    """Write each tool's definition to <output_dir>/<tool>.json, replacing
    the files of an earlier run, and return the written paths."""

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # A tool removed from the domain must not leave a stale schema behind.
    for stale in output_dir.glob("*.json"):
        stale.unlink()

    paths = []

    for definition in tool_definitions(domain):

        path = output_dir / f"{definition['function']['name']}.json"

        path.write_text(
            json.dumps(definition, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8"
        )

        paths.append(path)

    return paths


if __name__ == "__main__":

    domain_name = sys.argv[1] if len(sys.argv) > 1 else None

    if len(sys.argv) > 2:

        for written in write_tool_schemas(domain_name, sys.argv[2]):
            print(written)

    else:
        json.dump(tool_definitions(domain_name), sys.stdout, indent=2, ensure_ascii=False)
        print()
