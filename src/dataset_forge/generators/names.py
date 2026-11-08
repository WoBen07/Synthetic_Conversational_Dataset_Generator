import random


FIRST_NAMES = [
    # Female names
    {
        "value": "Emma",
        "gender": "female"
    },
    {
        "value": "Vanessa",
        "gender": "female"
    },
    {
        "value": "Anna",
        "gender": "female"
    },
    {
        "value": "Julia",
        "gender": "female"
    },
    {
        "value": "Maria",
        "gender": "female"
    },
    {
        "value": "Laura",
        "gender": "female"
    },
    {
        "value": "Sophia",
        "gender": "female"
    },
    {
        "value": "Hannah",
        "gender": "female"
    },
    {
        "value": "Lisa",
        "gender": "female"
    },
    {
        "value": "Sarah",
        "gender": "female"
    },
    {
        "value": "Katharina",
        "gender": "female"
    },
    {
        "value": "Elisabeth",
        "gender": "female"
    },
    {
        "value": "Monika",
        "gender": "female"
    },
    {
        "value": "Claudia",
        "gender": "female"
    },
    {
        "value": "Petra",
        "gender": "female"
    },
    {
        "value": "Helga",
        "gender": "female"
    },
    {
        "value": "Brigitte",
        "gender": "female"
    },


    # Male names
    {
        "value": "Michael",
        "gender": "male"
    },
    {
        "value": "Peter",
        "gender": "male"
    },
    {
        "value": "Thomas",
        "gender": "male"
    },
    {
        "value": "Martin",
        "gender": "male"
    },
    {
        "value": "Andreas",
        "gender": "male"
    },
    {
        "value": "Stefan",
        "gender": "male"
    },
    {
        "value": "Christian",
        "gender": "male"
    },
    {
        "value": "Markus",
        "gender": "male"
    },
    {
        "value": "Daniel",
        "gender": "male"
    },
    {
        "value": "Alexander",
        "gender": "male"
    },
    {
        "value": "Johannes",
        "gender": "male"
    },
    {
        "value": "Sebastian",
        "gender": "male"
    },
    {
        "value": "Wolfgang",
        "gender": "male"
    },
    {
        "value": "Klaus",
        "gender": "male"
    },
    {
        "value": "Rainer",
        "gender": "male"
    },
    {
        "value": "Gerhard",
        "gender": "male"
    }
]


def first_name():
    return random.choice(
        FIRST_NAMES
    )


LAST_NAMES = [
    "Schmidt",
    "Müller",
    "Fischer",
    "Weber",
    "Meyer",
    "Wagner",
    "Becker",
    "Schulz",
    "Hoffmann",
    "Schäfer",
    "Koch",
    "Bauer",
    "Richter",
    "Klein",
    "Wolf",
    "Schröder",
    "Neumann",
    "Schwarz",
    "Zimmermann",
    "Braun",
    "Krüger",
    "Hofmann",
    "Hartmann",
    "Lange",
    "Schmitt",
    "Werner",
    "Schmitz",
    "Krause",
    "Meier",
    "Lehmann",
    "Huber",
    "Kaiser",
    "Fuchs",
    "Peters",
    "Lang",
    "Möller",
    "Jung",
    "Hahn",
    "Keller",
    "Vogel"
]


def last_name():
    return random.choice(
        LAST_NAMES
    )