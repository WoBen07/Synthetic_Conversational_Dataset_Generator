# Templates

## `templates/toolcall_template_1.json`

A complete reminder conversation template that includes:

- a user request,
- a `find_patient` assistant tool call,
- a tool response containing matching patients,
- a confirmation exchange,
- a `get_patient_appointment` tool call,
- a `navigate_to` tool call,
- a `remind_patient` tool call,
- a final assistant confirmation.

## `templates/clarification_by_room.json`

A shorter clarification template with:

- initial user request,
- assistant clarification request,
- user clarification,
- assistant acknowledgement.

## Placeholder Convention

- JSON templates use `{{placeholder}}` syntax.
- Placeholders can point to nested fields such as `{{patient.full_name}}`.
- Language schemas provide simple variable names such as `{{user_request}}`.
- The renderer resolves placeholders recursively, so one generated phrase can contain another placeholder.