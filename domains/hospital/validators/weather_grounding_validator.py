class WeatherGroundingValidator:


    WEATHER_CLAIMS = {
        "rain": [
            "rain",
            "rainy",
            "wet",
            "drizzle",
            "shower",
            "storm",
            "thunderstorm"
        ],

        "snow": [
            "snow",
            "snowy",
            "snowfall",
            "snowstorm"
        ],

        "cold": [
            "cold",
            "chilly",
            "freezing",
            "icy"
        ],

        "hot": [
            "hot",
            "heat",
            "warm",
            "sunny"
        ]
    }


    WEATHER_SUPPORT = {
        "rain": [
            "rain",
            "rainy",
            "drizzle",
            "shower",
            "storm",
            "thunderstorm"
        ],

        "snow": [
            "snow",
            "snowy",
            "snowfall",
            "snowstorm"
        ],

        "cold": [
            "cold",
            "icy",
            "freezing",
            "snow"
        ],

        "hot": [
            "hot",
            "warm",
            "sunny"
        ]
    }


    def contains_any(self, text, words):

        return any(
            word in text
            for word in words
        )


    def validate(self, datapoint):

        errors = []

        messages = datapoint.get(
            "messages",
            []
        )


        try:

            weather = next(
                m["content"]
                for m in messages
                if m.get("role") == "tool"
                and m.get("name") == "get_weather"
            )


            response = next(
                m["content"].lower()
                for m in reversed(messages)
                if m.get("role") == "assistant"
                and "content" in m
            )


        except StopIteration:

            return errors



        actual_weather = (
            weather.get("condition", "")
            + " "
            + weather.get("temperature", "")
        ).lower()



        for claim, words in self.WEATHER_CLAIMS.items():

            if self.contains_any(
                response,
                words
            ):

                if not self.contains_any(
                    actual_weather,
                    self.WEATHER_SUPPORT[claim]
                ):

                    errors.append(
                        f"Assistant claimed {claim} weather without tool support"
                    )


        return errors