import re

from synthetic_data_generator.engine.linguistic_resolver import PHRASING_ONLY_FIELDS
from synthetic_data_generator.engine.text_utils import article_for


PLACEHOLDER_PATTERN = re.compile(
    r"\{\{(.*?)\}\}"
)

# A standalone "a"/"an" directly in front of a placeholder
ARTICLE_BEFORE_PLACEHOLDER = re.compile(
    r"(?:^|(?<=[\s(\"“'—–-]))([Aa]n?) $"
)


class TemplateRenderer:


    def __init__(self, context):

        self.context = context



    def render(self, template):

        return self._render_value(template)



    def _render_value(self, value):

        # dictionaries
        if isinstance(value, dict):

            return {
                key: self._render_value(val)
                for key, val in value.items()
            }


        # lists
        elif isinstance(value, list):

            return [
                self._render_value(item)
                for item in value
            ]


        # strings
        elif isinstance(value, str):

            return self._render_string(value)


        # numbers, bools, None
        else:

            return value



    def _render_string(self, value, depth=0):

        if depth > 10:
            raise RuntimeError(
                "Maximum template recursion depth exceeded"
            )


        matches = PLACEHOLDER_PATTERN.findall(value)


        if not matches:
            return value


        # Whole value is a placeholder
        if (
            len(matches) == 1
            and value.strip() == "{{" + matches[0] + "}}"
        ):

            result = self._lookup(matches[0])


            # recursively render generated strings
            if isinstance(result, str):
                return self._render_string(
                    result,
                    depth + 1
                )

            # A whole entity (e.g. a find_patient match) carries only
            # its record fields, not the phrasing helpers.
            if isinstance(result, dict):
                return {
                    key: value
                    for key, value in result.items()
                    if key not in PHRASING_ONLY_FIELDS
                }

            return result



        parts = []
        position = 0


        for found in PLACEHOLDER_PATTERN.finditer(value):

            replacement = self._lookup(found.group(1))


            if isinstance(replacement, str):

                replacement = self._render_string(
                    replacement,
                    depth + 1
                )


            replacement = str(replacement)

            parts.append(value[position:found.start()])

            parts = self._fix_article(parts, replacement)

            parts.append(replacement)

            position = found.end()


        parts.append(value[position:])


        return "".join(parts)



    def _fix_article(self, parts, replacement):

        # Phrases are written as "a {{appointment.appointment_type}}",
        # so the article has to follow whatever gets inserted
        # ("an MRI scan", "an eye examination").
        before = "".join(parts)

        article = ARTICLE_BEFORE_PLACEHOLDER.search(before)

        if not article or not replacement:
            return parts

        fitting = article_for(
            replacement,
            capitalized=article.group(1)[0] == "A"
        )

        return [
            before[:article.start(1)] + fitting + before[article.end(1):]
        ]



    def _lookup(self, path):

        parts = path.split(".")


        current = self.context


        for part in parts:

            if part not in current:

                raise KeyError(
                    f"Missing template variable: {path}"
                )


            current = current[part]


        return current