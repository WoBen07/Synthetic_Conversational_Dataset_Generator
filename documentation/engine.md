# Engine Modules

## `engine/config.py`

Version and default seed used in `metadata.json`:

- `GENERATOR_VERSION = "0.2.0"`
- `RANDOM_SEED = 42`

## `engine/metadata.py`

Writes a `metadata.json` file per template with the generator version,
timestamp, scenario path, template name, requested and generated amount,
skipped datapoints, rejected duplicates (`duplicates_rejected`) and the
random seed.

## `engine/template_loader.py`

Loads a template by id from `templates/<id>.json`, where `<id>` is the
path relative to `templates/` without the extension (e.g.
`tool_use/patient_reminder`), so category subfolders resolve
transparently.

## `engine/orchestrator.py`

Entry point for a full run (`python -m synthetic_data_generator.engine.orchestrator`).

- `get_templates()` recursively walks `templates/` and returns each
  template's id (path relative to `templates/` without `.json`). The id
  is used to build the matching `schemas/scenarios/<id>.yaml` and
  `schemas/language/<id>.yaml` paths.
- `get_amount()` reads `config/generation_config.yaml`:
  `important_templates` (keyed by the leaf name) wins over
  `category_amounts` (longest matching path prefix), which wins over
  `default_amount`.
- `plan_amounts()` produces the final amount per template:
  1. the configured amount from `get_amount()`,
  2. lowered to the template's `uniqueness_caps` entry, if the optional
     [uniqueness optimizer](uniqueness.md) wrote one,
  3. raised by `apply_tool_share_targets()` until every tool in
     `tool_share_targets` reaches its minimum share of all tool calls.
     A template is never raised above `tool_share_max_scale` times its
     amount or above its uniqueness cap. The tool calls per template are
     counted statically from the template JSON. The resulting shares are
     printed, with a note for every target that could not be reached.
- Output under `Synthetic_Data/` is written flat, keyed by the
  template's leaf name.

Flags: `--optimize` runs the uniqueness optimizer (with `--write`)
before generating, `--publish` / `--dry-run-publish` push approved
datasets afterwards (see [publishing](publishing.md)).

## `engine/dataset_generator.py`

- `generate_one()` builds the context, renders the template and
  normalises the conversation.
- `generate_one_traced()` does the same and additionally returns which
  language option was chosen for each variable the template actually
  used, plus all pool sizes. The uniqueness optimizer uses it.
- `generate_many()` writes the requested number of valid datapoints:
  - an invalid datapoint is regenerated (up to 50 attempts);
  - a datapoint whose conversation equals an earlier one is rejected
    too. Generated IDs (`p…`, `a…`) are masked before comparing,
    otherwise no two datapoints would ever be equal;
  - after 5 datapoints in a row could not be generated (broken
    template or exhausted phrase pool), the template is stopped with a
    message instead of looping forever.

## `engine/scenario_builder.py`

Builds the context for one datapoint:

1. sets `today` to a random weekday;
2. creates every entity of the scenario and applies the aliases;
3. resolves the constraints;
4. refreshes derived fields (`EntityRefresher`) and checks the
   `different` constraints again, since refreshing can redraw a
   location;
5. adds linguistic fields (`LinguisticResolver`);
6. renders `robot_context` if the scenario declares one (see
   `engine/robot_context.py`).

## `engine/datapoint_metadata.py`

Builds the `metadata` block every written datapoint carries:

```json
"metadata": {
  "template": "tool_use/patient_reminder",
  "category": "tool_use",
  "behaviour": "action",
  "tools": ["find_patient", "get_patient_appointment", "navigate_to", "remind_patient"],
  "tags": ["clarification"],
  "wording_id": "e51e4baa2f07",
  "generator_version": "0.2.0"
}
```

- `behaviour`: `action` if a tool with `side_effects: true` is called,
  `lookup_only` if only read-only tools are called, `no_tool` otherwise.
  Tools without the flag count as actions.
- `tags`: the scenario's optional `tags` list.
- `wording_id`: hash of the template and the language option chosen
  for every variable it used. Same id means the same text apart from
  names, rooms and days.

Use it to filter or evaluate by behaviour (e.g. how often the model
acts in `no_tool` conversations) and for the grouped split.

## `engine/tool_registry.py`

Loads `schemas/tools/*.yaml`. `has_side_effects(name)` reads a tool's
`side_effects` flag.

## `engine/dataset_merger.py`

Loads `Synthetic_Data/`, checks role alternation and splits every
template into train/validation, grouped by `wording_id`
(`split_template`). `wording_overlap()` counts validation datapoints
whose wording also appears in train. See [generation flow](workflow.md#9-merging).

## `engine/robot_context.py`

Turns the scenario's `robot_context` block into the text of the
template's opening system message: the current day, where the robot is,
which patient record it knows (with `patient_id`), who it is talking to
and an optional note. All templates share this wording, so the model
sees a single format. Details in [schemas](schemas.md#robot-context).

## `engine/schemaloader.py`

Loads YAML files relative to the package root.

## `engine/entity.py`

`EntityBuilder` creates one entity from a schema by:

- calling the configured generator for each field,
- storing generator metadata when the generator returns a dictionary
  (`first_name` adds `gender`, `appointment_type` adds `location`),
- evaluating computed fields such as `full_name`.

## `engine/constraint_resolver.py`

Supports two constraint types:

- `equal`: copies the first field value to all later fields in the list.
  The first field can also be `today` (e.g. `[today, appointment.day]`).
- `different`: raises a `ValueError` if any listed values are identical;
  the datapoint is then regenerated.

`check_different()` re-runs only the `different` constraints.

## `engine/entity_refresh.py`

Adds derived fields after constraint resolution:

- `full_name` when both `first_name` and `last_name` are present;
- for appointments, redraws `location` if it does not fit the
  `appointment_type`. This happens when an `equal` constraint copied one
  appointment's type onto another.

## `engine/linguistic_resolver.py`

Adds fields for entities that contain `gender`:

| gender | pronoun | object_pronoun | possessive_pronoun | title |
|---|---|---|---|---|
| male | he | him | his | Mr. |
| female | she | her | her | Ms. |
| other | they | them | their | Mx. |

plus `title_last_name` ("Ms. Weber"). `title` and `title_last_name` are
listed in `PHRASING_ONLY_FIELDS`: they are only for phrasing and are left
out when a whole entity is inserted into a tool result, so
`find_patient` output keeps its format.

## `engine/language_generator.py`

Picks one random option per language variable and records the chosen
index in `choices`. Options can be plain strings or dictionaries
(bundles, see [schemas](schemas.md#bundled-options)).

## `engine/template_renderer.py`

Replaces `{{path.to.value}}` placeholders, recursively.

- A placeholder that is the whole value keeps its type (e.g. an entity
  dictionary in a tool result).
- `a` / `an` directly in front of a placeholder is adjusted to the
  inserted text ("an MRI scan", "a CT scan", "an X-ray appointment").
- Every looked-up path is recorded in `used_paths`.

## `engine/text_utils.py`

English helpers shared by the renderer and the validators:
`wants_an()` / `article_for()` (vowel sounds, acronyms such as MRI/ENT/ECG,
silent h), `article_mismatches()` and `doubled_words()`.

## `engine/conversation_normalizer.py`

Folds consecutive assistant messages into one message that carries both
the text and the tool call, so chat templates see strictly alternating
turns.

## `engine/config_optimizer.py`

Optional. Estimates how many differently worded datapoints each template
can produce and writes `uniqueness_caps` into the config. See
[Uniqueness Optimizer](uniqueness.md).
