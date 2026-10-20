All paths below are inside the domain pack, e.g. `domains/hospital/`.
For a new application, first create a pack with
`python -m synthetic_data_generator.engine.new_domain <name>`.

1. Pick a category subfolder under `templates/` (e.g. `tool_use/`,
   `safety_and_refusals/`, `conversational/`) — reuse an existing one or
   create a new one if none fit. Add the new JSON template there,
   orient yourself on the existing ones. Start with a `user` message, or
   with `{"role": "system", "content": "{{robot_context}}"}`.
2. Add a linguistic schema for the phrases you want to use at the same
   relative path under `language/<category>/`. Bundle phrases that must
   match (a request and the `reason`/`note` derived from it).
3. Add needed entities (`entities/`) and tools (`tools/`).
4. Add a scenario containing said entities and define new constraints
   at the same relative path under `scenarios/<category>/`, plus a
   `robot_context` if the robot needs to know who it is with.
5. Render a few datapoints and run the tests.

The template, language schema, and scenario file must all share the same
name and category subfolder — the generator derives the scenario and
language paths from the template's path.

Details and the rules every conversation must follow:
[documentation/templates.md](documentation/templates.md),
[documentation/schemas.md](documentation/schemas.md) and
[documentation/domains.md](documentation/domains.md).
