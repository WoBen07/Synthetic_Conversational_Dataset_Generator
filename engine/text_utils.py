"""Small English helpers shared by the renderer and the validators."""

import re


# Letters whose spoken name starts with a vowel sound, for acronyms
# read letter by letter ("an MRI", "an ENT", "an X-ray", "an ECG").
_VOWEL_SOUND_LETTERS = set("AEFHILMNORSX")

# Words that start with a vowel letter but a consonant sound.
_CONSONANT_SOUND_PREFIXES = (
    "uni", "use", "usu", "uti", "ure", "uro", "eu", "one", "once", "ewe",
)

# Words that start with "h" but a vowel sound.
_SILENT_H_PREFIXES = (
    "hour", "honest", "honor", "honour", "heir",
)

_FIRST_WORD = re.compile(r"[A-Za-z0-9][A-Za-z0-9'\-]*")


def wants_an(phrase):
    """Return True when ``phrase`` takes "an" rather than "a"."""

    match = _FIRST_WORD.search(phrase)

    if not match:
        return False

    word = match.group(0)

    if word[0].isdigit():
        return word[0] == "8"

    head = word.split("-")[0]

    # Acronyms (MRI, ENT, ECG) and letter compounds (X-ray, T-shirt)
    if (len(head) > 1 and head.isupper()) or (len(head) == 1 and "-" in word):
        return head[0].upper() in _VOWEL_SOUND_LETTERS

    lower = word.lower()

    if lower.startswith(_SILENT_H_PREFIXES):
        return True

    if lower[0] in "aeiou":
        return not lower.startswith(_CONSONANT_SOUND_PREFIXES)

    return False


def article_for(phrase, capitalized=False):

    article = "an" if wants_an(phrase) else "a"

    return article.capitalize() if capitalized else article


# "a" / "an" as a standalone word followed by the next word
ARTICLE_PATTERN = re.compile(
    r"(?<![\w'\-])([Aa]n?) (?=([A-Za-z0-9][A-Za-z0-9'\-]*))"
)


def article_mismatches(text):
    """Return every "a X" / "an X" in ``text`` with the wrong article."""

    found = []

    for match in ARTICLE_PATTERN.finditer(text):

        article = match.group(1).lower()
        word = match.group(2)

        # "A" can be a list label or a grade ("Plan A", "an A"); only
        # judge lowercase "a", or a capital "A" that starts a sentence.
        if match.group(1) == "A" and match.start() > 0:
            before = text[:match.start()].rstrip()
            if before and before[-1] not in ".!?\"“(:—–-":
                continue

        if (article == "an") != wants_an(word):
            found.append(f"{match.group(1)} {word}")

    return found


DOUBLE_WORD = re.compile(r"\b(\w+)\s+\1\b", re.IGNORECASE)

# Repetitions that are fine in spoken English
_ALLOWED_DOUBLES = {"that", "had", "very", "bye", "no", "so", "really", "now"}


def doubled_words(text):

    return [
        match.group(0)
        for match in DOUBLE_WORD.finditer(text)
        if match.group(1).lower() not in _ALLOWED_DOUBLES
        and not match.group(1).isdigit()
    ]
