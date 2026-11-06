from synthetic_data_generator.engine.text_utils import (
    ALLOWED_DOUBLES,
    article_mismatches,
    doubled_words,
)


# Free-text tool arguments the robot writes itself
TEXT_ARGUMENTS = ("message", "reason", "note")


class LanguageValidator:
    """Reject slot-filling grammar slips such as "an neurology
    appointment appointment" or "a MRI scan". The article check only
    makes sense for English text; doubled words are checked always."""

    def __init__(self, check_articles=True, allowed_doubles=ALLOWED_DOUBLES):

        self.check_articles = check_articles
        self.allowed_doubles = allowed_doubles


    def validate(self, datapoint):

        errors = []

        for index, message in enumerate(datapoint.get("messages", [])):

            for text in self._texts(message):

                for doubled in doubled_words(text, self.allowed_doubles):
                    errors.append(
                        f"Doubled word at {index}: {doubled!r}"
                    )

                if not self.check_articles:
                    continue

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
