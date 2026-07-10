import random


class LanguageGenerator:


    def __init__(self, schema):

        self.schema = schema



    def generate(self):

        result = {}

        variables = self.schema["variables"]


        for name, options in variables.items():

            result[name] = random.choice(options)


        return result