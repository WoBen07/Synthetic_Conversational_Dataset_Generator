# Validation

Every rendered datapoint is validated before it is written. A datapoint
with any error is regenerated (see `generate_many` in
[engine](engine.md#enginedataset_generatorpy)), so validators work as
filters: a template whose phrases or tool arguments violate a rule
simply produces fewer valid datapoints, or none.

## Combined Validators

`engine/validators/validator.py` runs, in this order:

| validator | rejects |
|---|---|
| `StructureValidator` | missing `messages`/`role`; a conversation that does not start with `system` or `user`; a `system` message anywhere but first; an assistant turn with neither text nor tool call; a user or system message without content; a `tool` message without `name`; a tool result followed by anything other than an assistant turn |
| `PlaceholderValidator` | unresolved `{{...}}` anywhere in the datapoint |
| `ToolValidator` | a tool call not followed by a tool response of the same name |
| `ConversationFlowValidator` | two consecutive messages with the same role (guard behind the normaliser) |
| `PronounValidator` | simple gender/pronoun mismatches |
| `WeatherRecommendationValidator` | clothing advice that does not fit the reported weather |
| `WeatherConsistencyValidator` | weather claims that contradict the `get_weather` result |
| `WeatherGroundingValidator` | weather claims without a `get_weather` call |
| `GroundingValidator` | tool arguments the robot could not know (below) |
| `LanguageValidator` | doubled words and wrong indefinite articles (below) |

## GroundingValidator

Prevents training the model to act on information nobody gave it:

- every `patient_id` in a tool call must have appeared before, in the
  system context, a user message or a tool result;
- every `find_patient` argument must have been said by the user, stated
  in the system context or returned by an earlier tool. All words of
  the argument must occur, so a first and last name given in separate
  turns count, and so does a room taken from an earlier match;
- `reason` (`notify_staff`) and `note` (`log_patient_note`) must not be
  a copy of a user message; the robot summarises in its own words;
- `navigate_to` and `alert_staff` rooms must not start with an article
  ("Sunroom", not "the Sunroom").

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
