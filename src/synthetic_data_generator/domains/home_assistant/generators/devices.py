"""Values of the home_assistant domain. Names vary on purpose: the model is
for any home, so it has to read them from the system message.

Fields starting with ``home_`` tell home.py what an entity needs in the home;
``absent`` says it must not be there.
"""

import random


# Room name, then the German forms a phrase needs: where ("im Wohnzimmer"),
# direct object ("das Wohnzimmer"), to ("ins Wohnzimmer").
ROOMS = {
    "Wohnzimmer": ("im Wohnzimmer", "das Wohnzimmer", "ins Wohnzimmer"),
    "Schlafzimmer": ("im Schlafzimmer", "das Schlafzimmer", "ins Schlafzimmer"),
    "Büro": ("im Büro", "das Büro", "ins Büro"),
    "Arbeitszimmer": ("im Arbeitszimmer", "das Arbeitszimmer", "ins Arbeitszimmer"),
    "Küche": ("in der Küche", "die Küche", "in die Küche"),
    "Bad": ("im Bad", "das Bad", "ins Bad"),
    "Badezimmer": ("im Badezimmer", "das Badezimmer", "ins Badezimmer"),
    "Gäste-WC": ("im Gäste-WC", "das Gäste-WC", "ins Gäste-WC"),
    "Flur": ("im Flur", "den Flur", "in den Flur"),
    "Diele": ("in der Diele", "die Diele", "in die Diele"),
    "Esszimmer": ("im Esszimmer", "das Esszimmer", "ins Esszimmer"),
    "Kinderzimmer": ("im Kinderzimmer", "das Kinderzimmer", "ins Kinderzimmer"),
    "Gästezimmer": ("im Gästezimmer", "das Gästezimmer", "ins Gästezimmer"),
    "Hobbyraum": ("im Hobbyraum", "den Hobbyraum", "in den Hobbyraum"),
    "Keller": ("im Keller", "den Keller", "in den Keller"),
    "Dachboden": ("auf dem Dachboden", "den Dachboden", "auf den Dachboden"),
    "Waschküche": ("in der Waschküche", "die Waschküche", "in die Waschküche"),
    "Wintergarten": ("im Wintergarten", "den Wintergarten", "in den Wintergarten"),
    "Ankleide": ("in der Ankleide", "die Ankleide", "in die Ankleide"),
    "Lenas Zimmer": ("in Lenas Zimmer", "Lenas Zimmer", "in Lenas Zimmer"),
    "Maxis Zimmer": ("in Maxis Zimmer", "Maxis Zimmer", "in Maxis Zimmer"),
    "Emmas Zimmer": ("in Emmas Zimmer", "Emmas Zimmer", "in Emmas Zimmer"),
    "Balkon": ("auf dem Balkon", "den Balkon", "auf den Balkon"),
    "Terrasse": ("auf der Terrasse", "die Terrasse", "auf die Terrasse"),
    "Garage": ("in der Garage", "die Garage", "in die Garage"),
}

# Nobody vacuums or heats these.
OUTDOOR_ROOMS = {"Balkon", "Terrasse", "Garage"}

INDOOR_ROOMS = [name for name in ROOMS if name not in OUTDOOR_ROOMS]

# Names of one room: a home has only one of them.
SAME_ROOM = {"Bad": "Badezimmer", "Badezimmer": "Bad", "Flur": "Diele", "Diele": "Flur"}

GENDERED = {
    # nominative, accusative, dative article, genitive article, pronoun
    "f": ("die", "die", "der", "der", "sie"),
    "m": ("der", "den", "dem", "des", "ihn"),
    "n": ("das", "das", "dem", "des", "es"),
}

# Name, gender, genitive ending, rooms it can be in (None: any indoor room)
NAMED_LIGHTS = [
    ("Deckenlampe", "f", "", None),
    ("Stehlampe", "f", "", None),
    ("Tischlampe", "f", "", None),
    ("Leselampe", "f", "", None),
    ("Lichterkette", "f", "", None),
    ("Wandleuchte", "f", "", None),
    ("Hängelampe", "f", "", None),
    ("Bogenlampe", "f", "", None),
    ("Nachttischlampe", "f", "", ["Schlafzimmer", "Gästezimmer", "Kinderzimmer", "Lenas Zimmer", "Maxis Zimmer", "Emmas Zimmer"]),
    ("Esstischlampe", "f", "", ["Esszimmer", "Küche"]),
    ("Spiegelleuchte", "f", "", ["Bad", "Badezimmer", "Gäste-WC"]),
    ("LED-Streifen", "m", "s", None),
    ("Deckenfluter", "m", "s", None),
    ("Strahler", "m", "s", None),
    ("Leuchtglobus", "m", "", None),
    ("Nachtlicht", "n", "s", ["Schlafzimmer", "Kinderzimmer", "Lenas Zimmer", "Maxis Zimmer", "Emmas Zimmer", "Flur", "Diele"]),
]

