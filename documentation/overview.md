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

## Installation

```bash
pip install -e .            # from a clone of the repository
pip install -e ".[hub]"     # plus publishing to the Hugging Face Hub
```

This installs the `sdg` command:

| Command | Does |
|---|---|
| `sdg generate [--domain NAME ...] [--optimize]` | lint, generate and merge ([workflow](workflow.md)) |
| `sdg lint` | check the templates of every domain |
| `sdg optimize` | the [uniqueness optimizer](uniqueness.md) |
| `sdg new-domain NAME` | create a domain pack in the project's `domains/` |
| `sdg domains` | list the domains and where each one comes from |
| `sdg gui` | the local [web GUI](gui.md) |
| `sdg publish` | [push an approved dataset](publishing.md) to the Hub |

`sdg <command> --help` shows the options of each command. The modules
can still be run directly (`python -m synthetic_data_generator.engine.orchestrator`).

## Project Folder

The installed package is never written to. Everything you create lives in
a project folder:

```
my-project/
  domains/<name>/              your own domain packs (optional)
  config/generation_config.yaml   overrides the packaged default (optional)
  config/publish_config.yaml      Hub target (only needed for sdg publish)
  Synthetic_Data/              generated datapoints, one folder per template
  Datasets/                    merged train/validation files
```

The project folder is, in this order: `sdg --project DIR`, the
environment variable `SDG_PROJECT_DIR`, the repository root when running
from a clone, or the current directory. `engine/paths.py` holds this
logic.

Domains are looked up in the project's `domains/` first, then among the
packs built into the package (`hospital`, `home_assistant`). A project
pack with the same name as a built-in one replaces it.

## Repository Layout

- `src/synthetic_data_generator/`: the package.
  - `engine/`: orchestration, rendering, validation, loading, merging.
  - `generators/`: value generators shared by all domains (names,
    birthdays, weekdays).
  - `domains/<name>/`: the built-in domain packs: templates, scenarios,
    language schemas, entities, tools, config and optional Python hooks.
  - `config/generation_config.yaml`: default engine-wide settings.
  - `cli.py`: the `sdg` command.
- `config/publish_config.yaml`: publishing settings of this repository.
- `scripts/`: conversion into the tool-call format of Qwen and Gemma.
- `tests/`: the test suite (see [tests](testing.md)).
- `documentation/`: these docs.

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
