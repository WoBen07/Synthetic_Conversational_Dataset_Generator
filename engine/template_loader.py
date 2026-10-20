from pathlib import Path
import json


class TemplateLoader:

    def __init__(self, template_dir):

        # domains/<name>/templates/
        self.template_dir = Path(template_dir)


    def load(self, name):

        path = self.template_dir / f"{name}.json"

        if not path.exists():
            raise FileNotFoundError(
                f"Template not found: {path}"
            )

        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)
