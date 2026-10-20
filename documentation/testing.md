# Tests

The tests use `unittest` from the standard library (pytest runs them as
well). Run them from inside `synthetic_data_generator/`:

```bash
python -m unittest discover -s tests
```

or from the directory above:

```bash
python -m unittest discover -s synthetic_data_generator/tests
```

The whole suite takes about a second. GitHub Actions runs it on every
push and pull request (`.github/workflows/tests.yml`).

## What is covered

| file | checks |
|---|---|
| `test_text_and_rendering.py` | `a`/`an` rules, doubled words, renderer (article fix, nested placeholders, entity insertion without phrasing fields, recorded paths), language choices keep the random sequence |
| `test_scenarios.py` | constraints, location redraw, separate room pools, `today` constraint, `robot_context` wording |
| `test_validators.py` | grounding (IDs, search terms, copied reasons, articles in rooms), structure rules, language validator |
| `test_dataset.py` | uniqueness optimizer maths, datapoint metadata, grouped split without overlap, `generate_many` output |
| `test_templates.py` | every template has its scenario and language file, all placeholders and tools exist, `robot_context` declared where used, no two user/tool messages in a row, every template produces a valid datapoint, fixed-seed output |

## Golden outputs

`test_templates.GoldenOutputTest` renders three templates with a fixed
seed and compares them with `tests/golden/`. When it fails, the
generated data changed. If the change is intended (new phrases, a fix),
rewrite the files and commit them with the change:

```bash
UPDATE_GOLDEN=1 python -m unittest discover -s tests -k Golden
```

## Adding tests

New templates are covered automatically by `test_templates.py`. For a
new engine feature, add a test file `tests/test_<topic>.py` and start it
with `import helpers`, which makes the package importable and provides
`generate_valid()`, `reset_generators()` and `conversation()`.
