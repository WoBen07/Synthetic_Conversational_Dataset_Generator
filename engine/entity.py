import re



class EntityBuilder:


    def __init__(self, schema, generators):

        self.schema = schema

        # {key: function} - the shared generators plus the domain's
        self.generators = generators



    def create(self):

        entity = {}


        # generate fields

        for field, config in self.schema["fields"].items():

            generator = self.generators[
                config["generator"]
            ]

            result = generator()


            # Generator returns metadata
            if isinstance(result, dict):

                entity[field] = result["value"]

                for key, value in result.items():

                    if key != "value":
                        entity[key] = value


            # Generator returns simple value
            else:

                entity[field] = result



        # computed fields

        if "computed" in self.schema:

            for field, config in self.schema["computed"].items():

                entity[field] = self.replace(
                    config["template"],
                    entity
                )


        return entity



    def replace(self, text, entity):

        matches = re.findall(
            r"\{\{(.*?)\}\}",
            text
        )


        for match in matches:

            text = text.replace(
                "{{"+match+"}}",
                str(entity[match])
            )


        return text