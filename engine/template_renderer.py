import re


PLACEHOLDER_PATTERN = re.compile(
    r"\{\{(.*?)\}\}"
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

            return result



        result = value


        for match in matches:

            replacement = self._lookup(match)


            if isinstance(replacement, str):

                replacement = self._render_string(
                    replacement,
                    depth + 1
                )


            result = result.replace(
                "{{" + match + "}}",
                str(replacement)
            )


        return result



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