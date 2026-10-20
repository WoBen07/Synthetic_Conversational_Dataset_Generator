# Helpers for phrasing ("Ms. Weber"), not part of a patient record. The
# renderer leaves them out when a whole entity is inserted into a tool
# result, so find_patient output keeps its format.
PHRASING_ONLY_FIELDS = {"title", "title_last_name"}


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
            entity["title"] = "Mr."


        elif gender == "female":

            entity["pronoun"] = "she"
            entity["object_pronoun"] = "her"
            entity["possessive_pronoun"] = "her"
            entity["title"] = "Ms."


        else:

            entity["pronoun"] = "they"
            entity["object_pronoun"] = "them"
            entity["possessive_pronoun"] = "their"
            entity["title"] = "Mx."


        # "Mr. Weber" - lets a phrase name a patient without the first
        # name, which is what makes a follow-up "which one?" plausible.
        if "last_name" in entity:

            entity["title_last_name"] = (
                f"{entity['title']} {entity['last_name']}"
            )