#!/usr/bin/env python3

import json
import random
from pathlib import Path
from collections import defaultdict


# ==========================
# Configuration
# ==========================


PROJECT_ROOT = Path(__file__).resolve().parents[1]


INPUT_FOLDER = PROJECT_ROOT / "Synthetic_Data"
OUTPUT_FOLDER = PROJECT_ROOT / "Datasets" / "Test_Dataset_2"
TRAIN_OUTPUT = "train.jsonl"
VALIDATION_OUTPUT = "validation.jsonl"

VALIDATION_SPLIT = 0.1

RANDOM_SEED = 42

SHUFFLE = True


# ==========================
# Loading
# ==========================

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_dataset_by_template(input_folder):

    root = Path(input_folder)

    datasets = defaultdict(list)

    folders = [
        f for f in root.iterdir()
        if f.is_dir()
    ]

    for folder in folders:

        metadata_file = folder / "metadata.json"

        if not metadata_file.exists():
            print(
                f"Skipping {folder}: no metadata.json"
            )
            continue

        metadata = load_json(metadata_file)

        template = metadata.get("template")

        if template is None:
            print(
                f"Skipping {folder}: no template field"
            )
            continue

        json_files = [
            f for f in folder.glob("*.json")
            if f.name != "metadata.json"
        ]

        for json_file in json_files:

            try:
                datapoint = load_json(json_file)

                if "messages" not in datapoint:
                    print(
                        f"Skipping {json_file}: no messages"
                    )
                    continue

                datasets[template].append(datapoint)

            except Exception as e:
                print(
                    f"Failed loading {json_file}: {e}"
                )


        expected = metadata.get("amount")

        if expected is not None:
            actual = len(datasets[template])

            if actual != expected:
                print(
                    f"WARNING: {template}: "
                    f"metadata says {expected}, "
                    f"found {actual}"
                )


    return datasets



# ==========================
# Stratified split
# ==========================

def write_metadata(path, metadata):

    with open(path, "w", encoding="utf-8") as f:
        json.dump(
            metadata,
            f,
            indent=2,
            ensure_ascii=False
        )

def stratified_split(datasets):

    train = []
    validation = []

    random.seed(RANDOM_SEED)


    for template, samples in datasets.items():

        print(
            f"{template}: {len(samples)} samples"
        )


        if SHUFFLE:
            random.shuffle(samples)


        val_count = max(
            1,
            int(len(samples) * VALIDATION_SPLIT)
        )


        val_samples = samples[:val_count]
        train_samples = samples[val_count:]


        train.extend(train_samples)
        validation.extend(val_samples)


        print(
            f"  train={len(train_samples)}, "
            f"validation={len(val_samples)}"
        )


    if SHUFFLE:
        random.shuffle(train)
        random.shuffle(validation)


    return train, validation



# ==========================
# Writing
# ==========================

def write_jsonl(path, data):

    path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(path, "w", encoding="utf-8") as f:

        for item in data:

            f.write(
                json.dumps(
                    item,
                    ensure_ascii=False
                )
                + "\n"
            )



# ==========================
# Main
# ==========================

def main():

    output_folder = Path(OUTPUT_FOLDER)

    train_output = (
        output_folder / TRAIN_OUTPUT
    )

    validation_output = (
        output_folder / VALIDATION_OUTPUT
    )


    print("Loading datasets...")
    datasets = load_dataset_by_template(
        INPUT_FOLDER
    )


    print("\nSplitting datasets...")
    train, validation = stratified_split(
        datasets
    )


    print("\nWriting files...")

    write_jsonl(
        train_output,
        train
    )

    write_jsonl(
        validation_output,
        validation
    )

    metadata = {
        "generator": "dataset_merger",
        "input_folder": str(INPUT_FOLDER),
        "output_folder": str(OUTPUT_FOLDER),

        "random_seed": RANDOM_SEED,
        "shuffle": SHUFFLE,

        "validation_split": VALIDATION_SPLIT,

        "templates": {
            template: {
                "total": len(samples),
                "validation": max(
                    1,
                    int(len(samples) * VALIDATION_SPLIT)
                ),
                "train": len(samples) - max(
                    1,
                    int(len(samples) * VALIDATION_SPLIT)
                )
            }
            for template, samples in datasets.items()
        },

        "total_samples": {
            "all": len(train) + len(validation),
            "train": len(train),
            "validation": len(validation)
        }
    }


    metadata_file = output_folder / "metadata.json"

    write_metadata(
        metadata_file,
        metadata
    )


    print("\nFinished")
    print("====================")
    print(f"Output:     {output_folder}")
    print(f"Total:      {len(train)+len(validation)}")
    print(f"Train:      {len(train)}")
    print(f"Validation: {len(validation)}")
    print("====================")


if __name__ == "__main__":
    main()