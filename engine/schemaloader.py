from pathlib import Path
import yaml


class SchemaLoader:


    def __init__(self):

        # project root:
        # synthetic_data_generator/
        self.base_path = (
            Path(__file__)
            .resolve()
            .parent
            .parent
        )


    def load(self, relative_path):

        path = (
            self.base_path /
            relative_path
        )


        if not path.exists():

            raise FileNotFoundError(
                f"Schema not found: {path}"
            )


        with open(
            path,
            "r",
            encoding="utf-8"
        ) as file:

            return yaml.safe_load(file)