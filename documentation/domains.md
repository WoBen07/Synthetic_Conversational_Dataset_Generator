# Domains

The engine knows nothing about hospitals. Everything that belongs to one
application, its templates, phrases, entities, tools, value generators,
extra validators and amounts, lives in a **domain pack** under
`domains/<name>/`. The hospital robot is the domain `hospital`; a new
application (a shop assistant, a hotel concierge, ...) is a new pack, and
the engine stays unchanged.

## Layout

```
domains/<name>/
  domain.yaml          name, description, ID pattern, robot_context wording
  config.yaml          amounts, tool_share_targets, uniqueness_caps
  templates/           <category>/<template>.json
  scenarios/           <category>/<template>.yaml
  language/            <category>/<template>.yaml
  entities/            <type>.yaml
  tools/               <tool>.yaml
  __init__.py          optional Python hooks (below)
  generators/          optional, domain-specific value generators
  validators/          optional, domain-specific validators
```

A template's three files share the same `<category>/<template>` path in
`templates/`, `scenarios/` and `language/`; that path is the template id
(e.g. `tool_use/patient_reminder`).

Engine-wide settings stay in `config/generation_config.yaml`: which
domains to generate by default (`domains`), the uniqueness optimizer
settings and the seed range.

## `domain.yaml`

```yaml
name: hospital

description: >
  Hospital service robot reminding patients of appointments, ...

# Regex for generated IDs, masked when datapoints are compared for
# duplicates (null if the domain has none)
generated_id_pattern: '\b[pa]\d+\b'

# Wording of the opening system message, see schemas.md#robot-context
robot_context:
  today: "Today is {today}."
  location: "You are in {location}."
  numeric_location: "room {value}"
  records:
    patient: "Patient: {full_name} (patient_id: {patient_id}, room {room_number})."
  speakers:
    patient: "You are speaking with the patient."
    staff: "You are speaking with a member of staff."
```

`records` and `speakers` define the vocabulary a scenario's
`robot_context` block can use: `patient: patient` renders the record of
the entity `patient` with the `patient` sentence, `speaker: staff` adds
the `staff` sentence. An unknown key is an error.

## Python hooks (optional)

A pack that needs code adds an `__init__.py`. The engine reads three
optional names from it:

| name | purpose | hospital example |
|---|---|---|
| `GENERATORS` | `{key: function}` value generators, added to the shared ones (domain keys win) | rooms, appointment types with fitting locations, weather, patient IDs |
| `create_validators()` | validator instances, run after the engine's structural checks | weather advice must match the `get_weather` result |
| `refresh_entity(entity)` | called for every entity after constraints, to keep derived fields consistent | redraw an appointment location that no longer fits its type |

Shared generators (`generators/`): `first_name`, `last_name`,
`birthday`, `weekday`. A domain without Python uses only these plus
values from its language schemas.

## Creating a domain

```bash
python -m synthetic_data_generator.engine.new_domain retail_store \
    --description "Shop assistant robot answering customer questions."
```

creates `domains/retail_store/` with a working example: a `customer`
entity, a `check_order_status` tool and one template
(`orders/order_status`), YAML and JSON only. Generate it to check the
setup, then replace the example with real templates:

```bash
python -m synthetic_data_generator.engine.orchestrator --domain retail_store
```

Everything else works per domain as well: the
[validators](validation.md) read the domain's tool schemas, the
[uniqueness optimizer](uniqueness.md) takes `--domain`, and
`test_templates.py` can be pointed at the new domain.

## Generating and merging several domains

```bash
python -m synthetic_data_generator.engine.orchestrator                          # domains from config
python -m synthetic_data_generator.engine.orchestrator --domain hospital --domain retail_store
```

Output goes to `Synthetic_Data/<domain>/<template name>/`. The merger
combines all generated domains into one train/validation split
(stratified per domain and template), and writes `tools.json` as
`{domain: [definitions]}`. Every datapoint's `metadata.domain` tells the
preprocessors which tool list to attach, so an example never sees the
tools of another domain.

Template folders directly in `Synthetic_Data/` come from the layout
before domain packs; the merger skips them with a warning.

## What belongs where

| | engine | domain pack |
|---|---|---|
| rendering, constraints, articles, pronouns | ✓ | |
| structure, placeholder, grounding, schema, language validators | ✓ | |
| metadata, deduplication, split, optimizer, tool export | ✓ | |
| names, birthdays, weekdays | ✓ (shared generators) | can override |
| entities, tools, templates, phrases, amounts | | ✓ |
| ID format, robot_context wording | | ✓ (`domain.yaml`) |
| domain knowledge (rooms, appointment types, weather advice) | | ✓ (Python hooks) |

If a new domain needs an engine change, keep it generic and configure
the domain-specific part in `domain.yaml` or a hook.
