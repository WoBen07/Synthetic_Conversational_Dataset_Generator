"""Load the tool schemas of a domain (domains/<name>/tools/)."""

from functools import lru_cache
from pathlib import Path

import yaml


@lru_cache(maxsize=None)
def _load(tool_dir):

    tools = {}

    for path in sorted(Path(tool_dir).glob("*.yaml")):

        schema = yaml.safe_load(path.read_text(encoding="utf-8"))

        tools[schema["tool"]] = schema

    return tools


def load_tools(tool_dir):
    """Return {tool name: schema} for every <tool_dir>/*.yaml (cached)."""

    return _load(str(tool_dir))


def has_side_effects(name, tools):
    """Whether calling the tool changes something (sends, moves, records).

    ``tools`` is a {name: schema} dict as returned by load_tools. Unknown
    tools, or tools without the flag, count as having side effects -
    labelling an action as a mere lookup would be the worse mistake.
    """

    schema = tools.get(name)

    if schema is None:
        return True

    return bool(schema.get("side_effects", True))
