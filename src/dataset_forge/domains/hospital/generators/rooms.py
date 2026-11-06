import random


# Patient rooms are where patients stay. They are kept apart from the
# facility rooms below so a patient never "lives" in the CT room or at
# the reception desk.
PATIENT_ROOMS = [
    f"{floor}{number:03d}"
    for floor in (1, 2, 3)
    for number in range(1, 16)
]


# Facility rooms are where appointments take place, grouped by what
# they are used for. generators/appointments.py maps every appointment
# type onto one or more of these groups.
FACILITY_ROOMS = {

    "consultation": [
        "Consultation Room 1",
        "Consultation Room 2",
        "Consultation Room 3",
        "Examination Room 1",
        "Examination Room 2",
        "Examination Room 3",
    ],

    "treatment": [
        "Treatment Room 1",
        "Treatment Room 2",
        "Treatment Room 3",
    ],

    "therapy": [
        "Therapy Room 1",
        "Therapy Room 2",
        "Physiotherapy Room 1",
        "Physiotherapy Room 2",
    ],

    "radiology": [
        "Radiology 1",
        "Radiology 2",
    ],

    "mri": [
        "MRI Room 1",
        "MRI Room 2",
    ],

    "ct": [
        "CT Room 1",
        "CT Room 2",
    ],

    "ultrasound": [
        "Ultrasound Room 1",
        "Ultrasound Room 2",
    ],

    "laboratory": [
        "Laboratory Room 1",
        "Laboratory Room 2",
    ],

    "cardiology": [
        "Cardiology Room 1",
        "Cardiology Room 2",
    ],

    "pulmonary": [
        "Pulmonary Function Lab",
        "Examination Room 2",
    ],

    "eye": [
        "Eye Clinic Room 1",
        "Eye Clinic Room 2",
    ],

    "hearing": [
        "Audiology Room 1",
        "Audiology Room 2",
    ],

    "dental": [
        "Dental Clinic Room 1",
        "Dental Clinic Room 2",
    ],
}


ALL_FACILITY_ROOMS = sorted({
    room
    for rooms in FACILITY_ROOMS.values()
    for room in rooms
})


def patient_room():
    return random.choice(
        PATIENT_ROOMS
    )


# Kept under its old name because entity schemas reference the
# "room_number" generator.
room_number = patient_room


def facility_room():
    return random.choice(
        ALL_FACILITY_ROOMS
    )


def rooms_for(groups):
    return [
        room
        for group in groups
        for room in FACILITY_ROOMS[group]
    ]
