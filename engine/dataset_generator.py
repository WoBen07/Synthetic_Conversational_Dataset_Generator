import json
from pathlib import Path
from datetime import datetime

from synthetic_data_generator.engine.metadata import MetadataWriter
from synthetic_data_generator.engine.config import GENERATOR_VERSION, RANDOM_SEED
from synthetic_data_generator.engine.language_generator import LanguageGenerator
from synthetic_data_generator.engine.schemaloader import SchemaLoader

from synthetic_data_generator.engine.scenario_builder import ScenarioBuilder
from synthetic_data_generator.engine.template_loader import TemplateLoader
from synthetic_data_generator.engine.template_renderer import TemplateRenderer
from synthetic_data_generator.engine.validators.validator import Validator


class DatasetGenerator:


    def __init__(self):

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


        return renderer.render(
            template_data
        )



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
        attempts = 0
        max_attempts = max(amount * 100, 1)


        while index < amount:

            attempts += 1

            if attempts > max_attempts:

                raise RuntimeError(
                    "Failed to generate a valid datapoint after "
                    f"{attempts - 1} attempts"
                )


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

                print(errors)
                print(
                    "Regenerating datapoint after validation error."
                )

                continue


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

            "random_seed": RANDOM_SEED

        }


        self.metadata_writer.write(
            output_dir,
            metadata
        )