import random


# Room name, then the German forms a phrase needs: "im Wohnzimmer" (where),
# "das Wohnzimmer" (direct object of saugen/heizen), "ins Wohnzimmer" (to).
ROOMS = {
    "Wohnzimmer": ("im Wohnzimmer", "das Wohnzimmer", "ins Wohnzimmer"),
    "Schlafzimmer": ("im Schlafzimmer", "das Schlafzimmer", "ins Schlafzimmer"),
    "Büro": ("im Büro", "das Büro", "ins Büro"),
    "Arbeitszimmer": ("im Arbeitszimmer", "das Arbeitszimmer", "ins Arbeitszimmer"),
    "Küche": ("in der Küche", "die Küche", "in die Küche"),
    "Bad": ("im Bad", "das Bad", "ins Bad"),
    "Badezimmer": ("im Badezimmer", "das Badezimmer", "ins Badezimmer"),
    "Flur": ("im Flur", "den Flur", "in den Flur"),
    "Esszimmer": ("im Esszimmer", "das Esszimmer", "ins Esszimmer"),
    "Kinderzimmer": ("im Kinderzimmer", "das Kinderzimmer", "ins Kinderzimmer"),
    "Gästezimmer": ("im Gästezimmer", "das Gästezimmer", "ins Gästezimmer"),
}

# A string of fairy lights hangs where people spend the evening, not in the
# hallway or the bathroom.
STRING_LIGHT_ROOMS = ["Wohnzimmer", "Schlafzimmer", "Büro", "Esszimmer", "Kinderzimmer"]

STRING_LIGHT_SHARE = 0.3

# How a light is called: noun phrase, dative, accusative pronoun, and what
# "change its colour" refers to ("die Lichtfarbe im Wohnzimmer" names the
# normal light; string lights have to be said).
MAIN_LIGHT_NAMES = [
    ("das Licht", "dem Licht", "es", "die Lichtfarbe"),
    ("das Licht", "dem Licht", "es", "die Farbe des Lichts"),
    ("die Lampe", "der Lampe", "sie", "die Farbe der Lampe"),
    ("die Beleuchtung", "der Beleuchtung", "sie", "die Farbe der Beleuchtung"),
]

STRING_LIGHT_NAME = ("die Lichterkette", "der Lichterkette", "sie", "die Farbe der Lichterkette")

COLORS = {
    "red": "rot",
    "green": "grün",
    "blue": "blau",
    "yellow": "gelb",
    "orange": "orange",
    "purple": "lila",
    "pink": "pink",
    "turquoise": "türkis",
    "white": "weiß",
}

# Most vacuum requests use its name; the rest say what it is.
VACUUM_NAMES = [
    ("Fridolin", "Fridolin"),
    ("Der Sauger", "den Sauger"),
    ("Der Staubsauger", "den Staubsauger"),
    ("Der Saugroboter", "den Saugroboter"),
]

VACUUM_NAME_SHARE = 0.6


def capitalized(text):
    """Capitalize the first letter only ("Im Wohnzimmer")."""

    return text[0].upper() + text[1:]


def room_forms(name):

    in_room, accusative, into_room = ROOMS[name]

    return {
        "in_room": in_room,
        "in_room_cap": capitalized(in_room),
        "accusative": accusative,
        "accusative_cap": capitalized(accusative),
        "into_room": into_room,
    }


def room():

    name = random.choice(list(ROOMS))

    return {"value": name, **room_forms(name)}


def light():
    """A light and the room it is in, drawn together: the value is the
    ``light`` tool argument, the other fields are its German forms."""

    if random.random() < STRING_LIGHT_SHARE:
        fixture = "string_lights"
        names = STRING_LIGHT_NAME
        room_name = random.choice(STRING_LIGHT_ROOMS)
    else:
        fixture = "main"
        names = random.choice(MAIN_LIGHT_NAMES)
        room_name = random.choice(list(ROOMS))

    phrase, dative, pronoun, color_subject = names

    return {
        "value": fixture,
        "phrase": phrase,
        "phrase_cap": capitalized(phrase),
        "dative": dative,
        "pronoun_acc": pronoun,
        "color_subject": color_subject,
        "room": room_name,
        **room_forms(room_name),
    }


def light_color():

    color = random.choice(list(COLORS))

    return {"value": color, "german": COLORS[color]}


def non_white_light_color():
    """For a white-only light: "it can only do white, not white" is no
    conversation."""

    color = random.choice([name for name in COLORS if name != "white"])

    return {"value": color, "german": COLORS[color]}


def brightness_pct():
    """Mostly round values, as people say them, some exact ones."""

    if random.random() < 0.8:
        return random.randrange(5, 95, 5)

    return random.randint(1, 95)


def target_temperature():

    return random.randint(15, 28)


def vacuum_name():

    if random.random() < VACUUM_NAME_SHARE:
        nominative_cap, accusative = VACUUM_NAMES[0]
    else:
        nominative_cap, accusative = random.choice(VACUUM_NAMES[1:])

    return {
        "value": nominative_cap,
        "nominative_cap": nominative_cap,
        "accusative": accusative,
    }
