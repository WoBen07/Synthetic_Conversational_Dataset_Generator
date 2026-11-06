import yaml


class ScenarioLoader:


    def load(self, path):

        with open(
            path,
            "r",
            encoding="utf-8"
        ) as file:

            return yaml.safe_load(file)