# What "the light of the room" is called; the tool gets no light name then.
GENERIC_LIGHTS = [
    ("Licht", "n", "s", "die Lichtfarbe"),
    ("Licht", "n", "s", "die Farbe des Lichts"),
    ("Lampe", "f", "", "die Farbe der Lampe"),
    ("Beleuchtung", "f", "", "die Farbe der Beleuchtung"),
]

# Things on a switched socket: name, gender. Not the unsupported devices of
# no_tool/unsupported_device, which no home has.
SWITCHES = [
    ("Kaffeemaschine", "f"),
    ("Ventilator", "m"),
    ("Drucker", "m"),
    ("Wasserkocher", "m"),
    ("Weihnachtsbaum", "m"),
    ("Luftbefeuchter", "m"),
    ("Luftreiniger", "m"),
    ("Radio", "n"),
    ("Fernseher", "m"),
    ("Aquarium", "n"),
    ("Monitor", "m"),
    ("Verstärker", "m"),
    ("Spielekonsole", "f"),
    ("Heizlüfter", "m"),
    ("Springbrunnen", "m"),
]

SCENES = [
    "Filmabend", "Gute Nacht", "Guten Morgen", "Essen", "Lesen", "Party",
    "Kochen", "Entspannen", "Romantik", "Arbeiten", "Kino", "Besuch",
    "Hausputz", "Spielabend", "Frühstück", "Sonntag",
]

AUTOMATIONS = [
    "Morgenroutine", "Abendroutine", "Lüften", "Urlaubsmodus", "Wintermodus",
    "Alles aus", "Pflanzen gießen", "Sonnenschutz", "Anwesenheit simulieren",
    "Kaffee vorbereiten", "Nachtmodus", "Heimkommen",
]

# Name, gender
LOCKS = [
    ("Haustür", "f"), ("Hintertür", "f"), ("Kellertür", "f"),
    ("Terrassentür", "f"), ("Balkontür", "f"), ("Gartentor", "n"),
]

COLORS = {
    "red": "rot", "green": "grün", "blue": "blau", "yellow": "gelb",
    "orange": "orange", "purple": "lila", "pink": "pink",
    "turquoise": "türkis", "white": "weiß",
}

# Name of the vacuum robot, pronoun of the name. A home may also not have
# given it one.
ROBOT_NAMES = [
    ("Fridolin", "er"), ("Robi", "er"), ("Rosie", "sie"), ("Bruno", "er"),
    ("Herbert", "er"), ("Klaus", "er"), ("Emma", "sie"), ("Karl", "er"),
    ("Hugo", "er"), ("Lotte", "sie"), ("Staubi", "er"), ("Saugi", "er"),
    ("Flitzi", "er"), ("Wall-E", "er"), ("Dusty", "er"), ("Mia", "sie"),
    ("Theo", "er"), ("Greta", "sie"), ("Otto", "er"), ("Frieda", "sie"),
    ("Putzi", "er"), ("Krümel", "er"), ("Bert", "er"), ("Luise", "sie"),
]

UNNAMED_ROBOT_SHARE = 0.15

# How often the user says the robot's name when it has one
SAYS_NAME_SHARE = 0.65

VACUUM_WORDS = [
    ("Der Sauger", "den Sauger"),
    ("Der Staubsauger", "den Staubsauger"),
    ("Der Saugroboter", "den Saugroboter"),
    ("Der Roboter", "den Roboter"),
]


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


def _room(name):

    return {"value": name, "home_room": name, **room_forms(name)}


def home():
    """Filled by home.py once all entities of the conversation exist."""

    return "home"


def room():

    return _room(random.choice(list(ROOMS)))


def indoor_room():

    return _room(random.choice(INDOOR_ROOMS))


def missing_room():
    """A room the home does not have."""

    return {**_room(random.choice(INDOOR_ROOMS)), "absent": True}


