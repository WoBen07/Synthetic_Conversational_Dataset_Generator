from synthetic_data_generator.engine.text_utils import (
    article_mismatches,
    doubled_words,
)


# Free-text tool arguments the robot writes itself
TEXT_ARGUMENTS = ("message", "reason", "note")


class LanguageValidator:
    """Reject slot-filling grammar slips such as "an neurology
    appointment appointment" or "a MRI scan"."""

    def validate(self, datapoint):

        errors = []

        for index, message in enumerate(datapoint.get("messages", [])):

            for text in self._texts(message):

                for doubled in doubled_words(text):
                    errors.append(
                        f"Doubled word at {index}: {doubled!r}"
                    )

                for mismatch in article_mismatches(text):
                    errors.append(
                        f"Wrong article at {index}: {mismatch!r}"
                    )

        return errors


    def _texts(self, message):

        if message.get("role") == "tool":
            return []

        texts = []

        content = message.get("content")

        if isinstance(content, str):
            texts.append(content)

        call = message.get("tool_call") or {}

        arguments = call.get("arguments") or {}

        if isinstance(arguments, dict):

            for key in TEXT_ARGUMENTS:

                if isinstance(arguments.get(key), str):
                    texts.append(arguments[key])

        return texts
