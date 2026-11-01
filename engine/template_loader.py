import json


class TemplateLoader:

    def __init__(self, template_path):

        # Template id -> file (Domain.template_path: a variant's own
        # template if it has one, otherwise the pack's)
        self.template_path = template_path


    def load(self, name):

        path = self.template_path(name)

        if not path.exists():
            raise FileNotFoundError(
                f"Template not found: {path}"
            )

        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)
