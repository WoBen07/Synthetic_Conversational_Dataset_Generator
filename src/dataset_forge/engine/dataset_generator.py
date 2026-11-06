import hashlib
import json
import logging
import re
from pathlib import Path
from datetime import datetime
import random

from dataset_forge.engine.metadata import MetadataWriter
from dataset_forge.engine.config import GENERATOR_VERSION
from dataset_forge.engine.language_generator import LanguageGenerator
from dataset_forge.engine.schemaloader import SchemaLoader

from dataset_forge.engine.scenario_builder import ScenarioBuilder
from dataset_forge.engine.template_loader import TemplateLoader
from dataset_forge.engine.template_renderer import TemplateRenderer
from dataset_forge.engine.conversation_normalizer import normalize_conversation
from dataset_forge.engine.datapoint_metadata import build_metadata
from dataset_forge.engine.domain import resolve_domain
from dataset_forge.engine.validators.validator import Validator


# Regenerations and skipped datapoints. The command line prints these to
# stdout (log.configure_cli_logging); the GUI parses those lines.
logger = logging.getLogger(__name__)


def conversation_fingerprint(datapoint, generated_id):
    """Hash of the conversation with generated IDs masked.

    Generated IDs differ in every datapoint (the domain's
    generated_id_pattern), so they are masked - otherwise no two
    datapoints would ever count as duplicates.
    """

    text = json.dumps(
        datapoint.get("messages", []),
        sort_keys=True,
        ensure_ascii=False
    )

    return hashlib.sha1(
        generated_id.sub("<id>", text).encode("utf-8")
    ).hexdigest()


