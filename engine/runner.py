from synthetic_data_generator.engine.dataset_generator import DatasetGenerator


yamls = "unable_to_assist"

NUM_DATASETS = 50

OUTPUT_DIR = f"Synthetic_Data/{yamls}"

GENERATOR_VERSION = "0.2.0"

RANDOM_SEED = 42

generator = DatasetGenerator()



generator.generate_many(

    scenario=f"schemas/scenarios/{yamls}.yaml",

    template=f"{yamls}",

    amount=NUM_DATASETS,

    output_dir=OUTPUT_DIR,

    language_schema=f"schemas/language/{yamls}.yaml"
)