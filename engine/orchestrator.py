import os
import random
import subprocess
import yaml

from synthetic_data_generator.engine.dataset_generator import DatasetGenerator
from synthetic_data_generator.engine import dataset_merger
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


TEMPLATE_DIR = PROJECT_ROOT / "templates"
CONFIG_FILE = PROJECT_ROOT / "config" / "generation_config.yaml"

SCENARIO_DIR = PROJECT_ROOT / "schemas" / "scenarios"
LANGUAGE_DIR = PROJECT_ROOT / "schemas" / "language"

OUTPUT_ROOT = PROJECT_ROOT / "Synthetic_Data"

GENERATOR_VERSION = "0.2.0"


def load_config():
    with open(CONFIG_FILE, "r") as f:
        return yaml.safe_load(f)


def get_templates():

    templates = []

    for file in sorted(TEMPLATE_DIR.rglob("*.json")):

        relative = file.relative_to(TEMPLATE_DIR).with_suffix("")

        # POSIX-style id so it works the same as a lookup path
        # regardless of the subfolder it lives in, e.g.
        # "safety_and_refusals/medical_advice_refusal"
        templates.append(relative.as_posix())

    return templates


def get_amount(template_id, config):

    important = config.get("important_templates", {})

    # important_templates is keyed by the template's own name,
    # not its subfolder path, so look it up by the leaf name
    name = Path(template_id).name

    if name in important:
        return important[name]["amount"]

    return config["default_amount"]


def create_seed(config):

    seed_range = config["random_seed_range"]

    return random.randint(
        seed_range["min"],
        seed_range["max"]
    )


def run_template(template_id, amount, seed):

    print(
        f"\nGenerating {template_id}"
        f" | amount={amount}"
        f" | seed={seed}"
    )

    generator = DatasetGenerator(
        random_seed=seed
    )

    # Output stays flat, keyed by the template's own name, so the
    # subfolder grouping under templates/ and schemas/ doesn't
    # ripple into Synthetic_Data/ or the merger step.
    name = Path(template_id).name

    output_dir = (
        f"{OUTPUT_ROOT}/{name}"
    )

    generator.generate_many(

        scenario=f"{SCENARIO_DIR}/{template_id}.yaml",

        template=template_id,

        amount=amount,

        output_dir=output_dir,

        language_schema=f"{LANGUAGE_DIR}/{template_id}.yaml",

    )




def main():

    config = load_config()

    templates = get_templates()

    print(
        f"Found {len(templates)} templates:"
    )

    for t in templates:
        print(" -", t)


    for template in templates:

        amount = get_amount(
            template,
            config
        )

        seed = create_seed(
            config
        )

        run_template(
            template,
            amount,
            seed
        )


    # IMPORTANT:
    # Only called once after everything finished
    dataset_merger.main()


if __name__ == "__main__":
    main()