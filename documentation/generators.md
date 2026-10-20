# Generators

A generator returns one random value for an entity field. Entity schemas
refer to generators by key. Each domain sees the shared generators plus
its own (`GENERATORS` in the domain package; domain keys win).

A generator that returns a dictionary sets `value` as the field and
every other key as an additional entity field.

## Shared generators (`generators/`)

| key | module | returns |
|---|---|---|
| `first_name` | `names.py` | first name, plus `gender` metadata |
| `last_name` | `names.py` | last name |
| `birthday` | `birthday.py` | date string `DD.MM.YYYY` |
| `weekday` | `days.py` | Monday ... Sunday (also used for `today`) |

First names carry their gender, which drives the pronouns and titles
added by the linguistic resolver.

## Hospital generators (`domains/hospital/generators/`)

| key | module | returns |
|---|---|---|
| `patient_id` | `ids.py` | `p001`, `p002`, ... |
| `appointment_id` | `ids.py` | `a003`, ... (shares the counter with `patient_id`) |
| `patient_room`, `room_number` | `rooms.py` | patient room |
| `facility_room` | `rooms.py` | any facility room |
| `appointment_type` | `appointments.py` | appointment type, plus a fitting `location` |
| `condition`, `temperature` | `weather.py` | weather values from one shared profile |

### `rooms.py`

Two separate pools, so patients never stay in the CT room or at the
reception:

- `PATIENT_ROOMS`: patient rooms `1001`-`1015`, `2001`-`2015`,
  `3001`-`3015`.
- `FACILITY_ROOMS`: rooms where appointments take place, grouped by use
  (`consultation`, `treatment`, `therapy`, `radiology`, `mri`, `ct`,
  `ultrasound`, `laboratory`, `cardiology`, `pulmonary`, `eye`,
  `hearing`, `dental`). Every group has at least two rooms, so templates
  that need two different locations for the same type still work.

### `appointments.py`

`TYPE_LOCATIONS` maps every appointment type to the facility room groups
it can take place in (a blood test is in a laboratory room, an eye
examination in the eye clinic). `appointment_type()` draws the type and a
fitting `location` together; `locations_for(type)` lists the allowed
rooms. The domain's `refresh_entity` hook redraws a location that no
longer fits after a constraint copied another appointment's type.

Every type already reads as a complete noun phrase ("cardiology
appointment", "blood test", "MRI scan"). Language phrases must therefore
not add another "appointment" after `{{appointment.appointment_type}}`.

### `weather.py`

`condition()` picks a weather profile and a condition from it,
`temperature()` a temperature from the same profile, so the two always
fit together.

## Adding a generator

Write a function without arguments that returns a value (or a
dictionary with `value` and extra fields), add it to the domain's
`GENERATORS`, and reference its key in an entity schema. Only values
that every domain needs belong in the shared `generators/`.
