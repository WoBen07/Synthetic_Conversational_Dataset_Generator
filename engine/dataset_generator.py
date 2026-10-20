import hashlib
import json
import re
from pathlib import Path
from datetime import datetime
import random

from synthetic_data_generator.engine.metadata import MetadataWriter
from synthetic_data_generator.engine.config import GENERATOR_VERSION, RANDOM_SEED
from synthetic_data_generator.engine.language_generator import LanguageGenerator
from synthetic_data_generator.engine.schemaloader import SchemaLoader

from synthetic_data_generator.engine.scenario_builder import ScenarioBuilder
from synthetic_data_generator.engine.template_loader import TemplateLoader
from synthetic_data_generator.engine.template_renderer import TemplateRenderer
from synthetic_data_generator.engine.conversation_normalizer import normalize_conversation
from synthetic_data_generator.engine.validators.validator import Validator


# Generated IDs differ in every datapoint, so they are masked before
# comparing conversations - otherwise no two datapoints would ever count
# as duplicates.
GENERATED_ID = re.compile(r"\b[pa]\d+\b")


def conversation_fingerprint(datapoint):

    text = json.dumps(
        datapoint.get("messages", []),
        sort_keys=True,
        ensure_ascii=False
    )

    return hashlib.sha1(
        GENERATED_ID.sub("<id>", text).encode("utf-8")
    ).hexdigest()


class DatasetGenerator:


    def __init__(self, random_seed):

        self.random_seed = random_seed

        if random_seed is not None:
            random.seed(random_seed)

        self.template_loader = TemplateLoader()

        self.metadata_writer = MetadataWriter()
        self.schemaloader = SchemaLoader()
        self.validator = Validator()


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
            scenario
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
            context
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

        return normalize_conversation(
            rendered
        ), trace



    def generate_many(
        self,
        scenario,
        template,
        amount,
        output_dir,
        language_schema
    ):


        output_path = Path(
            output_dir
        )

        output_path.mkdir(
            parents=True,
            exist_ok=True
        )


        index = 0
        skipped = 0
        duplicates = 0
        consecutive_skips = 0

        max_attempts_per_datapoint = 50

        # A template whose datapoints keep failing (broken template, or a
        # phrase pool that is exhausted by deduplication) would otherwise
        # loop forever, since a skip does not advance the index.
        max_consecutive_skips = 5

        seen = set()


        while index < amount:

            attempts = 0
            datapoint = None


            while attempts < max_attempts_per_datapoint:

                attempts += 1

                try:

                    datapoint = self.generate_one(
                        scenario,
                        template,
                        language_schema
                    )


                except ValueError as error:

                    print(
                        f"Regenerating datapoint after generation error: {error}"
                    )

                    continue



                errors = self.validator.validate(
                    datapoint
                )


                if errors:

                    print(f"[{template}] {errors}")
                    print(
                        "Regenerating datapoint after validation error."
                    )

                    continue


                fingerprint = conversation_fingerprint(datapoint)

                if fingerprint in seen:

                    duplicates += 1

                    # Not an error, but it must not be written twice.
                    errors = ["duplicate"]

                    continue


                seen.add(fingerprint)


                # Valid datapoint found
                break



            #
            # Failed after max attempts
            #

            if datapoint is None or errors:

                skipped += 1

                consecutive_skips += 1

                print(
                    f"[{template}] Skipping datapoint after "
                    f"{max_attempts_per_datapoint} failed attempts."
                )

                if consecutive_skips >= max_consecutive_skips:

                    print(
                        f"[{template}] Giving up after {index} datapoints: "
                        f"{consecutive_skips} datapoints in a row could not "
                        f"be generated (template broken or phrase pool "
                        f"exhausted)."
                    )

                    break

                continue


            consecutive_skips = 0



            #
            # Save valid datapoint
            #

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


            index += 1
        metadata = {

            "generator_version": GENERATOR_VERSION,

            "generated_at": datetime.now().isoformat(),

            "scenario": scenario,

            "template": template,

            "amount": amount,

            "generated": index,

            "skipped": skipped,

            "duplicates_rejected": duplicates,

            "random_seed": RANDOM_SEED
        }


        self.metadata_writer.write(
            output_dir,
            metadata
        )