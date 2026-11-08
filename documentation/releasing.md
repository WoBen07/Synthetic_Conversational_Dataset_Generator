# Releasing to PyPI

`.github/workflows/release.yml` builds the package, tests the built wheel
and uploads it with PyPI trusted publishing - no API token is stored
anywhere.

| Trigger | Publishes to |
|---|---|
| pushing a tag `vX.Y.Z` | PyPI, then a GitHub release with the built files |
| "Run workflow" on the Actions tab | TestPyPI (a dry run; can be repeated) |

A tag must match `__version__` in `src/dataset_forge/__init__.py`,
otherwise the workflow stops before uploading anything.

## One-time setup

1. **PyPI account.** Create accounts on https://pypi.org and
   https://test.pypi.org (they are separate) and enable two-factor
   authentication.
2. **Trusted publishers.** The project does not exist yet, so add a
   *pending* publisher on both sites: Account settings > Publishing >
   "Add a new pending publisher" > GitHub, with

   | field | PyPI | TestPyPI |
   |---|---|---|
   | PyPI project name | `python-dataset-forge` | `python-dataset-forge` |
   | Owner | `WoBen07` | `WoBen07` |
   | Repository name | `Synthetic_Conversational_Dataset_Generator` | same |
   | Workflow name | `release.yml` | `release.yml` |
   | Environment name | `pypi` | `testpypi` |

   The first successful upload creates the project and turns the pending
   publisher into a normal one. If the GitHub repository is renamed,
   update the publisher, or uploads fail.
3. **GitHub environments.** In the repository: Settings > Environments >
   create `pypi` and `testpypi`. For `pypi`, add yourself under "Required
   reviewers", so every release waits for your approval before it uploads.

## Making a release

1. Set the version in `src/dataset_forge/__init__.py` (the package, the
   CLI's `--version` and the datapoints' `generator_version` all read it)
   and merge to `main`.
2. Optional dry run: Actions > release > Run workflow (on `main`), then
   check https://test.pypi.org/project/python-dataset-forge/ and try
   ```bash
   pip install -i https://test.pypi.org/simple/ \
       --extra-index-url https://pypi.org/simple/ python-dataset-forge
   ```
3. Tag and push:
   ```bash
   git tag v0.3.0
   git push origin v0.3.0
   ```
4. Approve the `pypi` deployment on the workflow run if you set up a
   reviewer. The GitHub release with generated notes follows.

A version can be uploaded to PyPI only once, even after deleting it: a
broken release is fixed with a new version (`0.3.1`), not by re-uploading.
