class WeatherRecommendationValidator:


    WARM_CLOTHING = [
        "jacket",
        "coat",
        "warm",
        "gloves",
        "scarf",
        "boots",
        "layers",
        "sweater",
        "thermal"
    ]


    RAIN_PROTECTION = [
        "umbrella",
        "raincoat",
        "waterproof",
        "rain jacket",
        "water-resistant"
    ]


    HOT_PROTECTION = [
        "water",
        "hydration",
        "sunscreen",
        "hat",
        "light clothing",
        "shorts",
        "t-shirt"
    ]


    WIND_PROTECTION = [
        "jacket",
        "coat",
        "layer",
        "windbreaker"
    ]


    COLD_CONDITIONS = [
        "snow",
        "snowy",
        "snowfall",
        "snowstorm",
        "icy",
        "freezing"
    ]


    RAIN_CONDITIONS = [
        "rain",
        "rainy",
        "drizzle",
        "shower",
        "thunderstorm",
        "stormy",
        "freezing rain",
        "hail"
    ]


    WIND_CONDITIONS = [
        "windy",
        "stormy",
        "breezy",
        "thunderstorm"
    ]


    DRY_CONDITIONS = [
        "sunny",
        "clear",
        "warm and sunny",
        "hot and dry",
        "foggy",
        "misty",
        "cloudy",
        "overcast"
    ]


    def extract_temperature(self, weather):

        temperature = weather.get(
            "temperature",
            ""
        )

        try:
            return int(
                temperature
                .replace("°C", "")
                .strip()
            )

        except:
            return None



    def contains_any(
        self,
        text,
        keywords
    ):

        return any(
            keyword in text
            for keyword in keywords
        )



    def validate(self, datapoint):

        errors = []

        messages = datapoint.get(
            "messages",
            []
        )


        #
        # Extract weather tool output
        #

        try:

            weather = next(
                message.get("content", {})
                for message in messages
                if message.get("role") == "tool"
                and message.get("name") == "get_weather"
            )


        except StopIteration:

            return errors



        #
        # Extract final assistant answer
        #

        try:

            recommendation = next(
                message.get("content", "")
                for message in reversed(messages)
                if message.get("role") == "assistant"
                and message.get("content")
            ).lower()


        except StopIteration:

            return errors



        condition = weather.get(
            "condition",
            ""
        ).lower()


        temperature = self.extract_temperature(
            weather
        )



        #
        # TEMPERATURE RULES
        #

        if temperature is not None:


            #
            # Cold
            #

            if temperature <= 10:

                if not self.contains_any(
                    recommendation,
                    self.WARM_CLOTHING
                ):

                    errors.append(
                        "Cold temperature without warm clothing recommendation"
                    )



            #
            # Hot
            #

            if temperature >= 30:


                if self.contains_any(
                    recommendation,
                    self.WARM_CLOTHING
                ):

                    errors.append(
                        "Warm clothing recommended during hot weather"
                    )


                if not self.contains_any(
                    recommendation,
                    self.HOT_PROTECTION
                ):

                    errors.append(
                        "Hot weather without heat protection advice"
                    )



        #
        # RAIN / STORM RULES
        #

        is_rain = self.contains_any(
            condition,
            self.RAIN_CONDITIONS
        )


        if is_rain:


            if not self.contains_any(
                recommendation,
                self.RAIN_PROTECTION
            ):

                errors.append(
                    "Rain or storm without rain protection recommendation"
                )



        #
        # DRY WEATHER CONTRADICTIONS
        #

        is_dry = self.contains_any(
            condition,
            self.DRY_CONDITIONS
        )


        if is_dry:


            if self.contains_any(
                recommendation,
                self.RAIN_PROTECTION
            ):

                errors.append(
                    "Rain protection recommended during dry weather"
                )



        #
        # WIND RULES
        #

        is_windy = self.contains_any(
            condition,
            self.WIND_CONDITIONS
        )


        if is_windy:


            if not self.contains_any(
                recommendation,
                self.WIND_PROTECTION
            ):

                errors.append(
                    "Windy weather without wind protection"
                )



        #
        # SNOW / ICE RULES
        #

        is_cold_condition = self.contains_any(
            condition,
            self.COLD_CONDITIONS
        )


        if is_cold_condition:


            if not self.contains_any(
                recommendation,
                self.WARM_CLOTHING
            ):

                errors.append(
                    "Snow or ice without warm clothing recommendation"
                )


        return errors