"""``dforge init``: set up a project folder.

    dforge init my-project
    dforge init my-project --domain retail_store   # with a first domain pack

See documentation/overview.md#project-folder.
"""

import argparse
import sys
from pathlib import Path

GENERATION_CONFIG = """\
# Settings of this project, merged key by key over the defaults that ship
# with dataset_forge (dataset_forge/config/generation_config.yaml).

# Domains generated when no --domain is given. Empty: every domain -
# yours in domains/, installed packs and the built-in ones.
domains: [{domains}]

# Folder below Datasets/ for the merged train/validation files.
merged_dataset: dataset

# Run seed for reproducible runs (or pass --seed). Empty: a fresh one per
# run, printed and stored in Datasets/<merged_dataset>/metadata.json.
seed:
"""

PUBLISH_EXAMPLE = """\
# Hugging Face Hub target for `dforge publish`. Copy this file to
# config/publish_config.yaml (git-ignored) and fill it in.
hf_repo_id:          # e.g. "your-username/your-dataset"
private: true

# Only folders listed here (under Datasets/) can be published.
approved_datasets: []
"""

GITIGNORE = """\
Synthetic_Data/
Datasets/
config/publish_config.yaml
"""

README = """\
# {name}

A [Dataset Forge](https://pypi.org/project/python-dataset-forge/) project.

```bash
dforge domains        # available domains
dforge new-domain NAME
dforge generate       # domains from config/generation_config.yaml
dforge gui
```

- `domains/`: this project's domain packs
- `config/`: settings
- `Synthetic_Data/`, `Datasets/`: generated output (git-ignored)
"""


def init_project(path, domain=None, description="Describe the domain here."):
    """Create the project folder ``path`` (it may exist, but must not be a
    project yet) and return the files written."""

    path = Path(path)
    config = path / "config" / "generation_config.yaml"

    if config.exists():
        raise FileExistsError(f"{path} is already a project ({config} exists)")

    files = {
        config: GENERATION_CONFIG.format(domains=domain or ""),
        path / "config" / "publish_config.example.yaml": PUBLISH_EXAMPLE,
        path / ".gitignore": GITIGNORE,
        path / "README.md": README.format(name=path.resolve().name),
        path / "domains" / ".gitkeep": "",
    }

    written = []

    for file, content in files.items():

        # Never replace a README or .gitignore that is already there
        if file.exists():
            continue

        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(content, encoding="utf-8")
        written.append(file)

    if domain:

        from dataset_forge.engine.new_domain import create_domain

        written.append(create_domain(domain, description, path / "domains"))

    return written


def main(argv=None):

    parser = argparse.ArgumentParser(description="Set up a project folder.")
    parser.add_argument("path", nargs="?", default=".", help="folder (default: current)")
    parser.add_argument("--domain", metavar="NAME", help="also create a first domain pack")
    parser.add_argument("--description", default="Describe the domain here.")

    args = parser.parse_args(argv)

    for file in init_project(args.path, args.domain, args.description):
        print(f"Created {file}")

    where = "" if args.path == "." else f"cd {args.path} && "

    print(f"\nNext: {where}dforge generate" + (f" --domain {args.domain}" if args.domain else ""))

    return 0


if __name__ == "__main__":
    sys.exit(main())
