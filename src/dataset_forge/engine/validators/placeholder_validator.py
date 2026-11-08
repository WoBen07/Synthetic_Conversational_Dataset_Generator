import re


PLACEHOLDER = re.compile(r"\{\{.*?\}\}")


class PlaceholderValidator:

    def validate(self, datapoint):

        errors = []

        self._walk(
            datapoint,
            errors
        )

        return errors


    def _walk(
        self,
        value,
        errors,
        path=""
    ):

        if isinstance(value, dict):

            for key, val in value.items():

                self._walk(
                    val,
                    errors,
                    f"{path}.{key}"
                )


        elif isinstance(value, list):

            for i, item in enumerate(value):

                self._walk(
                    item,
                    errors,
                    f"{path}[{i}]"
                )


        elif isinstance(value, str):

            if PLACEHOLDER.search(value):

                errors.append(

                    f"Unresolved placeholder at {path}: {value}"

                )