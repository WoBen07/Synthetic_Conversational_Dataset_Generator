# Extending the Generator

## A new application domain

Create a domain pack (see [domains](domains.md)):

```bash
python -m synthetic_data_generator.engine.new_domain <name> --description "..."
```

and replace its example template with real ones as below.

## A new template

Inside a domain (`domains/<domain>/`):

1. Add or reuse an entity schema in `entities/`.
2. Pick a category subfolder (an existing one like `tool_use/` or
   `safety_and_refusals/`, or a new one) and add a scenario YAML file at
   `scenarios/<category>/<name>.yaml`. Declare a
   [`robot_context`](schemas.md#robot-context) if the robot needs to know
   where it is or who it is talking to, and tie "today" phrases to
   `today` with an `equal` constraint.
3. Add a language schema at `language/<category>/<name>.yaml`.
   Use [bundled options](schemas.md#bundled-options) wherever a phrase and
   a tool argument, or two phrases, must match.
4. Add a JSON template at `templates/<category>/<name>.json`, following
   the [rules for conversations](templates.md#rules-for-conversations).
5. If a field needs a new value generator, add it to the domain's
   `GENERATORS` (see [generators](generators.md#adding-a-generator)); a
   new tool needs a schema in `tools/` (see
   [tool schemas](schemas.md#tool-schemas)).
6. Render a few datapoints and check them (see
   [checking a template](templates.md#checking-a-template)), then run
   the [tests](testing.md); `test_templates.py` covers the new template
   automatically. Add `tags` to the scenario if evaluation should be
   able to select the template's datapoints.
7. Optionally set an amount in the domain's `config.yaml` (otherwise the
   category amount applies) and run the
   [uniqueness optimizer](uniqueness.md) to see whether the phrase pools
   are large enough for it.

The scenario, language, and template files must share the same `<name>`
and live under the same `<category>` subfolder in all three trees: the
template id is derived from the path below `templates/`.

If the template calls a tool that should make up a minimum share of the
dataset, add the tool to `tool_share_targets` in the domain's config
instead of raising amounts by hand.

The short reference in [adding_new_templates.md](../adding_new_templates.md) matches this flow.
