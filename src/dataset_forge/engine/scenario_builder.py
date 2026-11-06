from dataset_forge.engine.schemaloader import SchemaLoader
from dataset_forge.engine.entity import EntityBuilder
from dataset_forge.engine.constraint_resolver import ConstraintResolver
from dataset_forge.engine.entity_refresh import EntityRefresher
from dataset_forge.engine.linguistic_resolver import LinguisticResolver
from dataset_forge.engine.robot_context import build_robot_context
from dataset_forge.engine.domain import resolve_domain






class ScenarioBuilder:


    def __init__(self, scenario_path, domain=None):

        self.domain = resolve_domain(domain)
        self.loader = SchemaLoader()
        self.constraint_resolver = ConstraintResolver()
        self.entity_refresher = EntityRefresher(self.domain.refresh_entity)
        self.linguistic_resolver = LinguisticResolver(
            self.domain.language_rules["pronouns"]
        )
        self.scenario = (
            self.loader.load(
                scenario_path
            )
        )



    def generate(self):

        context = {}

        # The current weekday. Scenarios whose phrases say "today" tie
        # an appointment to it with an equal constraint
        # ([today, appointment.day]); robot_context states it.
        context["today"] = self.domain.weekday()

        #
        # Generate all entities
        #
        for name, entity in self.scenario["entities"].items():

            entity_schema = self.loader.load(
                self.domain.entity_path(entity["type"])
            )

            builder = EntityBuilder(entity_schema, self.domain.generators)

            context[name] = builder.create()

        #
        # Create aliases
        #
        aliases = self.scenario.get("aliases", {})

        for alias, target in aliases.items():

            if target not in context:
                raise ValueError(
                    f"Alias '{alias}' refers to unknown entity '{target}'"
                )

            context[alias] = context[target]

        constraints = self.scenario.get(
            "constraints",
            []
        )


        context = self.constraint_resolver.resolve(
            context,
            constraints
        )


        context = self.entity_refresher.refresh(
            context
        )

        # Refreshing can redraw a location, so check the "different"
        # constraints once more.
        self.constraint_resolver.check_different(
            context,
            constraints
        )

        context = self.linguistic_resolver.resolve(
            context
        )

        self.domain.finish_context(
            context,
            self.scenario
        )

        robot_context = self.scenario.get("robot_context")

        if robot_context is not None:

            context["robot_context"] = build_robot_context(
                context,
                robot_context,
                self.domain.robot_context
            )


        return context


