"""Describe a generated datapoint, for filtering, evaluation and splits.

Every datapoint written by DatasetGenerator.generate_many carries a
``metadata`` block next to ``messages``::

    "metadata": {
      "domain": "hospital",
      "template": "tool_use/patient_reminder",
      "category": "tool_use",
      "behaviour": "action",
      "tools": ["find_patient", "get_patient_appointment", "remind_patient"],
      "tags": ["clarification"],
      "wording_id": "3f9a1c0b7d2e",
      "generator_version": "0.2.0"
    }

- behaviour: "action" if a tool with side effects is called (see
  ``side_effects`` in the domain's tool schemas), "lookup_only" if only read-only
  tools are called, "no_tool" otherwise.
- tags: the scenario's optional ``tags`` list.
- wording_id: domain and template plus the language option chosen for every
  variable it used. Datapoints with the same wording_id read the same
  apart from names, rooms and days; the merger keeps them on one side of
  the train/validation split.

The model-specific preprocessors only keep ``messages``, so metadata
never reaches training.
"""

import hashlib
import json

from synthetic_data_generator.engine.config import GENERATOR_VERSION
from synthetic_data_generator.engine.tool_registry import has_side_effects


def tool_calls(message):

    plural = message.get("tool_calls")

    if plural:
        return list(plural) if isinstance(plural, list) else [plural]

    singular = message.get("tool_call")

    return [singular] if singular else []


def wording_id(template, choices, domain=""):

    key = json.dumps([domain, template, sorted(choices.items())], ensure_ascii=False)

    return hashlib.sha1(key.encode("utf-8")).hexdigest()[:12]


def behaviour(tools, schemas):
    """Label from the called ``tools`` and the domain's tool ``schemas``."""

    if any(has_side_effects(tool, schemas) for tool in tools):
        return "action"

    if tools:
        return "lookup_only"

    return "no_tool"


def build_metadata(datapoint, domain, template, choices, tags=()):

    tools = [
        call["name"]
        for message in datapoint.get("messages", [])
        for call in tool_calls(message)
    ]

    return {
        "domain": domain.name,
        "template": template,
        "category": template.split("/")[0],
        "behaviour": behaviour(tools, domain.tools),
        "tools": tools,
        "tags": list(tags),
        "wording_id": wording_id(template, choices, domain.name),
        "generator_version": GENERATOR_VERSION,
    }
