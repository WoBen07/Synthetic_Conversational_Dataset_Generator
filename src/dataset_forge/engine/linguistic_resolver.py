from dataset_forge.engine.languages import LANGUAGES


# Helpers for phrasing ("Ms. Weber"), not part of a patient record. The
# renderer leaves them out when a whole entity is inserted into a tool
# result, so find_patient output keeps its format.
PHRASING_ONLY_FIELDS = {"title", "title_last_name"}


class LinguisticResolver:


    def __init__(self, pronouns=None):

        # {gender: fields}, from engine/languages.py
        self.pronouns = pronouns or LANGUAGES["en"]["pronouns"]



    def resolve(self, context):

        for name, entity in context.items():

            if not isinstance(entity, dict):
                continue


            if "gender" in entity:

                self._add_pronouns(entity)


        return context



    def _add_pronouns(self, entity):

        entity.update(
            self.pronouns.get(entity["gender"], self.pronouns["other"])
        )


        # "Mr. Weber" - lets a phrase name a patient without the first
        # name, which is what makes a follow-up "which one?" plausible.
        if "last_name" in entity:

            entity["title_last_name"] = (
                f"{entity['title']} {entity['last_name']}".strip()
            )