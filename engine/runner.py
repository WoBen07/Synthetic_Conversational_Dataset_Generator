from pathlib import Path

from synthetic_data_generator.engine.dataset_generator import DatasetGenerator


# path relative to schemas/scenarios and schemas/language,
# including the category subfolder
yamls = "patient_identity/identical_patients"

NUM_DATASETS = 50

# output stays flat, keyed by the template's own name
OUTPUT_DIR = f"Synthetic_Data/{Path(yamls).name}"

GENERATOR_VERSION = "0.2.0"

RANDOM_SEED = 42

generator = DatasetGenerator(RANDOM_SEED)



generator.generate_many(

    scenario=f"schemas/scenarios/{yamls}.yaml",

    template=f"{yamls}",

    amount=NUM_DATASETS,

    output_dir=OUTPUT_DIR,

    language_schema=f"schemas/language/{yamls}.yaml"
)