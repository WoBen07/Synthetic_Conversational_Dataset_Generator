# Domains

The engine knows nothing about hospitals. Everything that belongs to one
application, its templates, phrases, entities, tools, value generators,
extra validators and amounts, lives in a **domain pack** under
`domains/<name>/`. The hospital robot is the domain `hospital`, the German
smart-home assistant is the domain `home_assistant`; a new application (a
shop assistant, a hotel concierge, ...) is a new pack, and the engine stays
unchanged.

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
  variants/<variant>/  optional overlays, see "Variants" below
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
the `staff` sentence. An unknown key is an error. `today: null` leaves the
weekday out, for a domain in which nothing depends on it.

`language` (default `en`) names the language of the conversations. What
the engine itself writes or checks follows it, see
[languages](#languages).

## Python hooks (optional)

A pack that needs code adds an `__init__.py`. The engine reads three
optional names from it:

| name | purpose | hospital example |
|---|---|---|
| `GENERATORS` | `{key: function}` value generators, added to the shared ones (domain keys win) | rooms, appointment types with fitting locations, weather, patient IDs |
| `create_validators(domain)` | validator instances, run after the engine's structural checks; `domain` tells them the variant and language | weather advice must match the `get_weather` result |
| `refresh_entity(entity)` | called for every entity after constraints, to keep derived fields consistent | redraw an appointment location that no longer fits its type |
| `finish_context(context, scenario)` | called once all entities exist, before the system message is built, for what depends on several of them | home_assistant: build a home that contains the conversation's devices |
| `postprocess(datapoint, domain)` | the rendered conversation, before validation; may raise `ValueError` to redraw | home_assistant: drop empty arguments, speech-recognizer text, map tools to HA intents |

Shared generators (`generators/`): `first_name`, `last_name`,
`birthday`, `weekday`. A domain without Python uses only these plus
values from its language schemas.

## Creating a domain

```bash
sdg new-domain retail_store \
    --description "Shop assistant robot answering customer questions."
```

creates `domains/retail_store/` with a working example: a `customer`
entity, a `check_order_status` tool and one template
(`orders/order_status`), YAML and JSON only. Generate it to check the
setup, then replace the example with real templates:

```bash
sdg generate --domain retail_store
```

Everything else works per domain as well: the
[validators](validation.md) read the domain's tool schemas, the
[uniqueness optimizer](uniqueness.md) takes `--domain`, and
`test_templates.py` can be pointed at the new domain.

## Variants

A variant is the same application in another language and/or with other
tool schemas. It lives in `domains/<name>/variants/<variant>/`, in the
layout of the pack, holds only what differs, and is addressed as
`<name>@<variant>` wherever a domain name is accepted:

```bash
sdg generate --domain home_assistant@en
sdg generate --domain home_assistant --domain home_assistant@en
sdg optimize --domain home_assistant@en
python -m synthetic_data_generator.engine.tool_definitions home_assistant@en
```

The `domain.yaml` of a variant is required, may be empty, and goes on top
of the pack's.

| what | in the variant | effect |
|---|---|---|
| `domain.yaml` | patch | merged over the pack's; also `remove_tools`, `remove_templates` (ids or path prefixes) |
| `config.yaml` | patch | merged over the pack's, except `uniqueness_caps`, which are measured per variant and written here |
| `tools/<tool>.yaml` | patch, needs `tool:` | merged over the pack's tool of that name; a new name adds a tool |
| `templates/`, `scenarios/`, `entities/` | whole files | replace the pack's file or add a new one; everything else is inherited |
| `language/` | whole files | as above; a translated variant inherits nothing (below) |

A tool patch merges dictionaries key by key and replaces everything else,
and `null` removes an argument. Python hooks are shared: put the generators
a variant needs into the pack's `GENERATORS` and select them with an
overriding entity file.

Each variant is a domain of its own to the rest of the pipeline. Its name is
`metadata.domain` of its datapoints, its data goes to
`Synthetic_Data/<name>@<variant>/`, and its tools are a separate entry in
`tools.json` and in `tool_schemas/`, so one merged dataset can hold several
languages and schemas and every example still gets exactly its own tools.

### Another language

```yaml
# domains/home_assistant/variants/en/domain.yaml
language: en
robot_context:
  speakers:
    resident: "You are the voice assistant of this home ..."
```

```yaml
# domains/home_assistant/variants/en/tools/set_light_power.yaml
tool: set_light_power
description: Switches a light in a room on or off.
input:
  room:
    description: Room name without preposition or article.
```

plus `language/<category>/<template>.yaml` per template. If phrases rely on
language-specific entity fields (such as the German cases of a room), add
overriding `entities/` that use a generator for the new language.

A variant whose language differs from the pack's never falls back to the
pack's phrases: a template without a language file is skipped. The
orchestrator lists what is left to translate before generating (templates
without phrases, literal text in inherited templates, inherited tool
descriptions and `robot_context` sentences); `Domain.translation_gaps()`
returns the same list. A domain validator that looks for words of one
language has to be adapted through `create_validators(domain)`.

### Other tool schemas

```yaml
# domains/home_assistant/variants/hass/domain.yaml
remove_tools: [set_light_power]
```

Add or patch tools in `tools/`, and override the templates that call a
changed tool (`templates/<category>/<template>.json`) with their new names
and arguments; phrases and scenarios stay inherited. Datapoints are validated
against the variant's schemas, so a template still using the old schema
produces no data. Use `remove_templates` for behaviour the variant does not
have. A domain validator that names tools needs the new names as well.

### The home_assistant domain

German, for any home. Every conversation draws its own home, listed in the
system message, and everything the assistant does has to fit that list:

```
Du bist der Sprachassistent dieses Zuhauses ... Du sprichst mit einer Person, die hier wohnt.
Geräte im Zuhause:
- Wohnzimmer: Licht (Stehlampe, Lichterkette), Heizung, Rollläden
- Küche: Licht, Heizung, Schalter (Kaffeemaschine)
- Saugroboter: Fridolin
- Szenen: Filmabend
```

`domains/home_assistant/home.py` builds the list after the entities are drawn: the
conversation's own devices are always in it, the rest is random. A scenario asks
for more in a `home` block, see the module's docstring. Rooms, device names,
scenes and the robot's name vary, and a robot may have no name at all.

Tool arguments name what is on the list (`source: known`). `light` is optional:
"das Licht im Wohnzimmer" has none, "die Stehlampe" has one, and its room comes
from the list when the user does not say it.

About a third of the conversations have user text as a speech recognizer writes it
(lowercase, no punctuation, sometimes a filler word), see `postprocess.py`.

| category | teaches |
|---|---|
| `light`, `heating`, `vacuum`, `blinds`, `switches`, `scenes`, `media`, `sensors` | the devices, including reading their state |
| `security` | opening a lock, the garage or disarming the alarm asks first; a no calls nothing |
| `known_room` | the system message says where the user is, so no question back |
| `implied` | "Mir ist kalt" |
| `multi` | several tool calls for one request |
| `followup` | "Und im Büro auch", "Noch heller", a correction, a thank-you |
| `clarification` | a question back only when it is really open; a home of one room has none |
| `impossible` | values outside the range: no call, the limit is named |
| `not_in_home`, `no_tool` | what the list does not have, and what no tool can do |
| `error_handling` | a tool reports a failure; the assistant says so |

The variant `home_assistant@hass` has the same conversations with Home Assistant's
built-in intents as tools (`hass_mapping.py`, names from
[intents.yaml](https://github.com/OHF-Voice/intents/blob/main/intents.yaml)).
HA has no intent for some things, so 25 templates are left out (security, relative
adjustments, the heating mode, capability checks with a negative answer) and a draw
such as mopping is redrawn. Tool results keep this domain's format, not HA's own
response format.

### Languages

`engine/languages.py` holds what the engine has to know about a language;
a new language is one entry there, an unknown code is an error.

| rule | used for |
|---|---|
| `weekdays` | `today` and the `weekday` generator |
| `pronouns` | `pronoun`, `object_pronoun`, `possessive_pronoun`, `title` of entities with a `gender` |
| `wording` | default `today` and `location` sentences of the system message |
| `name_prefixes` | words a `format: name` tool argument must not start with |
| `allowed_doubles` | words the doubled-word check accepts |
| `decimal_separator` | how a number argument is written in text (21.5 is grounded by "21,5") |
| `english_articles` | whether the renderer's `a`/`an` fix and its validator run |

## Generating and merging several domains

```bash
sdg generate                          # domains from config
sdg generate --domain hospital --domain retail_store
```

Output goes to `Synthetic_Data/<domain>/<template name>/`, replacing what a
template generated before; the output of templates the domain no longer has is
removed, so old conversations never reach the merge. The merger
combines all generated domains into one train/validation split
(stratified per domain and template), and writes `tools.json` as
`{domain: [definitions]}`. Every datapoint's `metadata.domain` tells the
preprocessors which tool list to attach, so an example never sees the
tools of another domain. The same definitions are also written as one JSON
file per tool, `tool_schemas/<domain>/<tool>.json`.

With the domains from the config, the merged dataset goes to the merger's
`OUTPUT_FOLDER`. Any other selection gets a folder of its own named after
the domains (`Datasets/home_assistant/`, `Datasets/home_assistant+hospital/`),
so generating one domain never overwrites the merged dataset of the others.

Template folders directly in `Synthetic_Data/` come from the layout
before domain packs; the merger skips them with a warning.

## What belongs where

| | engine | domain pack |
|---|---|---|
| rendering, constraints, language rules (articles, pronouns, weekdays) | ✓ | |
| structure, placeholder, grounding, schema, language validators | ✓ | |
| metadata, deduplication, split, optimizer, tool export | ✓ | |
| names, birthdays, weekdays | ✓ (shared generators) | can override |
| another language or tool schema of an application | | ✓ (`variants/`) |
| entities, tools, templates, phrases, amounts | | ✓ |
| ID format, robot_context wording | | ✓ (`domain.yaml`) |
| domain knowledge (rooms, appointment types, weather advice) | | ✓ (Python hooks) |

If a new domain needs an engine change, keep it generic and configure
the domain-specific part in `domain.yaml` or a hook.
