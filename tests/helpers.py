"""Shared setup for the tests.

Run from inside synthetic_data_generator/::

    python -m unittest discover -s tests

or from the directory above it::

    python -m unittest discover -s synthetic_data_generator/tests

Set UPDATE_GOLDEN=1 to rewrite the expected outputs in tests/golden/
after an intended change of the generated data.
"""

import random
import sys
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]

# The package imports itself as synthetic_data_generator.*, so its parent
# directory has to be importable.
if str(PACKAGE_ROOT.parent) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT.parent))

from synthetic_data_generator.engine.dataset_generator import DatasetGenerator  # noqa: E402,F401
from synthetic_data_generator.engine.domain import load_domain  # noqa: E402
from synthetic_data_generator.domains.hospital.generators import ids, weather  # noqa: E402

# The domain most tests run against
HOSPITAL = load_domain("hospital")


def reset_generators(seed):
    """Make generation fully reproducible: seed and module-level state."""

    random.seed(seed)
    ids.counter = 0
    weather._current_profile = None


def paths(template_id, domain=HOSPITAL):

    return domain.paths(template_id)


def generate(generator, template_id):

    return generator.generate_one(*paths(template_id, generator.domain))


def generate_valid(generator, template_id, attempts=150):
    """First valid datapoint within ``attempts``, or None."""

    for _ in range(attempts):

        try:
            datapoint = generate(generator, template_id)
        except ValueError:
            # Constraint violation - the generator redraws as well.
            continue

        if not generator.validator.validate(datapoint):
            return datapoint

    return None


def all_templates(domain=HOSPITAL):

    return domain.templates()


def conversation(*messages):
    """Build a datapoint from (role, content-or-dict) pairs."""

    built = []

    for role, value in messages:

        if isinstance(value, dict):
            built.append({"role": role, **value})
        else:
            built.append({"role": role, "content": value})

    return {"messages": built}
