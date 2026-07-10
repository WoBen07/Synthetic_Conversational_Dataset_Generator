from .placeholder_validator import PlaceholderValidator
from .structure_validator import StructureValidator
from .tool_validator import ToolValidator
from .pronoun_validator import PronounValidator


class Validator:

    def __init__(self):

        self.validators = [

            StructureValidator(),

            PlaceholderValidator(),

            ToolValidator(),

            PronounValidator()

        ]


    def validate(self, datapoint):

        errors = []

        for validator in self.validators:

            errors.extend(
                validator.validate(datapoint)
            )

        return errors