# Extending the Generator

To add a new synthetic scenario:

1. Add or reuse an entity schema in `schemas/entities/`.
2. Add a scenario YAML file in `schemas/scenarios/`.
3. Add a language schema in `schemas/language/`.
4. Add a JSON template in `templates/`.
5. Register any new field generator in `generators/__init__.py`.
6. Run the generator through `engine/runner.py` or `DatasetGenerator`.

The short reference in [adding_new_templates.md](../adding_new_templates.md) matches this flow: template, language schema, entities/tools, then scenario and constraints.