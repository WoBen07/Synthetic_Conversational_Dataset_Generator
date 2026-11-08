import re


class WeatherConsistencyValidator:

    COLD_WEATHER = [
        "snow",
        "snowy",
        "snowfall",
        "blizzard",
        "freezing",
        "icy",
        "frost"
    ]

    HOT_WEATHER = [
        "hot",
        "heat",
        "sunny"
    ]

    def validate(self, datapoint):

        errors = []

        try:
            tool_message = next(
                m for m in datapoint["messages"]
                if m.get("role") == "tool"
                and m.get("name") == "get_weather"
            )

        except StopIteration:
            return errors


        weather = tool_message.get("content", {})

        temperature = weather.get("temperature", "")
        condition = weather.get("condition", "").lower()


        match = re.search(r"-?\d+", temperature)

        if not match:
            return errors


        temp = int(match.group())


        # Snow / ice at high temperatures
        if any(
            word in condition
            for word in self.COLD_WEATHER
        ):

            if temp > 8:
                errors.append(
                    f"Invalid weather combination: {temp}°C with {condition}"
                )


        # Extreme heat with winter conditions
        if temp > 30:

            if any(
                word in condition
                for word in [
                    "freezing",
                    "icy",
                    "snow"
                ]
            ):

                errors.append(
                    f"Invalid hot weather combination: {temp}°C with {condition}"
                )


        # Thunderstorms during extreme cold
        if "thunderstorm" in condition and temp < -10:

            errors.append(
                f"Invalid thunderstorm temperature: {temp}°C"
            )


        return errors