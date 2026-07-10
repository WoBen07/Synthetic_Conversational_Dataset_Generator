import random


ROOMS = [
    # Patient rooms
    "1001",
    "1002",
    "1003",
    "1004",
    "1005",
    "1010",
    "1012",
    "1015",

    "2001",
    "2002",
    "2003",
    "2004",
    "2005",
    "2010",
    "2012",
    "2015",

    "3001",
    "3002",
    "3003",
    "3004",
    "3010",
    "3012",
    "3015",

    # Examination rooms
    "Examination Room 1",
    "Examination Room 2",
    "Examination Room 3",
    "Consultation Room 1",
    "Consultation Room 2",
    "Consultation Room 3",

    # Treatment rooms
    "Treatment Room 1",
    "Treatment Room 2",
    "Treatment Room 3",
    "Therapy Room 1",
    "Therapy Room 2",
    "Physiotherapy Room 1",

    # Diagnostics
    "Radiology 1",
    "Radiology 2",
    "MRI Room",
    "CT Room",
    "Ultrasound Room",
    "Laboratory Room",

    # Special rooms
    "Emergency Room 1",
    "Emergency Room 2",
    "Operating Room 1",
    "Operating Room 2",
    "Recovery Room 1",
    "Waiting Room",
    "Reception"
]


def room_number():
    return random.choice(
        ROOMS
    )