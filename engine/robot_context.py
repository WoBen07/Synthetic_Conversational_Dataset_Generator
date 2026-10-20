"""Build the system message that tells the robot where it is and who
it is with.

Without it, many templates had the robot call tools with IDs that never
appeared anywhere in the conversation - the model learned to invent
them. A scenario declares what the robot knows, e.g.::

    robot_context:
      location: patient.room_number   # context path or literal text
      patient: patient                # record kind: entity whose record is known
      speaker: patient                # one of the domain's speakers
      note: "You have just entered the patient's room."

and the template starts with::

    {"role": "system", "content": "{{robot_context}}"}

The wording comes from the ``robot_context`` section of the domain's
domain.yaml, so every template of a domain shares one format::

    robot_context:
      today: "Today is {today}."
      location: "You are in {location}."
      numeric_location: "room {value}"
      records:
        patient: "Patient: {full_name} (patient_id: {patient_id}, room {room_number})."
      speakers:
        patient: "You are speaking with the patient."

The current weekday ("today") is always included so "today" in a user
message can be checked against the data.
"""


DEFAULT_WORDING = {
    "today": "Today is {today}.",
    "location": "You are in {location}.",
    "numeric_location": "{value}",
    "records": {},
    "speakers": {},
}

# Keys of a scenario's robot_context block that are not record kinds
SPEC_KEYS = {"location", "speaker", "note"}


def _resolve(context, value):

    if not isinstance(value, str):
        return value

    current = context

    for part in value.split("."):

        if not isinstance(current, dict) or part not in current:
            # Not a context path - treat it as literal text.
            return value

        current = current[part]

    return current


def build_robot_context(context, spec, wording=None):
    """Render a scenario's robot_context ``spec`` with the domain's
    ``wording`` (the robot_context section of domain.yaml)."""

    wording = {**DEFAULT_WORDING, **(wording or {})}

    sentences = [wording["today"].format(today=context["today"])]

    location = spec.get("location")

    if location:

        place = str(_resolve(context, location))

        if place.isdigit():
            place = wording["numeric_location"].format(value=place)

        sentences.append(wording["location"].format(location=place))

    # Every other key names a record kind of the domain ("patient:
    # patient" = the record of the entity "patient", in the "patient"
    # wording).
    for kind, entity_name in spec.items():

        if kind in SPEC_KEYS:
            continue

        if kind not in wording["records"]:
            raise ValueError(
                f"robot_context: unknown record kind {kind!r}; the domain "
                f"defines {sorted(wording['records'])}"
            )

        sentences.append(wording["records"][kind].format(**context[entity_name]))

    speaker = spec.get("speaker")

    if speaker:

        if speaker not in wording["speakers"]:
            raise ValueError(
                f"robot_context: unknown speaker {speaker!r}; the domain "
                f"defines {sorted(wording['speakers'])}"
            )

        sentences.append(wording["speakers"][speaker])

    note = spec.get("note")

    if note:
        # The note may contain placeholders; the renderer resolves
        # them when it inserts {{robot_context}}.
        sentences.append(note)

    return " ".join(sentences)
