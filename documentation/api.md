# Python API

Generate datapoints in memory, without the file pipeline of
`dforge generate` (no `Synthetic_Data/`, no merge):

```python
from dataset_forge import Forge

forge = Forge("hospital", seed=42)

forge.templates            # template ids, e.g. "tool_use/patient_reminder"
forge.tools                # the domain's tools as OpenAI-style function definitions
forge.planned_amounts()    # {template: amount} as dforge generate would make them

for datapoint in forge.generate("tool_use/patient_reminder", n=5):
    print(datapoint["messages"])
    print(datapoint["metadata"])

ten_each = list(forge.generate_all(n=10))
as_planned = list(forge.generate_all())
some = list(forge.generate_all(n={"tool_use/patient_reminder": 3}, templates=["tool_use/patient_reminder"]))
```

`Forge(domain, seed=None)`:

- `domain`: a name (`"hospital"`, `"home_assistant@hass"`, a project or
  installed pack) or a `Domain`. Domains are looked up as described in
  [the project folder](overview.md#project-folder); set
  `DFORGE_PROJECT_DIR` before importing `dataset_forge` to use another
  project's domains.
- `seed`: an int for reproducible output. `None` draws a fresh one,
  available as `forge.seed`.

`generate(template, n)` yields up to `n` valid, distinct datapoints -
fewer only if the template cannot produce more, which is logged as a
warning. Each datapoint is a dict with `messages` and `metadata`, the
same as the files `dforge generate` writes.

## Reproducibility

A new `Forge` with the same seed and domain, making the same calls with
the same package version, returns the same datapoints. Each template's
seed is derived from the Forge seed exactly as in
[`dforge generate`](workflow.md#reproducibility). Generation seeds
Python's global `random` module, so other code using `random` in the same
process is affected.

## Logging

Nothing is printed. Regenerated datapoints are logged at `INFO` and
skipped ones at `WARNING` on the `dataset_forge` logger:

```python
import logging
logging.basicConfig(level=logging.INFO)
```

## Other entry points

`dataset_forge.list_domains()` and `dataset_forge.load_domain(name)` list
and load domains. The engine modules (`dataset_forge.engine.*`) are
importable as well, but are not a stable interface yet.
