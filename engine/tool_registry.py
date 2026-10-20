"""Load the tool schemas in schemas/tools/."""

from functools import lru_cache
from pathlib import Path

import yaml


TOOL_DIR = Path(__file__).resolve().parents[1] / "schemas" / "tools"


@lru_cache(maxsize=None)
def load_tools():
    """Return {tool name: schema} for every schemas/tools/*.yaml."""

    tools = {}

    for path in sorted(TOOL_DIR.glob("*.yaml")):

        schema = yaml.safe_load(path.read_text(encoding="utf-8"))

        tools[schema["tool"]] = schema

    return tools


def has_side_effects(name):
    """Whether calling the tool changes something (sends, moves, records).

    Unknown tools, or tools without the flag, count as having side
    effects - labelling an action as a mere lookup would be the worse
    mistake.
    """

    schema = load_tools().get(name)

    if schema is None:
        return True

    return bool(schema.get("side_effects", True))
