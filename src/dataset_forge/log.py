"""Logging setup of the command line tools."""

import logging
import sys


def configure_cli_logging(level=logging.INFO):
    """Print the package's log messages as plain lines on stdout, in order
    with its other output. Does nothing if logging is already set up."""

    package = logging.getLogger("dataset_forge")

    if package.handlers:
        return

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(message)s"))

    package.addHandler(handler)
    package.setLevel(level)
