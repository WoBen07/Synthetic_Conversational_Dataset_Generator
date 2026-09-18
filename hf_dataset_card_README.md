---
language:
- en
tags:
- synthetic
- healthcare
- robotics
- human-robot-interaction
- dialogue
- conversational-ai
- function-calling
- tool-use
task_categories:
- text-generation
pretty_name: Synthetic Hospital-Robot Conversational Dataset
size_categories:
- 10K<n<100K
configs:
- config_name: default
  data_files:
  - split: train
    path: Test_Dataset_9/train.jsonl
  - split: validation
    path: Test_Dataset_9/validation.jsonl
- config_name: qwen
  data_files:
  - split: train
    path: Test_Dataset_9/train_qwen_61k.jsonl
  - split: validation
    path: Test_Dataset_9/validation_qwen_61k.jsonl
---

# Synthetic Hospital-Robot Conversational Dataset

A fully synthetic dataset of multi-turn conversations between a patient (or
visitor) and a hospital service robot, generated for training and
evaluating conversational AI models on human-robot interaction (HRI) in a
medical setting.

**This is not real patient data.** Every name, patient ID, room number, and
appointment is randomly generated at build time — nothing in this dataset
was collected from an actual hospital, patient, or interaction. It is also
not a source of medical advice or clinical guidance; several of the
conversations exist specifically to show the robot *declining* to give
medical advice and escalating to human staff instead.

## Dataset Summary

Conversations are built from hand-authored templates covering eight
behavioral categories of hospital-robot interaction:

| Category | What it covers |
|---|---|
| `conversational` | Small talk and companionship — hobbies, family news, media, jokes, weather, reminiscing, gratitude, boredom check-ins, and chit-chat interleaved before/during/after a task |
| `patient_identity` | Verifying who a patient is, disambiguating similar or identical names, correcting a mistaken identity |
| `physical_interaction` | Escorting a patient, room changes mid-task, offering physical assistance (a cane, a jacket, shoes), introductions to staff or other patients |
| `safety_and_refusals` | Declining out-of-scope requests (medical advice, physical assistance beyond the robot's role), emergency escalation, consent-seeking, stating capability boundaries |
| `social_dynamics` | Handling patient frustration, patiently repeating information, de-escalation |
| `tool_error_recovery` | Recovering from a failed or ambiguous tool call — no match found, multiple matches, retrying after failure |
| `tool_use` | Scheduling and rescheduling appointments, reminders, navigation, multi-step tool call sequences |
| `trust_and_honesty` | Honest uncertainty, refusing to fabricate information, self-correction, being transparent about what is logged, wellbeing check-ins |

The current release (`Test_Dataset_9`) contains **61,350** conversations
generated from 128 distinct templates, split 90/10 into train and
validation.

| Split | Examples |
|---|---|
| train | 55,215 |
| validation | 6,135 |
| **total** | **61,350** |

## Dataset Structure

Each line of the `.jsonl` files is one JSON object with a single field,
`messages`: a list of chat turns in strict `user`/`assistant`(/`tool`)
alternation, in the widely-used chat-format style (compatible with
ChatML-style and OpenAI-style chat templates).

Two file variants are provided, built from the same underlying
conversations:

### `train.jsonl` / `validation.jsonl` (default)

The generator's native format. A tool call is a single object on the
assistant message; a tool's response is a plain JSON object.

```json
{
  "messages": [
    {"role": "user", "content": "Could you walk Helga Schulz over to 1015 for the appointment?"},
    {"role": "assistant", "content": "Of course, on our way to 1015 now."},
    {"role": "user", "content": "Actually, stop — 1015 just got closed off, go to the Sunroom instead."},
    {
      "role": "assistant",
      "content": "No problem, updating the route to the Sunroom.",
      "tool_call": {"name": "navigate_to", "arguments": {"room": "the Sunroom"}}
    },
    {"role": "tool", "name": "navigate_to", "content": {"status": "arrived", "location": "the Sunroom"}},
    {"role": "assistant", "content": "Here at the Sunroom now, no trouble redirecting."}
  ]
}
```

### `train_qwen_61k.jsonl` / `validation_qwen_61k.jsonl` (`qwen` config)

The same conversations reshaped into the OpenAI/Qwen function-calling
format: `tool_calls` is a list with an `id`, and the matching tool response
carries `tool_call_id` with its `content` JSON-stringified. Use this
variant if you're fine-tuning a model that expects that convention.

```json
{
  "messages": [
    {"role": "user", "content": "..."},
    {
      "role": "assistant",
      "content": "No problem, updating the route to the Sunroom.",
      "tool_calls": [{"id": "call_45cc3a5b", "type": "function", "function": {"name": "navigate_to", "arguments": {"room": "the Sunroom"}}}]
    },
    {"role": "tool", "name": "navigate_to", "tool_call_id": "call_45cc3a5b", "content": "{\"status\": \"arrived\", \"location\": \"the Sunroom\"}"},
    {"role": "assistant", "content": "..."}
  ]
}
```

Load either variant with the `datasets` library:

```python
from datasets import load_dataset

ds = load_dataset("Verox132/Medical_Conversational_Dataset", "default")
# or: load_dataset("Verox132/Medical_Conversational_Dataset", "qwen")
```

## Source Data / Generation Methodology

Every conversation is produced by a template-driven generator: a scenario
defines the entities involved (patient, appointment, weather, etc.) and any
constraints between them, a language schema supplies pools of phrasing for
each turn, and a JSON template assembles them into a full conversation.
Every rendered conversation is validated (structure, resolved
placeholders, matched tool calls, pronoun/gender consistency) before being
kept, and consecutive same-role turns are folded so the result is always
strict `user`/`assistant` alternation.

The generator itself is open source:
**[github.com/WoBen07/Synthetic_Conversational_Dataset_Generator](https://github.com/WoBen07/Synthetic_Conversational_Dataset_Generator)**

This project was started as part of a Bachelor's thesis at the University
of Augsburg, Germany, developed by Benedict Wohlgemuth under the guidance
of Dr. Matthias Kraus. The dataset is under active development — more
categories, entrypoints, and dataset versions will be added over time
under new subfolders in this repo.

## Limitations

- **Synthetic, not real-world data.** Language patterns reflect the
  authors' template design, not observed real hospital interactions.
- **English only**, and reflects a Western/German-influenced naming and
  cultural context (patient and visitor names are drawn from a German name
  pool).
- **Template-based diversity.** Phrasing is drawn from finite pools of
  hand-written options per template, so exact wording repeats across the
  dataset far more than in naturally collected dialogue.
- **Not clinically validated.** Nothing in this dataset should be used as
  a source of medical advice, and models trained on it should not be
  deployed to give medical advice either.

## License

TBD — a license has not been finalized yet. Do not treat this repo as
licensed for reuse until this section is updated.

## Citation

If you use this dataset, please cite the source repository:

```
Wohlgemuth, B. (2026). Synthetic Conversational Dataset Generator
[Software and dataset]. University of Augsburg.
https://github.com/WoBen07/Synthetic_Conversational_Dataset_Generator
```
