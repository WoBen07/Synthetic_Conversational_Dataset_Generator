"""Build the system message that tells the robot where it is and who
it is with.

Without it, many templates had the robot call tools with a patient_id
that never appeared anywhere in the conversation - the model learned
to invent IDs. A scenario declares what the robot knows, e.g.::

    robot_context:
      location: patient.room_number   # context path or literal text
      patient: patient                # entity whose record is known
      speaker: patient                # patient | unidentified |
                                      # visitor | relative | staff |
                                      # patient_and_visitor
      note: "You have just entered the room for a routine check."

and the template starts with::

    {"role": "system", "content": "{{robot_context}}"}

Every template gets the same wording, so the model sees a single,
learnable format. The current weekday ("today") is always included so
"today" in a user message can be checked against appointment.day.
"""


SPEAKER_SENTENCES = {
    "patient": "You are speaking with the patient.",
    "unidentified": (
        "You are speaking with a patient whose identity you have not "
        "confirmed yet."
    ),
    "visitor": "You are speaking with a visitor of the patient.",
    "relative": "You are speaking with a relative of the patient.",
    "staff": "You are speaking with a member of staff.",
    "patient_and_visitor": (
        "You are speaking with the patient, who has a visitor with them."
    ),
}


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


def _place(location):

    location = str(location)

    if location.isdigit():
        return f"room {location}"

    return location


def build_robot_context(context, spec):

    sentences = [f"Today is {context['today']}."]

    location = spec.get("location")

    if location:
        sentences.append(
            f"You are in {_place(_resolve(context, location))}."
        )

    patient_name = spec.get("patient")

    if patient_name:

        patient = context[patient_name]

        sentences.append(
            f"Patient: {patient['full_name']} "
            f"(patient_id: {patient['patient_id']}, "
            f"room {patient['room_number']})."
        )

    speaker = spec.get("speaker")

    if speaker:
        sentences.append(SPEAKER_SENTENCES[speaker])

    note = spec.get("note")

    if note:
        # The note may contain placeholders; the renderer resolves
        # them when it inserts {{robot_context}}.
        sentences.append(note)

    return " ".join(sentences)
