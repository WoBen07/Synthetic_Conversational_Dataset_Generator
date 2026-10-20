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

## `engine/domain.py`

Loads [domain packs](domains.md). `load_domain(name)` returns a cached
`Domain` with the pack's paths (`template_path()`, `scenario_path()`,
`language_path()`, `entity_path()`, `paths(template_id)` for
`generate_one`), its `templates()`, `tools`, `generators` (shared plus
the domain's), `robot_context` wording, `generated_id_pattern`, its
`config.yaml` (`load_config()`) and its Python hooks
(`create_validators()`, `refresh_entity()`). `list_domains()`,
`configured_domains()` (from `config/generation_config.yaml`) and
`default_domain()` (the first configured one) select domains;
`resolve_domain()` accepts a `Domain`, a name or `None`.

## `engine/new_domain.py`

Creates a new domain pack with one working example template:
`python -m synthetic_data_generator.engine.new_domain <name>`.

## `engine/template_loader.py`

Loads a template by id from the domain's `templates/<id>.json`, where
`<id>` is the path relative to `templates/` without the extension (e.g.
`tool_use/patient_reminder`).

## `engine/orchestrator.py`

Entry point for a full run (`python -m synthetic_data_generator.engine.orchestrator`).
Generates every template of the selected domains (`--domain`, repeatable;
default: `domains` in `config/generation_config.yaml`).

- `get_templates(domain)` returns a domain's template ids.
- `get_amount()` reads the domain's `config.yaml`:
  `important_templates` (keyed by the leaf name) wins over
  `category_amounts` (longest matching path prefix), which wins over
  `default_amount`.
- `plan_amounts(domain)` produces the final amount per template:
  1. the configured amount from `get_amount()`,
  2. lowered to the template's `uniqueness_caps` entry, if the optional
     [uniqueness optimizer](uniqueness.md) wrote one,
  3. raised by `apply_tool_share_targets()` until every tool in
     `tool_share_targets` reaches its minimum share of all tool calls.
     A template is never raised above `tool_share_max_scale` times its
     amount or above its uniqueness cap. The tool calls per template are
     counted statically from the template JSON. The resulting shares are
     printed, with a note for every target that could not be reached.
- Output goes to `Synthetic_Data/<domain>/<template leaf name>/`.

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
2. creates every entity of the scenario from the domain's
   `entities/<type>.yaml`, with the domain's generators, and applies the
   aliases;
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

`load_tools(tool_dir)` loads a domain's tool schemas (cached);
`has_side_effects(name, tools)` reads a tool's `side_effects` flag.

## `engine/tool_definitions.py`

Exports a domain's tool schemas as JSON-schema function definitions
(`{"type": "function", "function": {name, description, parameters}}`),
the format chat templates take via `apply_chat_template(..., tools=...)`.
`requires_one_of` is stated in the description, since many chat
templates do not understand `anyOf`. Generator-internal keys are
dropped.

## `engine/dataset_merger.py`

Loads `Synthetic_Data/<domain>/<template>/` (all domains, or the ones
passed to `main(domains=...)`; folders of the old flat layout are
skipped), checks role alternation and splits every template into
train/validation, grouped by `wording_id` (`split_template`). Writes
`tools.json` as `{domain: [definitions]}` next to `train.jsonl`. `wording_overlap()` counts validation datapoints
whose wording also appears in train. See [generation flow](workflow.md#9-merging).

## `engine/robot_context.py`

Turns the scenario's `robot_context` block into the text of the
template's opening system message: the current day, where the robot is,
which records it knows (in the hospital: the patient with
`patient_id`), who it is talking to and an optional note. The wording
comes from the domain's `domain.yaml`, so all templates of a domain
share one format. Details in [schemas](schemas.md#robot-context).

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

Adds derived fields after constraint resolution: `full_name` when both
`first_name` and `last_name` are present, then the domain's
`refresh_entity` hook (the hospital domain redraws an appointment
`location` that no longer fits the `appointment_type`, which happens
when an `equal` constraint copied one appointment's type onto another).

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
