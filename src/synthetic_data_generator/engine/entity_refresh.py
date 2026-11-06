class EntityRefresher:
    """Recompute derived fields after constraints changed an entity."""


    def __init__(self, domain_hook=None):

        # The domain's refresh_entity(entity), e.g. the hospital domain
        # redraws an appointment location that no longer fits its type.
        self.domain_hook = domain_hook



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


        if self.domain_hook:
            self.domain_hook(entity)
