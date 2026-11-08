import random


WEATHER_PROFILES = [

    {
        "conditions": [
            "Sunny",
            "Clear",
            "Partly cloudy",
            "Warm and sunny"
        ],
        "temperatures": [
            "18°C",
            "20°C",
            "22°C",
            "25°C",
            "28°C"
        ]
    },

    {
        "conditions": [
            "Hot and dry",
            "Humid"
        ],
        "temperatures": [
            "30°C",
            "32°C",
            "35°C",
            "38°C",
            "40°C"
        ]
    },

    {
        "conditions": [
            "Cloudy",
            "Overcast",
            "Foggy",
            "Misty"
        ],
        "temperatures": [
            "8°C",
            "10°C",
            "12°C",
            "15°C",
            "18°C",
            "20°C"
        ]
    },

    {
        "conditions": [
            "Rainy",
            "Light rain",
            "Heavy rain",
            "Drizzle"
        ],
        "temperatures": [
            "5°C",
            "8°C",
            "10°C",
            "12°C",
            "15°C",
            "18°C",
            "20°C"
        ]
    },

    {
        "conditions": [
            "Thunderstorm",
            "Stormy",
            "Windy",
            "Breezy"
        ],
        "temperatures": [
            "10°C",
            "12°C",
            "15°C",
            "18°C",
            "20°C"
        ]
    },

    {
        "conditions": [
            "Cold and cloudy",
            "Icy"
        ],
        "temperatures": [
            "-5°C",
            "-3°C",
            "-1°C",
            "0°C",
            "2°C",
            "4°C",
            "6°C",
            "8°C"
        ]
    },

    {
        "conditions": [
            "Snowy",
            "Light snowfall",
            "Heavy snowfall",
            "Snowstorm"
        ],
        "temperatures": [
            "-15°C",
            "-12°C",
            "-10°C",
            "-8°C",
            "-5°C",
            "-3°C",
            "0°C"
        ]
    },

    {
        "conditions": [
            "Freezing rain",
            "Hail"
        ],
        "temperatures": [
            "-5°C",
            "-3°C",
            "0°C",
            "2°C"
        ]
    }
]


# Shared state for one generated weather instance
_current_profile = None


def _select_profile():
    global _current_profile

    _current_profile = random.choice(
        WEATHER_PROFILES
    )



def condition():
    global _current_profile

    if _current_profile is None:
        _select_profile()

    return random.choice(
        _current_profile["conditions"]
    )



def temperature():
    global _current_profile

    if _current_profile is None:
        _select_profile()

    temp = random.choice(
        _current_profile["temperatures"]
    )

    # Reset after temperature was generated
    _current_profile = None

    return temp