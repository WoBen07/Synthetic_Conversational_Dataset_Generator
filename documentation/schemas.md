# Schemas

## Entity Schemas

### `schemas/entities/patient.yaml`

Defines a patient with these fields:

- `patient_id`
- `first_name`
- `last_name`
- `room_number`
- computed `full_name = "{{first_name}} {{last_name}}"`

### `schemas/entities/appointment.yaml`

Defines an appointment with these fields:

- `appointment_id`
- `day`
- `appointment_type`
- `location`

## Scenario Schemas

### `schemas/scenarios/patient_reminder.yaml`

Defines a reminder scenario with:

- `target_patient`
- `alternative_patient`
- `appointment`
- alias `patient -> target_patient`
- constraints that keep the two patients distinct in key fields while sharing the same last name.

### `schemas/scenarios/clarification_room.yaml`

Defines a clarification scenario with one `patient` entity and the language schema `clarification_by_room`.

### `schemas/scenarios/patient_lookup.yaml`

Defines the `ambiguous_patient_lookup` scenario with two patient entities, matching last names, and distinct patient IDs and room numbers.

## Language Schemas

### `schemas/language/patient_reminder.yaml`

Contains phrase pools for:

- `remind_user_phrase`
- `multiple_patient_confirmation_request`
- `patient_confirmation`
- `reminder_phrase`
- `confirmation_phrase_task_fullfillment`

### `schemas/language/clarification_by_room.yaml`

Contains phrase pools for:

- `user_request`
- `clarification_request`
- `user_clarification`
- `acknowledgement`

## Tool Schemas

### `schemas/tools/find_patient.yaml`

Describes a `find_patient` tool with an output schema that expects a `matches` list with at least two `patient` items.