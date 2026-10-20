# Validation

Every rendered datapoint is validated before it is written. A datapoint
with any error is regenerated (see `generate_many` in
[engine](engine.md#enginedataset_generatorpy)), so validators work as
filters: a template whose phrases or tool arguments violate a rule
simply produces fewer valid datapoints, or none.

## Combined Validators

`engine/validators/validator.py` runs the engine's validators plus the
domain's own (from its `create_validators()` hook), in this order:

| validator | rejects |
|---|---|
| `StructureValidator` | missing `messages`/`role`; a conversation that does not start with `system` or `user`; a `system` message anywhere but first; an assistant turn with neither text nor tool call; a user or system message without content; a `tool` message without `name`; a tool result followed by anything other than an assistant turn |
| `PlaceholderValidator` | unresolved `{{...}}` anywhere in the datapoint |
| `ToolValidator` | a tool call not followed by a tool response of the same name |
| `ConversationFlowValidator` | two consecutive messages with the same role (guard behind the normaliser) |
| `PronounValidator` | simple gender/pronoun mismatches |
| *domain validators* | hospital: `WeatherRecommendationValidator` (clothing advice must fit the reported weather), `WeatherConsistencyValidator` (no weather claims contradicting `get_weather`), `WeatherGroundingValidator` (no weather claims without a `get_weather` call), in `domains/hospital/validators/` |
| `ToolSchemaValidator` | tool calls and results that do not match the domain's `tools/` (unknown tool or argument, missing required argument, wrong type or enum value, undeclared result field) |
| `GroundingValidator` | tool arguments the robot could not know (below) |
| `LanguageValidator` | doubled words and wrong indefinite articles (below) |

## GroundingValidator

Prevents training the model to act on information nobody gave it. The
rules are declared per argument in the tool schemas (`source`, `format`,
see [tool schemas](schemas.md#tool-schemas)), so the validator itself
knows nothing about patients and works for any domain:

- `known`: IDs such as `patient_id`, and the room an alert is sent to,
  must have appeared verbatim before, in the system context, a user
  message or a tool result (`p9` does not count for `p99`);
- `mentioned`: search terms and navigation targets must consist of words
  that appeared before. A first and last name given in separate turns
  count, and so does a room from an earlier tool result;
- `own_words`: `reason` and `note` must not copy a user message;
- `format: name`: no leading article ("Sunroom", not "the Sunroom").

The robot's own messages never count as a source: it cannot ground an
argument in something it announced itself.

## LanguageValidator

Checks user and assistant text and the free-text tool arguments
(`message`, `reason`, `note`):

- doubled words such as "appointment appointment" or "check-up up"
  (deliberate repetitions like "bye bye" or "no no" are allowed);
- `a`/`an` that does not fit the next word ("a MRI scan", "an
  cardiology appointment"). The renderer already fixes articles in front
  of placeholders, so this mostly catches articles written in front of
  literal words.

## What validators cannot catch

Content that is grammatical and grounded but wrong in meaning, e.g. a
note "requires an interpreter" for a patient who said they were nervous,
is prevented by construction instead: bundle related phrases in the
language schema (see [schemas](schemas.md#bundled-options)) and check a
sample by hand or with an LLM judge.
