import random

from synthetic_data_generator.generators.appointments import (
    TYPE_LOCATIONS,
    locations_for,
)


class EntityRefresher:


    def refresh(self, context):

        for name, entity in context.items():

            if not isinstance(entity, dict):
                continue


            self._refresh_entity(entity)


        return context



    def _refresh_entity(self, entity):

        if (
            "first_name" in entity
            and "last_name" in entity
        ):

            entity["full_name"] = (
                f"{entity['first_name']} "
                f"{entity['last_name']}"
            )


        # An "equal" constraint can copy one appointment's type onto
        # another whose location was drawn for a different type. Draw a
        # fitting location again so type and room never contradict.
        appointment_type = entity.get("appointment_type")

        if (
            appointment_type in TYPE_LOCATIONS
            and "location" in entity
        ):

            allowed = locations_for(appointment_type)

            if entity["location"] not in allowed:

                entity["location"] = random.choice(allowed)
