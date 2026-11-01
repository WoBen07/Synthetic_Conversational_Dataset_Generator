"""Validators of the home_assistant domain."""

from .light_capability_validator import LightCapabilityValidator


def create_validators(domain=None):

    return [LightCapabilityValidator()]
