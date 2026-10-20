#!/usr/bin/env python3

import json
from pathlib import Path


# ==========================
# Configuration
# ==========================

INPUT_FILE = Path("../Datasets/Test_Dataset_2/validation.jsonl")
OUTPUT_FILE = Path("../Datasets/Test_Dataset_2/validation_gemma.jsonl")

# Attach the tool definitions (tools.json from the dataset merger) to
# every example.
INCLUDE_TOOLS = True


# ==========================
# Conversion Logic
# ==========================


def load_tool_definitions():
    """Tool definitions written by the dataset merger (tools.json next to
    the input file). Attached to every example as "tools", so the chat
    template renders the same tool list the model gets at inference
    (tokenizer.apply_chat_template(messages, tools=example["tools"]))."""

    if not INCLUDE_TOOLS:
        return None

    path = Path(INPUT_FILE).parent / "tools.json"

    if not path.exists():
        print(f"WARNING: {path} not found - examples are written without tools")
        return None

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def extract_tool_calls(message):
    """
    Return the message's tool calls as a list, accepting both the singular
    `tool_call` (a dict) and the plural `tool_calls` (a list) forms.
    """

    plural = message.get("tool_calls")

    if plural:
        return list(plural) if isinstance(plural, list) else [plural]

    singular = message.get("tool_call")

    if singular:
        return [singular]

    return []


def convert_message(message):
    """
    Convert old tool_call format into OpenAI tool_calls format.

    A merged assistant turn may carry both text and a tool call; the text
    is preserved as `content` instead of being dropped.
    """

    # Convert assistant tool calls
    if "tool_call" in message or "tool_calls" in message:

        tool_calls = extract_tool_calls(message)

        content = message.get("content")

        if not (isinstance(content, str) and content.strip()):
            content = None

        return {
            "role": "assistant",
            "content": content,
            "tool_calls": [
                {
                    "type": "function",
                    "function": {
                        "name": tool_call["name"],
                        "arguments": json.dumps(
                            tool_call.get("arguments", {}),
                            ensure_ascii=False
                        )
                    }
                }
                for tool_call in tool_calls
            ]
        }

    return message


def convert_example(example, tools=None):
    """
    Convert a complete JSONL example.
    """

    converted = {
        "messages": [
            convert_message(message)
            for message in example["messages"]
        ]
    }

    if tools:
        converted["tools"] = tools

    return converted


def convert_jsonl(input_file, output_file):

    converted_count = 0

    tools = load_tool_definitions()

    with open(input_file, "r", encoding="utf-8") as infile, \
         open(output_file, "w", encoding="utf-8") as outfile:

        for line in infile:

            if not line.strip():
                continue

            example = json.loads(line)

            converted = convert_example(example, tools)

            outfile.write(
                json.dumps(
                    converted,
                    ensure_ascii=False
                ) + "\n"
            )

            converted_count += 1

    print(f"Converted {converted_count} examples")
    print(f"Output written to: {output_file}")


# ==========================
# Main
# ==========================

if __name__ == "__main__":

    convert_jsonl(
        INPUT_FILE,
        OUTPUT_FILE
    )