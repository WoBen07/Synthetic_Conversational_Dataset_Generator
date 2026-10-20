"""Validators of the hospital domain (run in addition to the engine's)."""

from .weather_recommendation_validator import WeatherRecommendationValidator
from .weather_consistency_validator import WeatherConsistencyValidator
from .weather_grounding_validator import WeatherGroundingValidator


def create_validators():

    return [
        WeatherRecommendationValidator(),
        WeatherConsistencyValidator(),
        WeatherGroundingValidator(),
    ]
