"""Python part of the hospital domain pack.

The engine reads three optional names from a domain package:

- GENERATORS: {key: function}, added to the shared generators;
- create_validators(): validator instances run after the engine's
  structural checks;
- refresh_entity(entity): called for every entity after constraints are
  resolved, to keep derived fields consistent.
"""

import random

from .generators import GENERATORS  # noqa: F401
from .generators.appointments import TYPE_LOCATIONS, locations_for
from .validators import create_validators  # noqa: F401


def refresh_entity(entity):

    # An "equal" constraint can copy one appointment's type onto another
    # whose location was drawn for a different type. Draw a fitting
    # location again so type and room never contradict.
    appointment_type = entity.get("appointment_type")

    if appointment_type in TYPE_LOCATIONS and "location" in entity:

        allowed = locations_for(appointment_type)

        if entity["location"] not in allowed:
            entity["location"] = random.choice(allowed)
