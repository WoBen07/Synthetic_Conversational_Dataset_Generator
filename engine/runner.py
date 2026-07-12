from synthetic_data_generator.engine.dataset_generator import DatasetGenerator
from synthetic_data_generator.engine.config import NUM_DATASETS, OUTPUT_DIR



generator = DatasetGenerator()

yamls = "patient_toolcall3"

generator.generate_many(

    scenario=f"schemas/scenarios/{yamls}.yaml",

    template=f"{yamls}",

    amount=NUM_DATASETS,

    output_dir=OUTPUT_DIR,

    language_schema=f"schemas/language/{yamls}.yaml"
)