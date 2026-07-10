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

Loads a template by name from `templates/<name>.json`.

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