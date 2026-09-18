# Publishing to HuggingFace Hub

`engine/publish_to_hub.py` pushes a merged dataset folder (`Datasets/<name>/`)
to a HuggingFace Hub dataset repo. Nothing is published automatically -
every run must find the target in `approved_datasets`.

## One-time setup

1. Create a HuggingFace account at https://huggingface.co if you don't have
   one.
2. Install the dependency: `pip install huggingface_hub` (or
   `pip install -r requirements.txt` from the project root). If your system
   Python is externally managed (Debian/Ubuntu), create a virtual
   environment first:
   ```
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
3. Create an access token at https://huggingface.co/settings/tokens (a
   "Write" token, since this pushes data) and log in once from the
   terminal:
   ```
   huggingface-cli login
   ```
   This stores the token locally so `publish_to_hub.py` can authenticate
   without you passing a secret around. Alternatively set the `HF_TOKEN`
   environment variable instead of logging in interactively.

## Approving a dataset for publishing

Edit `config/publish_config.yaml`:

```yaml
hf_repo_id: "your-username/hospital-robot-hri"
private: false
approved_datasets:
  - Test_Dataset_9
```

Only folder names listed under `approved_datasets` can ever be pushed -
adding a folder here is a deliberate, manual decision, not something the
generator or merger does for you.

## Publishing

```
# publish every entry in approved_datasets
python -m synthetic_data_generator.engine.publish_to_hub

# publish just one (it must already be in approved_datasets)
python -m synthetic_data_generator.engine.publish_to_hub --dataset Test_Dataset_9

# see what would happen without uploading anything
python -m synthetic_data_generator.engine.publish_to_hub --dry-run
```

Each approved dataset is uploaded under its own folder in the repo
(`<repo>/<dataset_name>/...`), so multiple dataset versions can coexist in
one HuggingFace repo.

## From the orchestrator

`engine/orchestrator.py --publish` runs the full generate-and-merge flow and
then publishes whatever is already in `approved_datasets`. It does not add
anything to that list itself - review `Datasets/<name>/` first, then edit
the config, then run with `--publish` (or run `publish_to_hub.py` on its
own after the fact). Add `--dry-run-publish` alongside `--publish` to see
what would be pushed without uploading.
