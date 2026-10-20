# Overview

The `synthetic_data_generator` package creates synthetic conversational
datapoints. Each template combines three inputs:

1. A scenario YAML file that defines entities, aliases, constraints, and
   what the robot knows at the start (`robot_context`).
2. A language-schema YAML file that supplies phrase pools for user and
   assistant text.
3. A JSON template that defines the final message structure to render.

The generator builds a context of entity data, injects randomized
language variables, renders the template, validates the result, and
writes accepted, non-duplicate datapoints to disk.

## Domains

All application-specific content lives in a [domain pack](domains.md)
under `domains/<name>/`. The engine itself is domain-neutral; the
hospital robot is the domain `hospital`.

## Folder Structure

- `engine/`: orchestration, rendering, validation, loading, merging.
- `generators/`: value generators shared by all domains (names,
  birthdays, weekdays).
- `domains/<name>/`: one domain pack: templates, scenarios, language
  schemas, entities, tools, config and optional Python hooks.
- `config/`: engine-wide settings (`generation_config.yaml`) and
  publishing settings.
- `Model_Specific_Preprocessors/`: conversion into the tool-call format
  of Qwen and Gemma.
- `tests/`: the test suite (see [tests](testing.md)).

## Template Grouping

Inside a domain, `templates/`, `scenarios/` and `language/` are each
split into the same category subfolders (e.g. `conversational/`,
`safety_and_refusals/`, `tool_use/`), and a template's three files
always live at the matching path:

```
domains/hospital/templates/tool_use/patient_reminder.json
domains/hospital/scenarios/tool_use/patient_reminder.yaml
domains/hospital/language/tool_use/patient_reminder.yaml
```

The template id used everywhere downstream is the path relative to
`templates/` without `.json`, e.g. `tool_use/patient_reminder`. New
categories just need a new subfolder. Generated output goes to
`Synthetic_Data/<domain>/<template name>/`.
