# Generation Flow

## 1. Entry Point

The main example entry point is `engine/runner.py`. It instantiates `DatasetGenerator` and calls `generate_many(...)` with a scenario file, a template name, an output directory, and a language schema.

## 2. Dataset Generation

`engine/dataset_generator.py` coordinates the full pipeline.

- `generate_one(...)` builds the context and renders one datapoint.
- `generate_many(...)` repeats generation until the requested amount of valid datapoints is written.
- Invalid datapoints are regenerated automatically.
- A `metadata.json` file is written after generation completes.

## 3. Scenario Building

`engine/scenario_builder.py` loads the scenario YAML and:

- loads each entity schema from `schemas/entities/<type>.yaml`,
- creates the entity with `EntityBuilder`,
- applies aliases from the scenario,
- resolves constraints,
- refreshes derived entity fields,
- adds linguistic fields such as pronouns.

## 4. Language Variables

`engine/language_generator.py` reads the language schema and selects one random phrase for each variable defined under `variables`.

Those variables are merged into the context before template rendering, so placeholders like `{{reminder_phrase}}` or `{{user_request}}` can be used in templates.

## 5. Template Rendering

`engine/template_renderer.py` replaces placeholders of the form `{{path.to.value}}`.

It supports nested dictionaries, lists, recursive placeholder resolution, and both whole-value and mixed-string placeholders.

## 6. Validation

`engine/validators/validator.py` combines four checks:

- `StructureValidator`
- `PlaceholderValidator`
- `ToolValidator`
- `PronounValidator`

## 7. Writing Output

Valid datapoints are written as `example_00000.json`, `example_00001.json`, and so on in the configured output directory.