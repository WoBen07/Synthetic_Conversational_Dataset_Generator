1. Pick a category subfolder under `templates/` (e.g. `tool_use/`,
   `safety_and_refusals/`, `conversational/`) — reuse an existing one or
   create a new one if none fit. Add the new JSON template there,
   orient yourself on the existing ones. Start with a `user` message, or
   with `{"role": "system", "content": "{{robot_context}}"}`.
2. Add a linguistic schema for the phrases you want to use at the same
   relative path under `schemas/language/<category>/`. Bundle phrases
   that must match (a request and the `reason`/`note` derived from it).
3. Add needed entities and tools.
4. Add a scenario containing said tools/entities and define new
   constraints at the same relative path under
   `schemas/scenarios/<category>/`, plus a `robot_context` if the robot
   needs to know who it is with.
5. Render a few datapoints and check that they validate.

The template, language schema, and scenario file must all share the same
name and category subfolder — the generator derives the scenario and
language paths from the template's path.

Details and the rules every conversation must follow:
[documentation/templates.md](documentation/templates.md) and
[documentation/schemas.md](documentation/schemas.md).
