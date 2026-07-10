class PronounValidator:


    def validate(self, datapoint):

        errors = []

        patient = datapoint.get("patient")

        if not patient:
            return errors


        text = self._extract_text(datapoint)


        if patient["gender"] == "male":

            if " her " in text.lower():

                errors.append(
                    "Male patient referenced with female pronoun"
                )


        if patient["gender"] == "female":

            if " his " in text.lower():

                errors.append(
                    "Female patient referenced with male pronoun"
                )


        return errors



    def _extract_text(self, datapoint):

        return " ".join(
            m["content"]
            for m in datapoint["messages"]
            if "content" in m
        )