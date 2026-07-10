# Generators

`generators/__init__.py` registers the available field generators.

Currently registered keys include:

- `first_name`
- `last_name`
- `patient_id`
- `appointment_id`
- `room_number`
- `appointment_type`
- `weekday`
- `gender`

## `generators/names.py`

Returns random first and last names. First names are stored as dictionaries with both `value` and `gender`, so the generated first name can carry gender metadata.

## `generators/ids.py`

Produces sequential IDs:

- `patient_id()` returns values such as `p001`.
- `appointment_id()` returns values such as `a002`.

Both functions share one module-level counter.

## `generators/appointments.py`

Randomly chooses an appointment type and a weekday.

## `generators/rooms.py`

Randomly chooses a room number or room label from a predefined list.

## Note

The generator registry imports `gender`, but no `generators/gender.py` file was present in the inspected folder snapshot. If that file is meant to exist, it should be added or the registry should be updated.