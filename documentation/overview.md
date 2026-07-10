# Overview

The `synthetic_data_generator` package creates synthetic conversational datapoints from three inputs:

1. A scenario YAML file that defines entities, aliases, and constraints.
2. A language-schema YAML file that supplies phrase pools for user and assistant text.
3. A JSON template that defines the final message structure to render.

The generator builds a context of entity data, injects randomized language variables, renders the template, validates the result, and writes accepted datapoints to disk.

## Folder Structure

- `engine/`: orchestration, rendering, validation, and loading logic.
- `generators/`: random value generators for entity fields.
- `schemas/`: YAML definitions for entities, scenarios, tools, and language variables.
- `templates/`: JSON templates for complete datapoints.
- `scripts/`: currently empty.