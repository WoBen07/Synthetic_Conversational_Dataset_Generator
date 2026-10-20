"""Generators shared by all domains.

A domain adds its own generators in domains/<name>/generators/ (its
GENERATORS dict); domain entries override shared ones with the same key.
See documentation/domains.md.
"""

from .names import first_name, last_name
from .days import weekday
from .birthday import birthday


REGISTRY = {

    "first_name": first_name,
    "last_name": last_name,

    "weekday": weekday,

    "birthday": birthday,
}
