# Validation

The generator validates each rendered datapoint before writing it.

## Combined Validators

`engine/validators/validator.py` runs these checks:

- `StructureValidator`: ensures `messages` exists and that each message has the required fields for its role.
- `PlaceholderValidator`: rejects unresolved `{{...}}` strings anywhere in the datapoint.
- `ToolValidator`: checks that assistant tool calls are followed by a matching tool response.
- `PronounValidator`: checks for simple gender/pronoun mismatches in rendered text.

## Practical Rules

- `messages` must exist.
- Each message must have a `role`.
- `user` messages must have `content`.
- `assistant` messages must have either `content` or `tool_call`.
- `tool` messages must have `name`.
- Tool calls must be followed by a matching tool response.
- No unresolved placeholders may remain in the final output.
- Pronoun usage should match the patient gender.