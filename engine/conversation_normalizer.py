"""Collapse consecutive assistant turns into a single message.

Templates historically expressed "assistant says something, then calls a
tool" as two adjacent ``{"role": "assistant"}`` entries, because no template
puts ``content`` and ``tool_call`` in the same message. Rendered into a chat
template (ChatML / Qwen) that becomes two ``<|im_start|>assistant`` blocks in
a row - a shape no base model has seen - which destabilises turn-boundary
learning during SFT and lets raw control tokens (``<tool_response>`` ...) leak
into generated answers.

This module folds every run of consecutive assistant messages into one
message that carries both the text and the tool call. It runs on every
generated datapoint (see ``DatasetGenerator.generate_one``), so future
templates that reintroduce the split are corrected automatically.
"""


def _tool_calls_of(message):
    """Return a message's tool calls as a list.

    Supports both the repository's singular ``tool_call`` (a dict) and the
    plural ``tool_calls`` (a list) in case a template ever uses it.
    """

    plural = message.get("tool_calls")

    if plural:
        return list(plural) if isinstance(plural, list) else [plural]

    singular = message.get("tool_call")

    if singular:
        return [singular]

    return []


def _merge_assistant_pair(first, second):
    """Merge two consecutive assistant messages into one."""

    contents = [
        message["content"]
        for message in (first, second)
        if isinstance(message.get("content"), str)
        and message["content"].strip()
    ]

    calls = _tool_calls_of(first) + _tool_calls_of(second)

    merged = {"role": "assistant"}

    if contents:
        merged["content"] = " ".join(contents)

    if len(calls) == 1:
        # Keep the repository-wide singular convention so the existing
        # validators and the model-specific preprocessors keep working.
        merged["tool_call"] = calls[0]

    elif len(calls) > 1:
        # Not produced by any current template, but merge both lists rather
        # than silently dropping a call.
        merged["tool_calls"] = calls

    return merged


def collapse_consecutive_assistant_messages(messages):
    """Return a new message list with no two adjacent assistant entries.

    A run of three or more assistant messages folds left into a single
    message. Input messages are not mutated.
    """

    collapsed = []

    for message in messages:

        if (
            collapsed
            and message.get("role") == "assistant"
            and collapsed[-1].get("role") == "assistant"
        ):
            collapsed[-1] = _merge_assistant_pair(collapsed[-1], message)

        else:
            collapsed.append(dict(message))

    return collapsed


def normalize_conversation(datapoint):
    """Return ``datapoint`` with its ``messages`` list normalised.

    The datapoint is shallow-copied; the original is left untouched.
    """

    messages = datapoint.get("messages")

    if not isinstance(messages, list):
        return datapoint

    normalized = dict(datapoint)

    normalized["messages"] = collapse_consecutive_assistant_messages(messages)

    return normalized
