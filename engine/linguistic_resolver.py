class LinguisticResolver:


    def resolve(self, context):

        for name, entity in context.items():

            if not isinstance(entity, dict):
                continue


            if "gender" in entity:

                self._add_pronouns(entity)


        return context



    def _add_pronouns(self, entity):

        gender = entity["gender"]


        if gender == "male":

            entity["pronoun"] = "he"
            entity["object_pronoun"] = "him"
            entity["possessive_pronoun"] = "his"


        elif gender == "female":

            entity["pronoun"] = "she"
            entity["object_pronoun"] = "her"
            entity["possessive_pronoun"] = "her"


        else:

            entity["pronoun"] = "they"
            entity["object_pronoun"] = "them"
            entity["possessive_pronoun"] = "their"