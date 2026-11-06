"""Where the generator finds its files and writes its output.

Two roots are kept apart:

- ``PACKAGE_DIR``: the installed package. It ships the engine, the
  built-in domain packs and the default ``config/generation_config.yaml``.
  Nothing is written here.
- ``PROJECT_ROOT``: the user's working folder. It may hold its own
  ``domains/`` and ``config/``, and receives ``Synthetic_Data/`` and
  ``Datasets/``.

``PROJECT_ROOT`` is, in this order:

1. ``$DFORGE_PROJECT_DIR`` if set,
2. the repository root when running from a source checkout
   (``<repo>/src/dataset_forge`` next to ``<repo>/pyproject.toml``),
3. the current working directory.
"""

import os
from pathlib import Path

PROJECT_ENV_VAR = "DFORGE_PROJECT_DIR"

PACKAGE_DIR = Path(__file__).resolve().parents[1]

BUILTIN_DOMAINS_DIR = PACKAGE_DIR / "domains"

DEFAULT_CONFIG_DIR = PACKAGE_DIR / "config"


def find_project_root():

    configured = os.environ.get(PROJECT_ENV_VAR)

    if configured:
        return Path(configured).expanduser().resolve()

    repository = PACKAGE_DIR.parents[1]

    if PACKAGE_DIR.parent.name == "src" and (repository / "pyproject.toml").exists():
        return repository

    return Path.cwd().resolve()


PROJECT_ROOT = find_project_root()

PROJECT_DOMAINS_DIR = PROJECT_ROOT / "domains"

PROJECT_CONFIG_DIR = PROJECT_ROOT / "config"

OUTPUT_ROOT = PROJECT_ROOT / "Synthetic_Data"

DATASETS_DIR = PROJECT_ROOT / "Datasets"


def config_file(name):
    """The project's ``config/<name>`` if it has one, otherwise the default
    shipped with the package."""

    own = PROJECT_CONFIG_DIR / name

    return own if own.exists() else DEFAULT_CONFIG_DIR / name


def display(path):
    """``path`` relative to the project root where possible, for messages."""

    path = Path(path)

    for root in (PROJECT_ROOT, PACKAGE_DIR.parent):
        if path.is_relative_to(root):
            return str(path.relative_to(root))

    return str(path)
