# Engine Modules

## `engine/config.py`

Default generation settings:

- `NUM_DATASETS = 20`
- `OUTPUT_DIR = "generated_data"`
- `GENERATOR_VERSION = "0.2.0"`
- `RANDOM_SEED = 42`

## `engine/metadata.py`

Writes a `metadata.json` file with the generator version, timestamp, scenario path, template name, amount, and random seed.

## `engine/template_loader.py`

Loads a template by id from `templates/<id>.json`, where `<id>` is the
path relative to `templates/` without the extension (e.g.
`tool_use/patient_reminder`), so category subfolders resolve
transparently.

## `engine/orchestrator.py`

`get_templates()` recursively walks `templates/` (`Path.rglob("*.json")`)
and returns each template's id as its path relative to `templates/`
without the `.json` extension. That id is used to build the matching
`schemas/scenarios/<id>.yaml` and `schemas/language/<id>.yaml` paths.
`get_amount()` looks up `config/generation_config.yaml`'s
`important_templates` by the id's leaf name only, and output under
`Synthetic_Data/` is written flat, keyed by that same leaf name — so
neither the config file nor the generated dataset layout needs to know
about category subfolders.

## `engine/schemaloader.py`

Loads YAML files relative to the package root.

## `engine/entity.py`

`EntityBuilder` creates one entity from a schema by:

- calling the configured generator for each field,
- storing generator metadata when the generator returns a dictionary,
- evaluating computed fields such as `full_name`.

## `engine/constraint_resolver.py`

Supports two constraint types:

- `equal`: copies the first field value to all later fields in the list.
- `different`: raises a `ValueError` if any listed values are identical.

## `engine/entity_refresh.py`

Adds derived fields after constraint resolution. At the moment it builds `full_name` when both `first_name` and `last_name` are present.

## `engine/linguistic_resolver.py`

Adds pronoun fields for entities that contain `gender`:

- male: `he`, `him`, `his`
- female: `she`, `her`, `her`
- fallback: `they`, `them`, `their`