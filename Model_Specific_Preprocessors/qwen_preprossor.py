import json
import uuid
from pathlib import Path


# ============================================================
# GLOBAL CONFIGURATION
# ============================================================

INPUT_FILE = "../Datasets/Test_Dataset_9/train.jsonl"

OUTPUT_FILE = "../Datasets/Test_Dataset_9/train_qwen_61k.jsonl"

ENCODING = "utf-8"


# ============================================================
# HELPER FUNCTIONS
# ============================================================


def create_tool_call_id():

    return f"call_{uuid.uuid4().hex[:8]}"



def normalize_arguments(arguments):

    """
    Ensures arguments are stored as an object.
    """

    if arguments is None:
        return {}

    if isinstance(arguments, str):

        try:
            return json.loads(arguments)

        except Exception:
            return {
                "value": arguments
            }

    return arguments



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


def convert_assistant_tool_call(message):

    """
    Converts:

    {
        "role": "assistant",
        "content": "... (optional)",
        "tool_call": {
            "name": "...",
            "arguments": {}
        }
    }


    into:


    {
        "role": "assistant",
        "content": "... (kept if present)",
        "tool_calls": [
            {
                "id": "...",
                "type": "function",
                "function": {
                    "name": "...",
                    "arguments": {}
                }
            }
        ]
    }

    """


    old_calls = extract_tool_calls(message)


    converted_calls = []
    call_id = None

    for old_call in old_calls:

        call_id = create_tool_call_id()

        converted_calls.append(
            {
                "id": call_id,
                "type": "function",
                "function": {
                    "name": old_call["name"],
                    "arguments": normalize_arguments(
                        old_call.get(
                            "arguments"
                        )
                    )
                }
            }
        )


    new_message = {
        "role": "assistant",
        "tool_calls": converted_calls
    }


    content = message.get("content")

    if isinstance(content, str) and content.strip():
        new_message["content"] = content


    # The last id is the one the single following tool response maps to.
    return new_message, call_id



def convert_tool_message(message, pending_tool_id):

    """
    Converts:

    {
        "role":"tool",
        "name":"find_patient",
        "content": {...}
    }


    into:


    {
        "role":"tool",
        "tool_call_id":"call_xxx",
        "name":"find_patient",
        "content":"{...}"
    }

    """


    new_message = dict(message)


    new_message["tool_call_id"] = pending_tool_id


    if not isinstance(
        new_message["content"],
        str
    ):

        new_message["content"] = json.dumps(
            new_message["content"],
            ensure_ascii=False
        )


    return new_message



# ============================================================
# DATASET PROCESSING
# ============================================================


def process_example(example):

    processed_messages = []

    current_tool_id = None


    for message in example["messages"]:


        if (
            message["role"] == "assistant"
            and (
                "tool_call" in message
                or "tool_calls" in message
            )
        ):

            new_message, current_tool_id = (
                convert_assistant_tool_call(
                    message
                )
            )

            processed_messages.append(
                new_message
            )


        elif (
            message["role"] == "tool"
        ):

            processed_messages.append(
                convert_tool_message(
                    message,
                    current_tool_id
                )
            )


            current_tool_id = None


        else:

            processed_messages.append(
                message
            )


    return {
        "messages": processed_messages
    }



def process_dataset():

    processed = 0


    with open(
        INPUT_FILE,
        "r",
        encoding=ENCODING
    ) as infile, open(
        OUTPUT_FILE,
        "w",
        encoding=ENCODING
    ) as outfile:


        for line in infile:

            if not line.strip():
                continue


            example = json.loads(
                line
            )


            example = process_example(
                example
            )


            outfile.write(
                json.dumps(
                    example,
                    ensure_ascii=False
                )
                + "\n"
            )


            processed += 1


    print(
        f"Processed {processed} examples"
    )

    print(
        f"Saved to {OUTPUT_FILE}"
    )



# ============================================================
# MAIN
# ============================================================


if __name__ == "__main__":

    process_dataset()