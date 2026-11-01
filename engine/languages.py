"""Language rules: what the engine has to know about a language.

A domain (or a variant of it) names its language in domain.yaml. Phrases,
wording and tool descriptions are the domain's; this table holds what the
engine itself produces or checks:

- weekdays: values of ``today`` and of the ``weekday`` generator;
- pronouns: fields the linguistic resolver adds per gender;
- wording: default sentences of the opening system message;
- name_prefixes: words a ``format: name`` tool argument must not start with;
- allowed_doubles: words that may legitimately repeat ("die die");
- english_articles: whether the a/an rules apply.

A new language is one more entry here. See documentation/domains.md.
"""

from synthetic_data_generator.engine.text_utils import ALLOWED_DOUBLES
from synthetic_data_generator.generators.days import DAYS


LANGUAGES = {

    "en": {
        "weekdays": DAYS,
        "pronouns": {
            "male": {"pronoun": "he", "object_pronoun": "him", "possessive_pronoun": "his", "title": "Mr."},
            "female": {"pronoun": "she", "object_pronoun": "her", "possessive_pronoun": "her", "title": "Ms."},
            "other": {"pronoun": "they", "object_pronoun": "them", "possessive_pronoun": "their", "title": "Mx."},
        },
        "wording": {
            "today": "Today is {today}.",
            "location": "You are in {location}.",
        },
        "name_prefixes": ["the", "a", "an"],
        "allowed_doubles": ALLOWED_DOUBLES,
        "english_articles": True,
    },

    "de": {
        "weekdays": ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"],
        "pronouns": {
            "male": {"pronoun": "er", "object_pronoun": "ihn", "possessive_pronoun": "sein", "title": "Herr"},
            "female": {"pronoun": "sie", "object_pronoun": "sie", "possessive_pronoun": "ihr", "title": "Frau"},
            "other": {"pronoun": "sie", "object_pronoun": "sie", "possessive_pronoun": "ihr", "title": ""},
        },
        "wording": {
            "today": "Heute ist {today}.",
            "location": "Du befindest dich hier: {location}.",
        },
        "name_prefixes": [
            "der", "die", "das", "den", "dem", "des",
            "ein", "eine", "einen", "einem", "einer",
            "im", "in", "ins", "am", "an", "auf", "zum", "zur",
        ],
        "allowed_doubles": {"der", "die", "das", "ja", "nein", "so", "sehr"},
        "english_articles": False,
    },
}


def language_rules(language):
    """The rules of a language code; an unknown one is an error, since the
    engine would otherwise produce English in the middle of its text."""

    if language not in LANGUAGES:
        raise ValueError(
            f"Unknown language {language!r}: add it to LANGUAGES in "
            f"engine/languages.py. Available: {', '.join(sorted(LANGUAGES))}"
        )

    return LANGUAGES[language]