class DatasetGenerator:


    def __init__(self, random_seed, domain=None):

        self.random_seed = random_seed

        if random_seed is not None:
            random.seed(random_seed)

        # A Domain, a domain name, or None for the default domain
        self.domain = resolve_domain(domain)

        self.template_loader = TemplateLoader(self.domain.template_path)

        self.metadata_writer = MetadataWriter()
        self.schemaloader = SchemaLoader()
        self.validator = Validator(self.domain)


    def generate_one(
        self,
        scenario,
        template,
        language_schema_template
    ):

        datapoint, _trace = self.generate_one_traced(
            scenario,
            template,
            language_schema_template
        )

        return datapoint



    def generate_one_traced(
        self,
        scenario,
        template,
        language_schema_template
    ):
        """Like generate_one, but also return which language option was
        chosen per variable, which of them the template actually used,
        and the size of every phrase pool."""

        #
        # Generate context
        #

        scenario_builder = ScenarioBuilder(
            scenario,
            self.domain
        )

        context = scenario_builder.generate()


        language_schema = self.schemaloader.load(
            language_schema_template
        )


        language_generator = LanguageGenerator(
            language_schema
        )


        language_context = language_generator.generate()


        context.update(
            language_context
        )



        #
        # Load template
        #

        template_data = self.template_loader.load(
            template
        )



        #
        # Render
        #

        renderer = TemplateRenderer(
            context,
            fix_articles=self.domain.language_rules["english_articles"]
        )


        rendered = renderer.render(
            template_data
        )


        #
        # Normalize conversation flow
        #
        # Fold any consecutive assistant messages into one so the datapoint
        # renders into strictly alternating chat-template turns.
        #

        used_variables = {
            path.split(".")[0]
            for path in renderer.used_paths
        } & set(language_generator.choices)

        trace = {

            "choices": {
                name: language_generator.choices[name]
                for name in used_variables
            },

            "pool_sizes": {
                name: len(options)
                for name, options in language_schema["variables"].items()
            },
        }

        return self.domain.postprocess(
            normalize_conversation(
                rendered
            )
        ), trace



    def template_hash(self, scenario, template, language_schema):
        """Short hash of the template's three files: datapoints with the same
        hash come from identical template, scenario and language files."""

        digest = hashlib.sha256()

        for path in (scenario, self.domain.template_path(template), language_schema):
            digest.update(Path(path).read_bytes())

        return digest.hexdigest()[:12]


    def iter_datapoints(
        self,
        scenario,
        template,
        language_schema,
        amount,
        stats=None
    ):
        """Yield up to ``amount`` valid, non-duplicate datapoints with their
        ``metadata``. Invalid datapoints are regenerated; a template that
        keeps failing stops early. ``stats`` (a dict), if given, receives
        the counts "generated", "skipped" and "duplicates_rejected"."""

        stats = stats if stats is not None else {}
        stats.update(generated=0, skipped=0, duplicates_rejected=0)

        consecutive_skips = 0

        max_attempts_per_datapoint = 50

        # A template whose datapoints keep failing (broken template, or a
        # phrase pool that is exhausted by deduplication) would otherwise
        # loop forever, since a skip does not advance the count.
        max_consecutive_skips = 5

        seen = set()

        tags = self.schemaloader.load(scenario).get("tags", [])

        template_hash = self.template_hash(scenario, template, language_schema)


        while stats["generated"] < amount:

            attempts = 0
            datapoint = None
            errors = None


            while attempts < max_attempts_per_datapoint:

                attempts += 1

                try:

                    datapoint, trace = self.generate_one_traced(
                        scenario,
                        template,
                        language_schema
                    )


                except ValueError as error:

                    logger.info(
                        "Regenerating datapoint after generation error: %s", error
                    )

                    continue



                errors = self.validator.validate(
                    datapoint
                )


                if errors:

                    logger.info("[%s] %s", template, errors)
                    logger.info(
                        "Regenerating datapoint after validation error."
                    )

                    continue


                fingerprint = conversation_fingerprint(
                    datapoint,
                    self.domain.generated_id_pattern
                )

                if fingerprint in seen:

                    stats["duplicates_rejected"] += 1

                    # Not an error, but it must not be written twice.
                    errors = ["duplicate"]

                    continue


                seen.add(fingerprint)


                # Added after validation, so validators only ever see
                # the conversation itself.
                datapoint["metadata"] = build_metadata(
                    datapoint,
                    self.domain,
                    template,
                    trace["choices"],
                    tags,
                    template_hash=template_hash
                )


                # Valid datapoint found
                break



            #
            # Failed after max attempts
            #

            if datapoint is None or errors:

                stats["skipped"] += 1

                consecutive_skips += 1

                logger.warning(
                    "[%s] Skipping datapoint after %d failed attempts.",
                    template, max_attempts_per_datapoint
                )

                if consecutive_skips >= max_consecutive_skips:

                    logger.warning(
                        "[%s] Giving up after %d datapoints: %d datapoints in "
                        "a row could not be generated (template broken or "
                        "phrase pool exhausted).",
                        template, stats["generated"], consecutive_skips
                    )

                    return

                continue


            consecutive_skips = 0

            stats["generated"] += 1

            yield datapoint



    def generate_many(
        self,
        scenario,
        template,
        amount,
        output_dir,
        language_schema
    ):
        """Write ``amount`` datapoints to output_dir/example_NNNNN.json and a
        metadata.json describing the run."""


        output_path = Path(
            output_dir
        )

        output_path.mkdir(
            parents=True,
            exist_ok=True
        )

        # Generating replaces the template's data. Files of an earlier, larger
        # run would otherwise stay and be merged with the new ones.
        for stale in output_path.glob("example_*.json"):
            stale.unlink()


        stats = {}

        datapoints = self.iter_datapoints(
            scenario,
            template,
            language_schema,
            amount,
            stats
        )

        for index, datapoint in enumerate(datapoints):

            filename = (
                output_path /
                f"example_{index:05d}.json"
            )


            with open(
                filename,
                "w",
                encoding="utf-8"
            ) as file:

                json.dump(
                    datapoint,
                    file,
                    indent=2,
                    ensure_ascii=False
                )


            print(
                f"Generated {filename}"
            )


        metadata = {

            "generator_version": GENERATOR_VERSION,

            "generated_at": datetime.now().isoformat(),

            "domain": self.domain.name,

            "language": self.domain.language,

            "scenario": scenario,

            "template": template,

            "template_hash": self.template_hash(scenario, template, language_schema),

            "amount": amount,

            "generated": stats["generated"],

            "skipped": stats["skipped"],

            "duplicates_rejected": stats["duplicates_rejected"],

            "random_seed": self.random_seed
        }


        self.metadata_writer.write(
            output_dir,
            metadata
        )
