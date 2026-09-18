#!/usr/bin/env python3
"""Push approved merged datasets under Datasets/ to a HuggingFace Hub repo.

Nothing is published unless it is explicitly listed in
config/publish_config.yaml under `approved_datasets` - generating or merging
a dataset does not make it eligible on its own. See documentation/publishing.md.
"""

import argparse
import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATASETS_DIR = PROJECT_ROOT / "Datasets"
PUBLISH_CONFIG_FILE = PROJECT_ROOT / "config" / "publish_config.yaml"


def load_publish_config():

    with open(PUBLISH_CONFIG_FILE, "r") as f:
        return yaml.safe_load(f)


def resolve_targets(requested_dataset, config):
    """Return the list of dataset folder names to publish.

    Every returned name is guaranteed to be in `approved_datasets` - this is
    the one gate that decides whether something can be pushed at all.
    """

    approved = set(config.get("approved_datasets") or [])

    if requested_dataset is not None:

        if requested_dataset not in approved:
            raise ValueError(
                f"'{requested_dataset}' is not in approved_datasets in "
                f"{PUBLISH_CONFIG_FILE.relative_to(PROJECT_ROOT)} - add it "
                f"there first if you've reviewed it and want it published."
            )

        return [requested_dataset]

    return sorted(approved)


def publish_dataset(name, config, dry_run):

    dataset_dir = DATASETS_DIR / name

    if not dataset_dir.is_dir():
        raise FileNotFoundError(
            f"Approved dataset '{name}' has no folder at {dataset_dir}"
        )

    repo_id = config.get("hf_repo_id")

    if not repo_id:
        raise ValueError(
            "hf_repo_id is not set in "
            f"{PUBLISH_CONFIG_FILE.relative_to(PROJECT_ROOT)} - "
            "set it to '<your-username>/<dataset-name>' first."
        )

    private = bool(config.get("private", False))

    print(
        f"{'[dry run] ' if dry_run else ''}"
        f"Publishing {dataset_dir.relative_to(PROJECT_ROOT)} "
        f"-> hub:{repo_id} (path_in_repo='{name}', private={private})"
    )

    if dry_run:
        return

    from huggingface_hub import HfApi

    api = HfApi()

    api.create_repo(
        repo_id=repo_id,
        repo_type="dataset",
        private=private,
        exist_ok=True,
    )

    api.upload_folder(
        repo_id=repo_id,
        repo_type="dataset",
        folder_path=str(dataset_dir),
        path_in_repo=name,
        commit_message=f"Publish {name}",
    )

    print(f"Done: https://huggingface.co/datasets/{repo_id}/tree/main/{name}")


def main(argv=None):

    parser = argparse.ArgumentParser(
        description=(
            "Push an approved Datasets/<name> folder to HuggingFace Hub. "
            "With no --dataset, publishes every entry in approved_datasets."
        )
    )

    parser.add_argument(
        "--dataset",
        help="A single Datasets/<name> folder to publish. Must already be "
             "listed in approved_datasets.",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be published without uploading anything.",
    )

    args = parser.parse_args(argv)

    config = load_publish_config()

    try:
        targets = resolve_targets(args.dataset, config)
    except ValueError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    if not targets:
        print("Nothing to publish: approved_datasets is empty.")
        return 0

    for name in targets:

        try:
            publish_dataset(name, config, args.dry_run)

        except (FileNotFoundError, ValueError) as error:
            print(f"Error: {error}", file=sys.stderr)
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