def noun_forms(name, gender, genitive=""):

    nominative, accusative, dative, genitive_article, pronoun = GENDERED[gender]

    return {
        "nom": f"{nominative} {name}",
        "nom_cap": f"{capitalized(nominative)} {name}",
        "acc": f"{accusative} {name}",
        "acc_cap": f"{capitalized(accusative)} {name}",
        "dat": f"{dative} {name}",
        "gen": f"{genitive_article} {name}{genitive}",
        "pron_acc": pronoun,
    }


def _light(fixture, forms, color_subject, room_name):
    """``fixture`` is the value of the light argument; empty means the light
    of the room, and postprocess.py drops the argument."""

    return {
        "value": fixture,
        "home_room": room_name,
        "home_light": fixture,
        "room": room_name,
        "color_subject": color_subject,
        **forms,
        **room_forms(room_name),
    }


def generic_light():

    name, gender, genitive, color_subject = random.choice(GENERIC_LIGHTS)

    return _light("", noun_forms(name, gender, genitive), color_subject, random.choice(list(ROOMS)))


def indoor_generic_light():
    """For a home of a single room: nobody lives on the balcony."""

    name, gender, genitive, color_subject = random.choice(GENERIC_LIGHTS)

    return _light("", noun_forms(name, gender, genitive), color_subject, random.choice(INDOOR_ROOMS))


def named_light():

    name, gender, genitive, rooms = random.choice(NAMED_LIGHTS)

    forms = noun_forms(name, gender, genitive)

    return _light(name, forms, f"die Farbe {forms['gen']}", random.choice(rooms or INDOOR_ROOMS))


def light():
    """Either the light of a room or a named one."""

    return named_light() if random.random() < 0.4 else generic_light()


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


def impossible_brightness():

    return random.choice([110, 120, 150, 200, 300, 500, 1000])


def spoken_number(value):
    """21.5 is said "21,5"; a whole number has no decimals in the argument."""

    return {"value": value, "spoken": str(value).replace(".", ",")}


def target_temperature():
    """Thermostats take half degrees, people mostly say whole ones."""

    if random.random() < 0.25:
        return spoken_number(random.randint(16, 26) + 0.5)

    return spoken_number(random.randint(15, 28))


def impossible_temperature():

    return spoken_number(random.choice([1, 2, 3, 4, 31, 32, 35, 40, 50, 60, 70, 80, 90, 100]))


def vacuum():
    """The robot of this home, and how the user calls it in this request.
    Replies use its real name."""

    if random.random() < UNNAMED_ROBOT_SHARE:
        robot, reply_pronoun = "", "er"
    else:
        robot, reply_pronoun = random.choice(ROBOT_NAMES)

    if robot and random.random() < SAYS_NAME_SHARE:
        nominative_cap, accusative, pronoun = robot, robot, reply_pronoun
        nominative = robot
    else:
        nominative_cap, accusative = random.choice(VACUUM_WORDS)
        nominative = nominative_cap[0].lower() + nominative_cap[1:]
        pronoun = "er"

    return {
        "value": robot,
        "home_vacuum": robot,
        "nom": nominative,
        "nom_cap": nominative_cap,
        "acc": accusative,
        "pronoun": pronoun,
        "reply": robot or "der Saugroboter",
        "reply_cap": robot or "Der Saugroboter",
        "reply_acc": robot or "den Saugroboter",
        "reply_dat": robot or "dem Saugroboter",
        "reply_pronoun": reply_pronoun,
    }


def _switch(name, gender):

    room_name = random.choice(INDOOR_ROOMS)

    return {
        "value": name,
        "home_room": room_name,
        "home_switch": name,
        "room": room_name,
        **noun_forms(name, gender),
        **room_forms(room_name),
    }


def switch():

    return _switch(*random.choice(SWITCHES))


def missing_switch():
    """Something the home has no switch for. No room, it is simply not there."""

    name, gender = random.choice(SWITCHES)

    return {"value": name, "home_absent_switch": name, **noun_forms(name, gender)}


def scene():

    name = random.choice(SCENES)

    return {"value": name, "home_scene": name}


def missing_scene():

    name = random.choice(SCENES)

    return {"value": name, "home_absent_scene": name}


def automation():

    name = random.choice(AUTOMATIONS)

    return {"value": name, "home_automation": name}


def lock():

    name, gender = random.choice(LOCKS)

    return {"value": name, "home_lock": name, **noun_forms(name, gender)}
