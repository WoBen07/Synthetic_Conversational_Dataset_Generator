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

def convert_message(message):
    """
    Convert old tool_call format into OpenAI tool_calls format.
    """

    # Convert assistant tool calls
    if "tool_call" in message:

        tool_call = message["tool_call"]

        return {
            "role": "assistant",
            "content": None,
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