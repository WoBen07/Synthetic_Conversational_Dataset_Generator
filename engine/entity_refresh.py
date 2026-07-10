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