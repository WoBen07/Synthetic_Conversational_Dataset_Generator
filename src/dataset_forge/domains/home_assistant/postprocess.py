"""The rendered conversation, before it is validated."""

import random
import re

from .hass_mapping import to_home_assistant_intents


# Share of conversations that look like a speech recognizer wrote the user's
# side: lowercase, no punctuation, sometimes a filler word.
SPEECH_SHARE = 0.35

FILLERS = ["ähm", "äh", "also", "ok"]

FILLER_SHARE = 0.25

# Commas between digits are decimal commas.
PUNCTUATION = re.compile(r"(?<!\d),|,(?!\d)|[.!?:;](?=\s|$)")


def _drop_empty_arguments(datapoint):
    """A placeholder that stands for "not given" renders empty: the light of
    a room has no light name, and then the argument does not exist."""

    for message in datapoint["messages"]:

        call = message.get("tool_call")

        if call:
            call["arguments"] = {
                key: value for key, value in call["arguments"].items()
                if value != ""
            }


def _as_speech(text):

    text = PUNCTUATION.sub("", text.lower()).replace("%", " prozent")

    text = " ".join(text.split())

    if random.random() < FILLER_SHARE:
        text = f"{random.choice(FILLERS)} {text}"

    return text


def postprocess(datapoint, domain):

    _drop_empty_arguments(datapoint)

    # One recognizer per conversation
    if random.random() < SPEECH_SHARE:

        for message in datapoint["messages"]:

            if message.get("role") == "user":
                message["content"] = _as_speech(message["content"])

    if domain.variant == "hass":
        to_home_assistant_intents(datapoint)

    return datapoint
