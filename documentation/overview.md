# Overview

The `dataset_forge` package creates synthetic conversational
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
pip install python-dataset-forge          # once released
pip install -e .                          # from a clone of the repository
pip install -e ".[hub]"                   # plus publishing to the Hugging Face Hub
```

The distribution is `python-dataset-forge`, the import name
`dataset_forge`. This installs the `dforge` command (long form:
`dataset-forge`):

| Command | Does |
|---|---|
| `dforge init [DIR] [--domain NAME]` | set up a [project folder](#project-folder) |
| `dforge generate [--domain NAME ...] [--seed N] [--optimize]` | lint, generate and merge ([workflow](workflow.md)) |
| `dforge lint` | check the templates of every domain |
| `dforge optimize` | the [uniqueness optimizer](uniqueness.md) |
| `dforge new-domain NAME [--package]` | create a domain pack in the project's `domains/`, or a [pip-installable one](domains.md#installable-domain-packs) |
| `dforge domains` | list the domains and where each one comes from |
| `dforge gui` | the local [web GUI](gui.md) |
| `dforge publish` | [push an approved dataset](publishing.md) to the Hub |

`dforge <command> --help` shows the options of each command. The modules
can still be run directly (`python -m dataset_forge.engine.orchestrator`).
To generate from Python instead, see the [Python API](api.md).

## Project Folder

The installed package is never written to. Everything you create lives in
a project folder, which `dforge init my-project` sets up:

```
my-project/
  domains/<name>/              your own domain packs (optional)
  config/generation_config.yaml   your settings (optional)
  config/publish_config.yaml      Hub target (only needed for dforge publish)
  Synthetic_Data/              generated datapoints, one folder per template
  Datasets/                    merged train/validation files
```

The project folder is, in this order: `dforge --project DIR`, the
environment variable `DFORGE_PROJECT_DIR`, the repository root when running
from a clone, or the current directory. `engine/paths.py` holds this
logic.

`config/generation_config.yaml` is merged key by key over the defaults
that ship with the package, so it only needs the keys you change:

| key | default | meaning |
|---|---|---|
| `domains` | `[]` (all) | domains generated when no `--domain` is given |
| `merged_dataset` | `dataset` | folder below `Datasets/` for the merged files of those domains |
| `seed` | empty (fresh per run) | run seed, see [reproducibility](workflow.md#reproducibility) |
| `uniqueness_optimizer` | | settings of the [optimizer](uniqueness.md) |

Domains are looked up in the project's `domains/` first, then among
[installed domain packs](domains.md#installable-domain-packs), then among
the packs built into the package (`hospital`, `home_assistant`). The
first one found replaces the others of the same name. `dforge domains`
shows where each domain comes from.

## Repository Layout

- `src/dataset_forge/`: the package.
  - `engine/`: orchestration, rendering, validation, loading, merging.
  - `generators/`: value generators shared by all domains (names,
    birthdays, weekdays).
  - `domains/<name>/`: the built-in domain packs: templates, scenarios,
    language schemas, entities, tools, config and optional Python hooks.
  - `config/generation_config.yaml`: default engine-wide settings.
  - `cli.py`: the `dforge` command; `api.py`: the [Python API](api.md).
- `config/generation_config.yaml`: this repository's own settings (its
  project config).
- `config/publish_config.example.yaml`: template for the git-ignored
  `config/publish_config.yaml`.
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
