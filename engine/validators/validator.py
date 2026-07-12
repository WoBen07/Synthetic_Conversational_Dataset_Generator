from .placeholder_validator import PlaceholderValidator
from .structure_validator import StructureValidator
from .tool_validator import ToolValidator
from .pronoun_validator import PronounValidator
from .weather_consistency_validator import WeatherConsistencyValidator
from .weather_recommendation_validator import WeatherRecommendationValidator
from .weather_grounding_validator import WeatherGroundingValidator

class Validator:

    def __init__(self):

        self.validators = [

            StructureValidator(),

            PlaceholderValidator(),

            ToolValidator(),

            PronounValidator(),

            WeatherRecommendationValidator(),

            WeatherConsistencyValidator(),

            WeatherGroundingValidator()

        ]


    def validate(self, datapoint):

        errors = []

        for validator in self.validators:

            errors.extend(
                validator.validate(datapoint)
            )

        return errors