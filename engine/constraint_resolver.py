class ConstraintResolver:


    def resolve(
        self,
        context,
        constraints
    ):

        for constraint in constraints:

            if constraint["type"] == "equal":

                self._resolve_equal(
                    context,
                    constraint["fields"]
                )


            elif constraint["type"] == "different":

                self._resolve_different(
                    context,
                    constraint["fields"]
                )


        return context



    def _resolve_equal(
        self,
        context,
        fields
    ):

        first = self._get_value(
            context,
            fields[0]
        )


        for field in fields[1:]:

            self._set_value(
                context,
                field,
                first
            )



    def _resolve_different(
        self,
        context,
        fields
    ):

        values = [
            self._get_value(context, field)
            for field in fields
        ]


        if len(set(values)) != len(values):

            raise ValueError(
                f"Constraint violated: {fields}"
            )



    def _get_value(
        self,
        context,
        path
    ):

        parts = path.split(".")

        value = context


        for part in parts:

            value = value[part]


        return value



    def _set_value(
        self,
        context,
        path,
        value
    ):

        parts = path.split(".")

        target = context


        for part in parts[:-1]:

            target = target[part]


        target[parts[-1]] = value