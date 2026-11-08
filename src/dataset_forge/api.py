"""Python API: generate datapoints in memory, without the file pipeline.

    from dataset_forge import Forge

    forge = Forge("hospital", seed=42)

    forge.templates                     # ["conversational/boredom_check_in", ...]
    forge.tools                         # OpenAI-style function definitions

    for datapoint in forge.generate("tool_use/patient_reminder", n=5):
        print(datapoint["messages"], datapoint["metadata"])

    everything = list(forge.generate_all(n=10))   # 10 per template

Every datapoint is a dict with ``messages`` and ``metadata`` (see
engine/datapoint_metadata.py), exactly as the command line writes them.

Seeds: a new Forge with the same seed and domain, making the same calls
with the same package version, gives the same datapoints. Each template's seed is derived from the Forge's seed and the
template's name, as in ``dforge generate``. Generation seeds Python's
global ``random`` module, so code using it alongside is affected.

Log messages (regenerated and skipped datapoints) go to the
``dataset_forge`` logger; nothing is printed.
"""

from dataset_forge.engine import orchestrator
from dataset_forge.engine.dataset_generator import DatasetGenerator
from dataset_forge.engine.domain import Domain, load_domain
from dataset_forge.engine.tool_definitions import tool_definitions


class Forge:

    def __init__(self, domain, seed=None):
        """``domain``: a domain name ("hospital", "home_assistant@hass") or a
        Domain. ``seed``: an int for reproducible output; None draws a fresh
        one, available as ``self.seed``."""

        self.domain = domain if isinstance(domain, Domain) else load_domain(domain)

        self.config = orchestrator.load_config()

        self.seed = orchestrator.create_seed(self.config) if seed is None else int(seed)

        self.domain.reset_state()


    def __repr__(self):
        return f"Forge({self.domain.name!r}, seed={self.seed})"


    @property
    def templates(self):
        """Template ids of the domain, e.g. "tool_use/patient_reminder"."""

        return self.domain.templates()


    @property
    def tools(self):
        """The domain's tools as OpenAI-style function definitions."""

        return tool_definitions(self.domain)


    def planned_amounts(self):
        """{template id: amount} as ``dforge generate`` would produce them:
        the domain's config.yaml with uniqueness caps and tool-share
        targets applied."""

        return orchestrator.plan_amounts(self.domain, verbose=False)


    def generate(self, template, n=1):
        """Yield up to ``n`` valid, distinct datapoints of one template.
        Fewer come out only if the template cannot produce more (broken, or
        its phrase pools are exhausted); that is logged as a warning."""

        if template not in self.templates:
            raise KeyError(
                f"{self.domain.name} has no template {template!r}; see "
                f"Forge.templates"
            )

        generator = DatasetGenerator(
            orchestrator.template_seed(self.seed, self.domain.name, template, self.config),
            domain=self.domain,
        )

        scenario, template_id, language = self.domain.paths(template)

        yield from generator.iter_datapoints(scenario, template_id, language, n)


    def generate_all(self, n=None, templates=None):
        """Yield datapoints of every template (or of ``templates``) in turn.

        ``n``: an int (per template), a {template id: amount} dict, or None
        for the planned amounts (``planned_amounts()``)."""

        selected = list(templates) if templates is not None else self.templates

        if n is None:
            amounts = self.planned_amounts()
        elif isinstance(n, int):
            amounts = dict.fromkeys(selected, n)
        else:
            amounts = n

        for template in selected:
            yield from self.generate(template, amounts.get(template, 0))
