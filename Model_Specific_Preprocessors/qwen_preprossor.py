import json
import uuid
from pathlib import Path


# ============================================================
# GLOBAL CONFIGURATION
# ============================================================

INPUT_FILE = "../Datasets/Test_Dataset_9/train.jsonl"

OUTPUT_FILE = "../Datasets/Test_Dataset_9/train_qwen_61k.jsonl"

ENCODING = "utf-8"

# Attach the tool definitions (tools.json from the dataset merger) to
# every example.
INCLUDE_TOOLS = True


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



def load_tool_definitions():
    """Tool definitions written by the dataset merger (tools.json next to
    the input file, {domain: [definitions]}). Each example gets its
    domain's list as "tools", so the chat
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


def tools_for(example, tools):
    """The tool definitions of the example's domain.

    tools.json maps {domain: [definitions]}; an example names its domain
    in metadata.domain. If the file holds a single domain, or is a plain
    list (older merger), every example gets that list.
    """

    if not tools or isinstance(tools, list):
        return tools

    domain = (example.get("metadata") or {}).get("domain")

    if domain in tools:
        return tools[domain]

    if len(tools) == 1:
        return next(iter(tools.values()))

    raise ValueError(
        f"Example without a known domain ({domain!r}); tools.json has "
        f"{sorted(tools)}"
    )



# ============================================================
# DATASET PROCESSING
# ============================================================


def process_example(example, tools=None):

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


    processed = {
        "messages": processed_messages
    }

    example_tools = tools_for(example, tools)

    if example_tools:
        processed["tools"] = example_tools

    return processed



def process_dataset():

    processed = 0

    tools = load_tool_definitions()


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
                example,
                tools
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