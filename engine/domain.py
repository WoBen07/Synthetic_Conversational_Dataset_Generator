"""Domain packs: everything that belongs to one application domain.

The engine knows nothing about hospitals. All domain content lives in
``domains/<name>/``::

    domains/<name>/
      domain.yaml        name, description, ID pattern, robot_context wording
      config.yaml        amounts, tool-share targets, uniqueness caps
      templates/         <category>/<template>.json
      scenarios/         <category>/<template>.yaml
      language/          <category>/<template>.yaml
      entities/          <type>.yaml
      tools/             <tool>.yaml
      __init__.py        optional Python hooks (GENERATORS,
                         create_validators(), refresh_entity())
      generators/        optional, domain-specific value generators
      validators/        optional, domain-specific validators

See documentation/domains.md.
"""

import importlib
import re
from functools import lru_cache
from pathlib import Path

import yaml

from synthetic_data_generator.engine.tool_registry import load_tools
from synthetic_data_generator.generators import REGISTRY as SHARED_GENERATORS


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DOMAINS_DIR = PROJECT_ROOT / "domains"

GLOBAL_CONFIG_FILE = PROJECT_ROOT / "config" / "generation_config.yaml"

# Matches nothing - for domains without generated IDs
NO_MATCH = r"(?!)"


class Domain:

    def __init__(self, name, root=None):
        """``root`` defaults to domains/<name>; tests pass another folder.
        Python hooks are only imported for packs inside domains/."""

        self.name = name
        self.root = Path(root) if root else DOMAINS_DIR / name

        spec_file = self.root / "domain.yaml"

        if not spec_file.exists():
            raise FileNotFoundError(
                f"Unknown domain {name!r}: {spec_file} not found. "
                f"Available: {', '.join(list_domains()) or 'none'}"
            )

        self.spec = yaml.safe_load(spec_file.read_text(encoding="utf-8")) or {}

        self.description = " ".join(str(self.spec.get("description", "")).split())

        self.template_dir = self.root / "templates"
        self.scenario_dir = self.root / "scenarios"
        self.language_dir = self.root / "language"
        self.entity_dir = self.root / "entities"
        self.tool_dir = self.root / "tools"
        self.config_file = self.root / "config.yaml"

        self.robot_context = self.spec.get("robot_context") or {}

        self.generated_id_pattern = re.compile(
            self.spec.get("generated_id_pattern") or NO_MATCH
        )

        self.module = self._import_module()

        self.generators = {
            **SHARED_GENERATORS,
            **getattr(self.module, "GENERATORS", {}),
        }


    def _import_module(self):

        if not (self.root / "__init__.py").exists():
            return None

        if self.root.parent.resolve() != DOMAINS_DIR.resolve():
            raise ValueError(
                f"{self.root} has Python hooks but is outside {DOMAINS_DIR}; "
                f"they can only be imported from there"
            )

        return importlib.import_module(
            f"synthetic_data_generator.domains.{self.name}"
        )


    # ---------- templates ----------

    def templates(self):
        """Template ids (path below templates/ without .json), sorted."""

        return [
            path.relative_to(self.template_dir).with_suffix("").as_posix()
            for path in sorted(self.template_dir.rglob("*.json"))
        ]

    def template_path(self, template_id):
        return self.template_dir / f"{template_id}.json"

    def scenario_path(self, template_id):
        return self.scenario_dir / f"{template_id}.yaml"

    def language_path(self, template_id):
        return self.language_dir / f"{template_id}.yaml"

    def entity_path(self, entity_type):
        return self.entity_dir / f"{entity_type}.yaml"

    def paths(self, template_id):
        """(scenario, template, language) arguments for generate_one."""

        return (
            str(self.scenario_path(template_id)),
            template_id,
            str(self.language_path(template_id)),
        )


    # ---------- configuration and tools ----------

    def load_config(self):
        """Read config.yaml (not cached - the optimizer rewrites it)."""

        if not self.config_file.exists():
            return {}

        return yaml.safe_load(self.config_file.read_text(encoding="utf-8")) or {}

    @property
    def tools(self):
        return load_tools(self.tool_dir)


    # ---------- Python hooks ----------

    def create_validators(self):

        factory = getattr(self.module, "create_validators", None)

        return factory() if factory else []

    def refresh_entity(self, entity):

        hook = getattr(self.module, "refresh_entity", None)

        if hook:
            hook(entity)


    def __repr__(self):
        return f"Domain({self.name!r})"


def list_domains():
    """Names of all domain packs (folders with a domain.yaml)."""

    if not DOMAINS_DIR.exists():
        return []

    return sorted(
        path.parent.name
        for path in DOMAINS_DIR.glob("*/domain.yaml")
    )


@lru_cache(maxsize=None)
def load_domain(name):
    return Domain(name)


def load_global_config():

    if not GLOBAL_CONFIG_FILE.exists():
        return {}

    return yaml.safe_load(GLOBAL_CONFIG_FILE.read_text(encoding="utf-8")) or {}


def configured_domains():
    """Domains to generate when none is named: the global config's
    ``domains`` list, or every domain pack."""

    return load_global_config().get("domains") or list_domains()


def default_domain():
    """The domain used when code does not name one: the first configured
    domain."""

    domains = configured_domains()

    if not domains:
        raise RuntimeError(f"No domain packs found in {DOMAINS_DIR}")

    return domains[0]


def resolve_domain(domain):
    """Accept a Domain, a domain name or None (default domain)."""

    if isinstance(domain, Domain):
        return domain

    return load_domain(domain or default_domain())
