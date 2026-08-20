1. Pick a category subfolder under `templates/` (e.g. `tool_use/`,
   `safety_and_refusals/`, `conversational/`) — reuse an existing one or
   create a new one if none fit. Add the new JSON template there,
   orient yourself on the existing ones.
2. Add a linguistic schema for the phrases you want to use at the same
   relative path under `schemas/language/<category>/`.
3. Add needed entities and tools.
4. Add a scenario containing said tools/entities and define new
   constraints at the same relative path under
   `schemas/scenarios/<category>/`.

The template, language schema, and scenario file must all share the same
name and category subfolder — the generator derives the scenario and
language paths from the template's path.