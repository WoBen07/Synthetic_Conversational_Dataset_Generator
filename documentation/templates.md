# Templates

A template (`templates/<category>/<name>.json`) is the message structure
of one datapoint. Every string may contain placeholders that are filled
from the scenario's entities and the language schema.

```json
{
  "messages": [
    { "role": "system", "content": "{{robot_context}}" },
    { "role": "user", "content": "{{remind_user_phrase}}" },
    {
      "role": "assistant",
      "tool_call": {
        "name": "find_patient",
        "arguments": { "name": "{{patient.last_name}}" }
      }
    },
    {
      "role": "tool",
      "name": "find_patient",
      "content": { "matches": ["{{patient}}", "{{alternative_patient}}"] }
    },
    { "role": "assistant", "content": "{{multiple_patient_confirmation_request}}" }
  ]
}
```

## Placeholder Convention

- `{{placeholder}}` syntax; nested paths such as `{{patient.full_name}}`
  or `{{question.reason}}` (bundled language options).
- A placeholder that is the whole value keeps its type: `"{{patient}}"`
  inserts the patient record as an object.
- Placeholders inside language phrases are resolved recursively.
- An assistant message may carry `content` and a `tool_call` together;
  consecutive assistant messages are merged automatically, but writing
  them as one message is clearer.

## Rules for Conversations

These rules come from errors found in earlier datasets; the
[validators](validation.md) enforce the checkable ones.

1. **Start with `user` or `system`.** If the robot speaks first (it
   enters a room, it comes to remind someone), set the scene with
   `robot_context` and a `note`.
2. **Every ID and search term needs a source.** The robot only uses a
   `patient_id` it got from the context or a tool result, and only
   searches for names or rooms someone mentioned. A patient talking
   about "my appointment" needs a `robot_context` with `patient:`;
   a staff request about a named patient needs a `find_patient` step.
3. **"Today" must be true.** Phrases that say "today" need
   `equal: [today, appointment.day]` in the scenario and a
   `robot_context`, so the day is visible.
4. **React to every tool result.** A tool message is followed by an
   assistant turn, never directly by the user.
5. **Tool arguments are written by the robot.** `reason` and `note`
   summarise the request in the robot's words, contain only facts from
   the conversation and come from the same bundle as the request.
6. **Ask only when it is ambiguous.** If the user gave the full name
   and only one match fits, the robot proceeds
   (`tool_use/patient_reminder_direct`). A clarification question needs
   a request that really is ambiguous (only "Ms. Weber").
7. **Act only with a reason.** Offers ("Shall I let a nurse know?") are
   followed by the user's answer; the tool is called only after a yes.
   For each such template there is a counterpart in which the user
   declines and no tool is called.
8. **Route staff calls consistently.** See [staff routing](schemas.md#staff-routing).
   Do not put requests that another template routes to the other tool
   into your template.

## Counterpart Templates

Pairs that differ in one decisive detail, so the model learns the
detail rather than a default:

| template | counterpart | difference |
|---|---|---|
| `safety_and_refusals/complaint_handling` | `complaint_venting_no_action` | patient wants a person / is only venting |
| `safety_and_refusals/consent_seeking` | `consent_declined_no_action` | patient agrees / declines |
| `safety_and_refusals/false_alarm_retraction` | `false_alarm_declined_no_action` | patient accepts / declines a check |
| `safety_and_refusals/urgency_contrast_alert` | `urgency_contrast_notify` | red-flag symptom (`alert_staff` high) / mild symptom (`notify_staff`) in the same body area |
| `tool_use/patient_reminder` | `patient_reminder_direct` | "Ms. Weber" (ask which one) / full name (no question) |

`safety_and_refusals/benign_question_no_refusal` covers harmless
questions that sound alarming ("How do I kill the lights?"); the robot
answers without refusing and without a tool call.

## Checking a Template

```bash
# from the directory that contains synthetic_data_generator/
python -c "
from synthetic_data_generator.engine.dataset_generator import DatasetGenerator
g = DatasetGenerator(1); t = 'tool_use/patient_reminder'
dp = g.generate_one(f'schemas/scenarios/{t}.yaml', t, f'schemas/language/{t}.yaml')
print(dp); print(g.validator.validate(dp))"
```

An empty list means the datapoint is valid. Render a few dozen and read
them; the [uniqueness optimizer](uniqueness.md) report also shows
whether the phrase pools are large enough for the configured amount.
