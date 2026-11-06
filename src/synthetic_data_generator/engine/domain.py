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
      variants/<variant>/  optional overlays: another language and/or
                         another tool schema, named "<name>@<variant>"

See documentation/domains.md.
"""

import copy
import importlib
import json
import random
import re
from functools import cached_property, lru_cache
from pathlib import Path

import yaml

from synthetic_data_generator.engine.languages import language_rules
from synthetic_data_generator.engine.paths import (
    BUILTIN_DOMAINS_DIR,
    PROJECT_DOMAINS_DIR,
    PROJECT_ROOT,  # noqa: F401  (re-exported)
    config_file,
)
from synthetic_data_generator.engine.tool_registry import load_tools
from synthetic_data_generator.generators import REGISTRY as SHARED_GENERATORS


# Folders searched for domain packs, in order: the project's own packs
# shadow built-in packs of the same name.
DOMAIN_DIRS = [PROJECT_DOMAINS_DIR, BUILTIN_DOMAINS_DIR]

GLOBAL_CONFIG_FILE = config_file("generation_config.yaml")

# Matches nothing - for domains without generated IDs
NO_MATCH = r"(?!)"

# Separates a domain from its variant: "home_assistant@en"
VARIANT_SEPARATOR = "@"

PLACEHOLDER = re.compile(r"\{\{.*?\}\}")


def deep_merge(base, patch):
    """``patch`` on top of ``base``: dictionaries merge key by key, anything
    else (lists too) is replaced. Neither input is changed."""

    merged = copy.deepcopy(base)

    for key, value in patch.items():

        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = copy.deepcopy(value)

    return merged


def _read_yaml(path):

    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


class Domain:

    def __init__(self, name, root=None):
        """``name`` is "<domain>" or "<domain>@<variant>". ``root`` defaults
        to the first <folder>/<domain> of DOMAIN_DIRS; tests pass another
        folder. Python hooks are only imported for packs inside one of
        DOMAIN_DIRS."""

        self.name = name

        self.base_name, _, variant = name.partition(VARIANT_SEPARATOR)

        self.variant = variant or None

        self.root = Path(root) if root else find_pack(self.base_name)

        spec_file = self.root / "domain.yaml"

        if not spec_file.exists():
            raise FileNotFoundError(
                f"Unknown domain {name!r}: {spec_file} not found. "
                f"Available: {', '.join(list_domains()) or 'none'}"
            )

        self.base_spec = _read_yaml(spec_file)

        self.spec = self.base_spec

        # What the variant overrides, in the layout of the pack
        self.overlay = None

        if self.variant:

            self.overlay = self.root / "variants" / self.variant

            overlay_spec = self.overlay / "domain.yaml"

            if not overlay_spec.exists():
                raise FileNotFoundError(
                    f"Unknown variant {name!r}: {overlay_spec} not found. "
                    f"Available: {', '.join(list_domains()) or 'none'}"
                )

            self.spec = deep_merge(self.base_spec, _read_yaml(overlay_spec))

        self.description = " ".join(str(self.spec.get("description", "")).split())

        # Language of the conversations; engine/languages.py holds what the
        # engine has to know about it.
        self.language = self.spec.get("language", "en")

        self.language_rules = language_rules(self.language)

        # A translated variant must not fall back to the pack's phrases: the
        # dataset would silently mix two languages.
        self.translated = (
            self.language != self.base_spec.get("language", "en")
        )

        self.config_file = (self.overlay or self.root) / "config.yaml"

        self.robot_context = {
            **self.language_rules["wording"],
            **(self.spec.get("robot_context") or {}),
        }

        self.generated_id_pattern = re.compile(
            self.spec.get("generated_id_pattern") or NO_MATCH
        )

        self.module = self._import_module()

        self.generators = {
            **SHARED_GENERATORS,
            "weekday": self.weekday,
            **getattr(self.module, "GENERATORS", {}),
        }


    def _import_module(self):

        if not (self.root / "__init__.py").exists():
            return None

        folder = self.root.parent.resolve()

        if folder not in [path.resolve() for path in DOMAIN_DIRS]:
            raise ValueError(
                f"{self.root} has Python hooks but is outside "
                f"{', '.join(map(str, DOMAIN_DIRS))}; they can only be "
                f"imported from there"
            )

        # Packs of every domain folder import as
        # synthetic_data_generator.domains.<name>, so their relative imports
        # work wherever the folder is.
        import synthetic_data_generator.domains as packs

        if str(folder) not in packs.__path__:
            packs.__path__.insert(0, str(folder))

        module = importlib.import_module(
            f"synthetic_data_generator.domains.{self.base_name}"
        )

        if Path(module.__file__).resolve().parent != self.root.resolve():
            raise ValueError(
                f"Domain {self.base_name!r} is defined twice with Python "
                f"hooks: {Path(module.__file__).parent} and {self.root}"
            )

        return module


    def _find(self, kind, relative):
        """The variant's file if it has one, otherwise the pack's."""

        if self.overlay:

            own = self.overlay / kind / relative

            if own.exists():
                return own

        return self.root / kind / relative


    # ---------- templates ----------

    def _all_templates(self):
        """Templates of the pack and the variant, without the removed ones."""

        folders = [self.root / "templates"]

        if self.overlay:
            folders.append(self.overlay / "templates")

        removed = self.spec.get("remove_templates") or []

        return sorted(
            (
                template_id
                for template_id in {
                    path.relative_to(folder).with_suffix("").as_posix()
                    for folder in folders
                    for path in folder.rglob("*.json")
                }
                if not any(
                    template_id == prefix or template_id.startswith(f"{prefix}/")
                    for prefix in removed
                )
            ),
            key=lambda template_id: template_id.split("/")
        )

    def templates(self):
        """Template ids (path below templates/ without .json), sorted. A
        translated variant has the templates it has phrases for; see
        translation_gaps for the others."""

        return [
            template_id for template_id in self._all_templates()
            if not self.translated or self.language_path(template_id).exists()
        ]

    def template_path(self, template_id):
        return self._find("templates", f"{template_id}.json")

    def template_paths(self):
        return [self.template_path(template_id) for template_id in self.templates()]

    def scenario_path(self, template_id):
        return self._find("scenarios", f"{template_id}.yaml")

    def language_path(self, template_id):

        relative = f"{template_id}.yaml"

        if self.translated:
            return self.overlay / "language" / relative

        return self._find("language", relative)

    def entity_path(self, entity_type):
        return self._find("entities", f"{entity_type}.yaml")

    def paths(self, template_id):
        """(scenario, template, language) arguments for generate_one."""

        return (
            str(self.scenario_path(template_id)),
            template_id,
            str(self.language_path(template_id)),
        )


    # ---------- configuration and tools ----------

    def load_config(self):
        """Read config.yaml (not cached - the optimizer rewrites it). A
        variant's settings go on top of the pack's, except the uniqueness
        caps: those were measured on the pack's phrases."""

        config_file = self.root / "config.yaml"

        config = _read_yaml(config_file) if config_file.exists() else {}

        if self.overlay:

            config.pop("uniqueness_caps", None)

            if self.config_file.exists():
                config = deep_merge(config, _read_yaml(self.config_file))

        return config

    @cached_property
    def tools(self):
        """{tool name: schema}. A file in the variant's tools/ patches the
        pack's tool of the same name (only what differs, e.g. translated
        descriptions; an argument set to null is removed) or adds a new
        tool; ``remove_tools`` in its domain.yaml drops one."""

        tools = load_tools(self.root / "tools")

        if not self.overlay:
            return tools

        removed = self.spec.get("remove_tools") or []

        merged = {
            name: schema for name, schema in tools.items()
            if name not in removed
        }

        for name, patch in load_tools(self.overlay / "tools").items():

            schema = deep_merge(merged.get(name, {}), patch)

            for section in ("input", "output"):

                if schema.get(section):
                    schema[section] = {
                        key: spec for key, spec in schema[section].items()
                        if spec is not None
                    }

            merged[name] = schema

        return merged


    # ---------- language ----------

    def weekday(self):
        """A weekday in the domain's language (the shared generator's
        ``weekday`` key and ``today``)."""

        return random.choice(self.language_rules["weekdays"])

    def translation_gaps(self):
        """What a translated variant still has in the pack's language: no
        phrases for a template, text inherited from a template, a tool or
        the system message wording. Empty for anything not translated."""

        if not self.translated:
            return []

        gaps = []

        for template_id in self._all_templates():

            if not self.language_path(template_id).exists():
                gaps.append(f"template {template_id}: no language file (skipped)")

            elif not (self.overlay / "templates" / f"{template_id}.json").exists():

                messages = json.loads(
                    self.template_path(template_id).read_text(encoding="utf-8")
                ).get("messages", [])

                if any(
                    isinstance(message.get("content"), str)
                    and message.get("role") != "tool"
                    and re.search(r"\w", PLACEHOLDER.sub("", message["content"]))
                    for message in messages
                ):
                    gaps.append(f"template {template_id}: literal text in the template")

        base_tools = load_tools(self.root / "tools")

        for name, schema in sorted(self.tools.items()):

            base = base_tools.get(name) or {}

            if schema.get("description") and schema["description"] == base.get("description"):
                gaps.append(f"tool {name}: description")

            for argument, spec in (schema.get("input") or {}).items():

                inherited = (base.get("input") or {}).get(argument) or {}

                if spec.get("description") and spec["description"] == inherited.get("description"):
                    gaps.append(f"tool {name}: description of {argument}")

        def wording_gaps(wording, base, where):

            for key, text in wording.items():

                if isinstance(text, dict):
                    wording_gaps(text, (base or {}).get(key), f"{where}.{key}")

                elif text and text == (base or {}).get(key):
                    gaps.append(f"domain.yaml: {where}.{key}")

        wording_gaps(
            self.spec.get("robot_context") or {},
            self.base_spec.get("robot_context"),
            "robot_context"
        )

        return gaps


    # ---------- Python hooks ----------

    def create_validators(self):

        factory = getattr(self.module, "create_validators", None)

        return factory(self) if factory else []

    def finish_context(self, context, scenario):
        """After all entities exist, before the system message is built:
        for what depends on several entities (a home that contains them)."""

        hook = getattr(self.module, "finish_context", None)

        if hook:
            hook(context, scenario)

    def postprocess(self, datapoint):
        """The rendered conversation, before validation. May raise ValueError
        for a draw this domain cannot use; it is redrawn."""

        hook = getattr(self.module, "postprocess", None)

        return hook(datapoint, self) if hook else datapoint

    def refresh_entity(self, entity):

        hook = getattr(self.module, "refresh_entity", None)

        if hook:
            hook(entity)


    def __repr__(self):
        return f"Domain({self.name!r})"


def list_domains():
    """Names of all domain packs (folders with a domain.yaml) and of their
    variants ("<domain>@<variant>")."""

    packs = {
        path.parent.name
        for folder in DOMAIN_DIRS
        for path in folder.glob("*/domain.yaml")
    }

    variants = [
        f"{pack}{VARIANT_SEPARATOR}{path.parent.name}"
        for pack in packs
        for path in find_pack(pack).glob("variants/*/domain.yaml")
    ]

    return sorted([*packs, *variants])


def find_pack(base_name):
    """The folder of the domain pack ``base_name``: the first one in
    DOMAIN_DIRS. If none exists, where it would be in the project."""

    for folder in DOMAIN_DIRS:

        root = folder / base_name

        if (root / "domain.yaml").exists():
            return root

    return DOMAIN_DIRS[0] / base_name


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
        raise RuntimeError(
            f"No domain packs found in {', '.join(map(str, DOMAIN_DIRS))}"
        )

    return domains[0]


def resolve_domain(domain):
    """Accept a Domain, a domain name or None (default domain)."""

    if isinstance(domain, Domain):
        return domain

    return load_domain(domain or default_domain())
