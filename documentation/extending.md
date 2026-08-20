# Extending the Generator

To add a new synthetic scenario:

1. Add or reuse an entity schema in `schemas/entities/`.
2. Pick a category subfolder (an existing one like `tool_use/` or
   `safety_and_refusals/`, or a new one) and add a scenario YAML file at
   `schemas/scenarios/<category>/<name>.yaml`.
3. Add a language schema at `schemas/language/<category>/<name>.yaml`.
4. Add a JSON template at `templates/<category>/<name>.json`.
5. Register any new field generator in `generators/__init__.py`.
6. Run the generator through `engine/runner.py` or `DatasetGenerator`.

The scenario, language, and template files must share the same `<name>`
and live under the same `<category>` subfolder in all three trees —
`engine/orchestrator.py` finds templates by walking `templates/`
recursively and derives the scenario/language paths from the same
relative path.

The short reference in [adding_new_templates.md](../adding_new_templates.md) matches this flow: template, language schema, entities/tools, then scenario and constraints.