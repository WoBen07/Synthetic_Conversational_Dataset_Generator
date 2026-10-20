from .placeholder_validator import PlaceholderValidator
from .structure_validator import StructureValidator
from .tool_validator import ToolValidator
from .conversation_flow_validator import ConversationFlowValidator
from .pronoun_validator import PronounValidator
from .tool_schema_validator import ToolSchemaValidator
from .grounding_validator import GroundingValidator
from .language_validator import LanguageValidator


class Validator:
    """Engine validators plus the domain's own (domain.create_validators)."""

    def __init__(self, domain):

        tools = domain.tools

        self.validators = [

            StructureValidator(),

            PlaceholderValidator(),

            ToolValidator(),

            ConversationFlowValidator(),

            PronounValidator(),

            *domain.create_validators(),

            ToolSchemaValidator(tools),

            GroundingValidator(tools),

            LanguageValidator()

        ]


    def validate(self, datapoint):

        errors = []

        for validator in self.validators:

            errors.extend(
                validator.validate(datapoint)
            )

        return errors
