from pathlib import Path

from synthetic_data_generator.engine.dataset_generator import DatasetGenerator


from synthetic_data_generator.engine.domain import load_domain

# Generate one template of one domain. The template id is its path below
# domains/<domain>/templates/, including the category subfolder.
DOMAIN = "hospital"

yamls = "patient_identity/identical_patients"

NUM_DATASETS = 50

OUTPUT_DIR = f"Synthetic_Data/{DOMAIN}/{Path(yamls).name}"

GENERATOR_VERSION = "0.2.0"

RANDOM_SEED = 42

domain = load_domain(DOMAIN)

generator = DatasetGenerator(RANDOM_SEED, domain=domain)



generator.generate_many(

    scenario=str(domain.scenario_path(yamls)),

    template=f"{yamls}",

    amount=NUM_DATASETS,

    output_dir=OUTPUT_DIR,

    language_schema=str(domain.language_path(yamls))
)