# Generation Flow

## 1. Entry Points

- **Full run:** `python -m synthetic_data_generator.engine.orchestrator`
  (from the directory that contains `synthetic_data_generator/`) lints
  the templates, plans the amounts, generates every template and merges
  the result into train/validation files. `--optimize` first runs the
  [uniqueness optimizer](uniqueness.md).
- **Single template:** `engine/runner.py` instantiates `DatasetGenerator`
  and calls `generate_many(...)` for one scenario, template and language
  schema.

## 2. Planning Amounts

`orchestrator.plan_amounts()` takes the configured amount of each
template (`config/generation_config.yaml`), lowers it to the template's
uniqueness cap if one is set, and raises templates that use rare tools
until `tool_share_targets` is met. See [engine](engine.md#engineorchestratorpy).

## 3. Scenario Building

`engine/scenario_builder.py` loads the scenario YAML and:

- sets `today` to a random weekday,
- creates each entity from `schemas/entities/<type>.yaml`,
- applies aliases,
- resolves constraints,
- refreshes derived fields (full name, a location that fits the
  appointment type) and re-checks `different` constraints,
- adds linguistic fields (pronouns, titles),
- renders the `robot_context` system text if the scenario declares one.

## 4. Language Variables

`engine/language_generator.py` picks one random option for each
variable under `variables` and records which one. Options can be
strings or bundles (dictionaries). The variables are merged into the
context, so placeholders like `{{reminder_phrase}}` or
`{{question.reason}}` can be used in templates.

## 5. Template Rendering

`engine/template_renderer.py` replaces placeholders of the form
`{{path.to.value}}`. It supports nested dictionaries, lists, recursive
placeholder resolution, whole-value placeholders (an entity inserted as
an object) and fixes `a`/`an` in front of inserted text.

## 6. Normalisation

Consecutive assistant messages are folded into one
(`engine/conversation_normalizer.py`).

## 7. Validation

`engine/validators/validator.py` runs all validators; see
[validation](validation.md). Invalid datapoints are regenerated, up to
50 attempts each.

## 8. Writing Output

Valid datapoints that are not duplicates of earlier ones are written as
`example_00000.json`, `example_00001.json`, ... in
`Synthetic_Data/<template name>/`, followed by a `metadata.json`. If 5
datapoints in a row cannot be generated, the template is stopped early
and the metadata records how many were generated.

## 9. Merging

`engine/dataset_merger.py` loads all template folders, checks strict
role alternation, splits every template into train and validation
(stratified) and writes `train.jsonl`, `validation.jsonl` and
`metadata.json`.
