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
OUTPUT_FOLDER = PROJECT_ROOT / "Datasets" / "Test_Dataset_9"
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
# Conversation-flow lint
# ==========================

def assert_strict_role_alternation(datasets):
    """Fail loudly if any datapoint has two consecutive messages with the
    same role.

    Runs over the full generated corpus as a last line of defence: the
    renderer already folds consecutive assistant turns, so a hit here means
    that step regressed and the dataset must not be written.
    """

    violations = []

    for template, samples in datasets.items():

        template_file = f"templates/{template}.json"

        for sample_index, datapoint in enumerate(samples):

            messages = datapoint.get("messages", [])

            for i in range(1, len(messages)):

                if messages[i].get("role") == messages[i - 1].get("role"):

                    violations.append(
                        f"{template} (sample {sample_index}): "
                        f"consecutive '{messages[i].get('role')}' at "
                        f"messages {i - 1}/{i} - check {template_file}"
                    )

    if violations:

        preview = "\n".join(f"  - {v}" for v in violations[:20])

        more = (
            f"\n  ... and {len(violations) - 20} more"
            if len(violations) > 20
            else ""
        )

        raise RuntimeError(
            f"Conversation-flow lint failed: {len(violations)} datapoint(s) "
            f"have consecutive same-role messages.\n{preview}{more}"
        )

    print(
        f"Conversation-flow lint OK: "
        f"{sum(len(s) for s in datasets.values())} datapoints, "
        f"strictly alternating roles."
    )


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

def wording_key(datapoint, index):
    """Group key for the split: datapoints with the same wording_id read
    the same apart from names, rooms and days. Datapoints generated
    before metadata existed get a key of their own."""

    metadata = datapoint.get("metadata") or {}

    return metadata.get("wording_id") or f"__no_wording_id_{index}"


def split_template(samples, rng):
    """Split one template into (train, validation) by wording.

    Whole wording groups go to validation until it holds about
    VALIDATION_SPLIT of the samples, so validation never contains a
    datapoint whose wording was also seen in training - with a plain
    random split most validation datapoints had a training twin that
    differed only in the names.
    """

    target = max(1, int(len(samples) * VALIDATION_SPLIT))

    groups = defaultdict(list)

    for index, datapoint in enumerate(samples):
        groups[wording_key(datapoint, index)].append(datapoint)

    keys = list(groups)

    if SHUFFLE:
        rng.shuffle(keys)

    train = []
    validation = []

    for key in keys:

        group = groups[key]

        # A group never goes to validation if that would leave training
        # with less than the rest of the template.
        if len(validation) < target and len(group) <= len(samples) - target:
            validation.extend(group)
        else:
            train.extend(group)

    return train, validation


def stratified_split(datasets):
    """Split every template on its own (stratified), grouped by wording.

    Returns (train, validation, counts) with counts per template.
    """

    rng = random.Random(RANDOM_SEED)

    train = []
    validation = []
    counts = {}

    for template, samples in datasets.items():

        train_samples, val_samples = split_template(samples, rng)

        train.extend(train_samples)
        validation.extend(val_samples)

        counts[template] = {
            "total": len(samples),
            "train": len(train_samples),
            "validation": len(val_samples),
        }

        print(
            f"{template}: {len(samples)} samples, "
            f"train={len(train_samples)}, validation={len(val_samples)}"
        )

        if not val_samples:
            print(
                f"  WARNING: no validation samples - the template has too "
                f"few distinct wordings to split without overlap"
            )

    if SHUFFLE:
        rng.shuffle(train)
        rng.shuffle(validation)

    return train, validation, counts


def wording_overlap(train, validation):
    """Number of validation datapoints whose wording_id is also in train."""

    train_ids = {
        (d.get("metadata") or {}).get("wording_id")
        for d in train
    } - {None}

    return sum(
        1 for d in validation
        if (d.get("metadata") or {}).get("wording_id") in train_ids
    )



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


    print("\nLinting conversation flow...")
    assert_strict_role_alternation(datasets)


    print("\nSplitting datasets...")
    train, validation, counts = stratified_split(
        datasets
    )

    overlap = wording_overlap(train, validation)

    print(
        f"Wording overlap between train and validation: {overlap} "
        f"validation datapoint(s)"
    )

    without_metadata = sum(
        1 for d in train + validation if "metadata" not in d
    )

    if without_metadata:
        print(
            f"WARNING: {without_metadata} datapoint(s) have no metadata "
            f"(generated by an older version) and are split without "
            f"wording groups - regenerate them for a leak-free split."
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

        "split": "stratified by template, grouped by metadata.wording_id",

        "wording_overlap": overlap,

        "templates": counts,

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