# Schemas

## Entity Schemas

`schemas/entities/<type>.yaml` lists an entity's fields and the
[generator](generators.md) for each.

### `patient.yaml`

- `patient_id`, `first_name` (adds `gender`), `last_name`,
  `room_number` (patient rooms only), `birthday`
- computed `full_name`
- added by the linguistic resolver: `pronoun`, `object_pronoun`,
  `possessive_pronoun`, `title`, `title_last_name`

### `appointment.yaml`

- `appointment_id`, `day`
- `appointment_type`, which also sets `location` to a facility room that
  fits the type (there is no separate `location` field)

### `visitor.yaml`, `weather.yaml`

Visitor names; weather `condition` and `temperature`.

## Scenario Schemas

`schemas/scenarios/<category>/<name>.yaml` defines the context of one
template:

```yaml
name: patient_reminder

entities:
  target_patient:
    type: patient
  alternative_patient:
    type: patient
  appointment:
    type: appointment

aliases:
  patient: target_patient

constraints:
  - type: equal
    fields:
      - today
      - appointment.day
  - type: equal
    fields:
      - target_patient.last_name
      - alternative_patient.last_name
  - type: different
    fields:
      - target_patient.first_name
      - alternative_patient.first_name

robot_context:
  speaker: staff
```

- `entities`: one generated entity per key.
- `aliases`: a second name for an entity.
- `constraints`: `equal` copies the first field to the others,
  `different` rejects the draw if values repeat.
- `today`: every context has a `today` weekday. When a template's
  phrases say "today", tie the appointment to it with
  `equal: [today, appointment.day]`, as the **first** constraint, so
  later constraints that copy `appointment.day` see the final value.
- `robot_context`: see below.
- `tags` (optional): labels copied into every datapoint's metadata,
  e.g. `[offer_declined]` or `[urgency_contrast, urgent]`, to select
  groups of datapoints during evaluation.

### Robot context

What the robot knows before the conversation starts. It is rendered by
`engine/robot_context.py` and inserted by the template's opening
`{"role": "system", "content": "{{robot_context}}"}` message.

```yaml
robot_context:
  location: patient.room_number   # context path or literal text
  patient: patient                # entity whose record the robot knows
  speaker: patient                # see below
  note: "You have just entered the patient's room."
```

All keys are optional. The rendered message always starts with the day:

> Today is Tuesday. You are in room 2004. Patient: Anna Weber
> (patient_id: p123, room 2004). You are speaking with the patient. You
> have just entered the patient's room.

| speaker | sentence |
|---|---|
| `patient` | You are speaking with the patient. |
| `unidentified` | You are speaking with a patient whose identity you have not confirmed yet. |
| `visitor` | You are speaking with a visitor of the patient. |
| `relative` | You are speaking with a relative of the patient. |
| `staff` | You are speaking with a member of staff. |
| `patient_and_visitor` | You are speaking with the patient, who has a visitor with them. |

`note` may contain placeholders (`{{target_patient.title_last_name}}`,
language variables); they are resolved during rendering.

Use it whenever the robot acts for someone it has not looked up in the
conversation: a patient asking about "my appointment", the robot
entering a room on its own, a template that starts with a robot turn.
That way every `patient_id` and every room the robot uses is visible in
the conversation (see the [GroundingValidator](validation.md#groundingvalidator)).

## Language Schemas

`schemas/language/<category>/<name>.yaml` holds the phrase pools:

```yaml
variables:

  reminder_phrase:
    - "It's time for your {{appointment.appointment_type}}. Please follow me."
    - "I'm here to take you to your {{appointment.appointment_type}}."
```

For every datapoint one option per variable is chosen at random.
Options may contain placeholders, including other variables.

### Bundled options

When several parts of a conversation must match, make the options
dictionaries. One choice then fixes all parts together:

```yaml
variables:

  question:
    - text: "Can I take another dose of my pain medication now?"
      refusal: "I'm not qualified to advise on medication doses."
      offer: "I can let a nurse know you're asking about another dose."
      reason: "Patient asks whether they can take another dose of their pain medication now."
    - text: "What's this rash on my arm from?"
      refusal: "I can't tell you what's causing a rash."
      offer: "I can let a nurse know so they can look at your arm."
      reason: "Patient has a rash on their arm and would like it looked at."
```

The template uses `{{question.text}}`, `{{question.refusal}}` and so on.
Use bundles for:

- the user's request and the tool argument derived from it (`reason`,
  `note`, `search`, `room`), so arguments summarise what was said and
  never contradict it;
- a phrase and the name form it uses, e.g. `search: "{{patient.first_name}}"`
  for "Go and let Julia know ...";
- spoken and tool forms of a place (`phrase: "the Sunroom"`,
  `room: "Sunroom"`);
- a relative and their pronoun ("my mother" / "she").

### Phrase rules

- `{{appointment.appointment_type}}` is a complete noun phrase; never
  write "{{appointment.appointment_type}} appointment".
- Write `a {{...}}`; the renderer turns it into "an" where needed.
- Use `{{x.pronoun}}` only as a subject ("she has"), `{{x.possessive_pronoun}}`
  before nouns ("her appointment"), `{{x.object_pronoun}}` as an object
  ("remind her").
- Use `{{x.title_last_name}}` ("Ms. Weber") when only the last name is
  given, e.g. before asking which of several Webers is meant.
- If the robot asks for more information *before* searching, it must not
  claim to have found several matches.

## Tool Schemas

`schemas/tools/<tool>.yaml` documents the tools' inputs and outputs.
`side_effects: true|false` marks whether a call changes something
(sends, moves, records); it decides a datapoint's `behaviour` label.

| tool | inputs |
|---|---|
| `find_patient` | `name` and/or `room_number` |
| `get_patient_appointment` | `patient_id` |
| `remind_patient` | `patient_id`, `message` |
| `navigate_to` | `room` (bare room name) |
| `get_weather` | `location` |
| `notify_staff` | `reason`; `patient_id` optional |
| `alert_staff` | `room_number`, `urgency` (`low`/`medium`/`high`); `patient_id` optional |
| `log_patient_note` | `patient_id`, `note` |

`patient_id` on `notify_staff` and `alert_staff` is only set when a
patient has been identified; it is omitted otherwise, never guessed.

### Staff routing

The templates follow one rule so the model can learn the difference:

- **`alert_staff`**: someone has to come to the patient.
  - `high`: emergency (breathing trouble, chest pain, a fall, sudden
    weakness, heavy bleeding).
  - `medium`: physical help needed to move safely (out of bed, walking).
  - `low`: minor in-room help (a pillow, something out of reach) or a
    passed symptom the patient agreed to have checked.
- **`notify_staff`**: a message that staff follow up later: questions for
  the care team, clinical requests for the next round, complaints,
  preferences, scheduling, language or dietary needs, mild stable
  symptoms.

A symptom that has passed is not escalated on the robot's own
initiative: the robot offers, and calls staff only after the patient
agrees.
