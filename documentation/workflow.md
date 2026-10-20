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

Valid datapoints that are not duplicates of earlier ones get a
`metadata` block (template, category, behaviour, tools, tags, wording
ID; see [engine](engine.md#enginedatapoint_metadatapy)) and are written as
`example_00000.json`, `example_00001.json`, ... in
`Synthetic_Data/<template name>/`, followed by a `metadata.json`. If 5
datapoints in a row cannot be generated, the template is stopped early
and the metadata records how many were generated.

## 9. Merging

`engine/dataset_merger.py` loads all template folders, checks strict
role alternation, splits every template into train and validation and
writes `train.jsonl`, `validation.jsonl` and `metadata.json`.

The split is stratified by template and grouped by
`metadata.wording_id`: all datapoints with the same wording go to the
same side. With a plain random split, a large part of the validation set
had a training twin that differed only in names, rooms and days, so
validation scores measured memorised wording. The merger prints the
remaining overlap (0 for current data) and records it in its
`metadata.json`. Datapoints generated before metadata existed are split
one by one, with a warning.

Templates with very few distinct wordings may get no validation
datapoints at all (a warning is printed); add phrases or accept it.

Next to the split files the merger writes `tools.json`, the function
definitions of all tools.

## 10. Model-Specific Preprocessing

`Model_Specific_Preprocessors/qwen_preprossor.py` and
`Gemma_preprocessor.py` convert the merged files into the tool-call
format of each model family. They keep only `messages`, so `metadata`
never reaches training, and attach the definitions from `tools.json` to
every example as `tools` (switch off with `INCLUDE_TOOLS = False`).
The training script then renders each example with
`tokenizer.apply_chat_template(example["messages"], tools=example["tools"])`,
so the model is trained with the same tool list it gets at inference.
