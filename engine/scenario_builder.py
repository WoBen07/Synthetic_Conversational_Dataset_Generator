from synthetic_data_generator.engine.schemaloader import SchemaLoader
from synthetic_data_generator.engine.entity import EntityBuilder
from synthetic_data_generator.engine.constraint_resolver import ConstraintResolver
from synthetic_data_generator.engine.entity_refresh import EntityRefresher
from synthetic_data_generator.engine.linguistic_resolver import LinguisticResolver






class ScenarioBuilder:


    def __init__(self, scenario_path):

        self.loader = SchemaLoader()
        self.constraint_resolver = ConstraintResolver()
        self.entity_refresher = EntityRefresher()
        self.linguistic_resolver = LinguisticResolver()
        self.scenario = (
            self.loader.load(
                scenario_path
            )
        )



    def generate(self):

        context = {}

        #
        # Generate all entities
        #
        for name, entity in self.scenario["entities"].items():

            entity_schema = self.loader.load(
                f"schemas/entities/{entity['type']}.yaml"
            )

            builder = EntityBuilder(entity_schema)

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

        context = self.linguistic_resolver.resolve(
            context
        )


        return context


