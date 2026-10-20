# Generators

`generators/__init__.py` registers the available field generators in
`REGISTRY`. Entity schemas refer to them by key:

| key | module | returns |
|---|---|---|
| `first_name` | `names.py` | first name, plus `gender` metadata |
| `last_name` | `names.py` | last name |
| `patient_id` | `ids.py` | `p001`, `p002`, ... |
| `appointment_id` | `ids.py` | `a003`, ... (shares the counter with `patient_id`) |
| `patient_room` | `rooms.py` | patient room |
| `room_number` | `rooms.py` | alias of `patient_room` |
| `facility_room` | `rooms.py` | any facility room |
| `appointment_type` | `appointments.py` | appointment type, plus a fitting `location` |
| `weekday` | `appointments.py` | Monday ... Sunday |
| `condition`, `temperature` | `weather.py` | weather values from one shared profile |
| `birthday` | `birthday.py` | date string `DD.MM.YYYY` |

A generator that returns a dictionary sets `value` as the field and
every other key as an additional entity field.

## `generators/rooms.py`

Two separate pools, so patients never stay in the CT room or at the
reception:

- `PATIENT_ROOMS`: patient rooms `1001`-`1015`, `2001`-`2015`,
  `3001`-`3015`.
- `FACILITY_ROOMS`: rooms where appointments take place, grouped by use
  (`consultation`, `treatment`, `therapy`, `radiology`, `mri`, `ct`,
  `ultrasound`, `laboratory`, `cardiology`, `pulmonary`, `eye`,
  `hearing`, `dental`). Every group has at least two rooms, so templates
  that need two different locations for the same type still work.

`rooms_for(groups)` returns the rooms of the given groups.

## `generators/appointments.py`

`TYPE_LOCATIONS` maps every appointment type to the facility room
groups it can take place in (a blood test is in a laboratory room, an
eye examination in the eye clinic). `appointment_type()` draws the type
and a fitting `location` together; `locations_for(type)` lists the
allowed rooms.

Every type already reads as a complete noun phrase ("cardiology
appointment", "blood test", "MRI scan"). Language phrases must
therefore not add another "appointment" after
`{{appointment.appointment_type}}`.

## `generators/names.py`

Random first and last names. First names carry their gender, which
drives the pronouns and titles added by the linguistic resolver.

## `generators/ids.py`

Sequential IDs from one module-level counter.

## `generators/weather.py`

`condition()` picks a weather profile and a condition from it,
`temperature()` a temperature from the same profile, so the two always
fit together.
