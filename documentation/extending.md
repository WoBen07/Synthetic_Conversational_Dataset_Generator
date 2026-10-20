# Extending the Generator

To add a new synthetic scenario:

1. Add or reuse an entity schema in `schemas/entities/`.
2. Pick a category subfolder (an existing one like `tool_use/` or
   `safety_and_refusals/`, or a new one) and add a scenario YAML file at
   `schemas/scenarios/<category>/<name>.yaml`. Declare a
   [`robot_context`](schemas.md#robot-context) if the robot needs to know
   where it is or who it is talking to, and tie "today" phrases to
   `today` with an `equal` constraint.
3. Add a language schema at `schemas/language/<category>/<name>.yaml`.
   Use [bundled options](schemas.md#bundled-options) wherever a phrase and
   a tool argument, or two phrases, must match.
4. Add a JSON template at `templates/<category>/<name>.json`, following
   the [rules for conversations](templates.md#rules-for-conversations).
5. Register any new field generator in `generators/__init__.py`.
6. Render a few datapoints and check them (see
   [checking a template](templates.md#checking-a-template)), then run
   the [tests](testing.md); `test_templates.py` covers the new template
   automatically. Add `tags` to the scenario if evaluation should be
   able to select the template's datapoints.
7. Optionally set an amount in `config/generation_config.yaml`
   (otherwise the category amount applies) and run the
   [uniqueness optimizer](uniqueness.md) to see whether the phrase pools
   are large enough for it.

The scenario, language, and template files must share the same `<name>`
and live under the same `<category>` subfolder in all three trees:
`engine/orchestrator.py` finds templates by walking `templates/`
recursively and derives the scenario/language paths from the same
relative path.

If the template calls a tool that should make up a minimum share of the
dataset, add the tool to `tool_share_targets` in the config instead of
raising amounts by hand.

The short reference in [adding_new_templates.md](../adding_new_templates.md) matches this flow.
