# Overview

The `synthetic_data_generator` package creates synthetic conversational datapoints from three inputs:

1. A scenario YAML file that defines entities, aliases, and constraints.
2. A language-schema YAML file that supplies phrase pools for user and assistant text.
3. A JSON template that defines the final message structure to render.

The generator builds a context of entity data, injects randomized language variables, renders the template, validates the result, and writes accepted datapoints to disk.

## Folder Structure

- `engine/`: orchestration, rendering, validation, and loading logic.
- `generators/`: random value generators for entity fields.
- `schemas/`: YAML definitions for entities, scenarios, tools, and language variables.
- `templates/`: JSON templates for complete datapoints.
- `scripts/`: currently empty.

## Template Grouping

`templates/`, `schemas/scenarios/`, and `schemas/language/` are each split into
the same set of category subfolders (e.g. `conversational/`,
`safety_and_refusals/`, `tool_use/`), and a template's three files always
live at the matching path within each, e.g.:

```
templates/tool_use/patient_reminder.json
schemas/scenarios/tool_use/patient_reminder.yaml
schemas/language/tool_use/patient_reminder.yaml
```

`engine/orchestrator.py` discovers templates by recursively walking
`templates/` (`Path.rglob("*.json")`), so new categories just need a new
subfolder — nothing else to register. The template's id used everywhere
downstream is its path relative to `templates/` without the `.json`
extension, e.g. `tool_use/patient_reminder`. Generated output under
`Synthetic_Data/` stays flat and keyed by the template's own name only
(the category isn't part of the output path), so the merger step is
unaffected by this grouping.