#!/usr/bin/env python3

import json
from pathlib import Path


# ==========================
# Configuration
# ==========================

INPUT_FILE = Path("../Datasets/Test_Dataset_2/validation.jsonl")
OUTPUT_FILE = Path("../Datasets/Test_Dataset_2/validation_gemma.jsonl")


# ==========================
# Conversion Logic
# ==========================

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


def convert_example(example):
    """
    Convert a complete JSONL example.
    """

    return {
        "messages": [
            convert_message(message)
            for message in example["messages"]
        ]
    }


def convert_jsonl(input_file, output_file):

    converted_count = 0

    with open(input_file, "r", encoding="utf-8") as infile, \
         open(output_file, "w", encoding="utf-8") as outfile:

        for line in infile:

            if not line.strip():
                continue

            example = json.loads(line)

            converted = convert_example(example)

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