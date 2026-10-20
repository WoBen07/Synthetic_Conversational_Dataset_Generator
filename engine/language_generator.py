import random


class LanguageGenerator:


    def __init__(self, schema):

        self.schema = schema

        # Index of the option chosen per variable in the last generate()
        # call - engine/config_optimizer.py uses it to tell datapoints
        # apart by wording rather than by entity values.
        self.choices = {}



    def generate(self):

        result = {}

        self.choices = {}

        variables = self.schema["variables"]


        for name, options in variables.items():

            # randrange consumes the RNG exactly like random.choice, so
            # seeded runs produce the same data as before.
            index = random.randrange(len(options))

            self.choices[name] = index

            result[name] = options[index]


        return result