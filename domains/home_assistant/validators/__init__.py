"""Validators of the home_assistant domain."""

from .light_capability_validator import LightCapabilityValidator
from .security_confirmation_validator import SecurityConfirmationValidator


def create_validators(domain=None):

    return [LightCapabilityValidator(), SecurityConfirmationValidator()]
