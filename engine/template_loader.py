from pathlib import Path
import json


class TemplateLoader:

    def __init__(self):

        # synthetic_data_generator/
        self.base_path = (
            Path(__file__)
            .resolve()
            .parent
            .parent
        )


    def load(self, name):

        path = self.base_path / "templates" / f"{name}.json"

        if not path.exists():
            raise FileNotFoundError(
                f"Template not found: {path}"
            )

        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)