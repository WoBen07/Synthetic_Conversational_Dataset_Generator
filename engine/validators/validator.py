from .placeholder_validator import PlaceholderValidator
from .structure_validator import StructureValidator
from .tool_validator import ToolValidator
from .conversation_flow_validator import ConversationFlowValidator
from .pronoun_validator import PronounValidator
from .weather_consistency_validator import WeatherConsistencyValidator
from .weather_recommendation_validator import WeatherRecommendationValidator
from .weather_grounding_validator import WeatherGroundingValidator
from .grounding_validator import GroundingValidator
from .tool_schema_validator import ToolSchemaValidator
from .language_validator import LanguageValidator

class Validator:

    def __init__(self):

        self.validators = [

            StructureValidator(),

            PlaceholderValidator(),

            ToolValidator(),

            ConversationFlowValidator(),

            PronounValidator(),

            WeatherRecommendationValidator(),

            WeatherConsistencyValidator(),

            WeatherGroundingValidator(),

            ToolSchemaValidator(),

            GroundingValidator(),

            LanguageValidator()

        ]


    def validate(self, datapoint):

        errors = []

        for validator in self.validators:

            errors.extend(
                validator.validate(datapoint)
            )

        return errors