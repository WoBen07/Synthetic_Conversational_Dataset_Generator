from synthetic_data_generator.engine.dataset_generator import DatasetGenerator
from synthetic_data_generator.engine.config import NUM_DATASETS, OUTPUT_DIR



generator = DatasetGenerator()


generator.generate_many(

    scenario="schemas/scenarios/clarification_room.yaml",

    template="clarification_by_room",

    amount=NUM_DATASETS,

    output_dir=OUTPUT_DIR,

    language_schema="schemas/language/clarification_by_room.yaml"
)