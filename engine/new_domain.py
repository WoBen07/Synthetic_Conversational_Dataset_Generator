#!/usr/bin/env python3
"""Create a new domain pack with one working example template.

    python -m synthetic_data_generator.engine.new_domain retail_store \\
        --description "Shop assistant robot answering customer questions."

The pack is YAML/JSON only (no Python): a customer entity, one tool, one
template with its scenario and language schema, and a config. Generate it
right away to check the setup, then replace the example with real
templates:

    python -m synthetic_data_generator.engine.orchestrator --domain retail_store

See documentation/domains.md.
"""

import argparse
import re
import sys

from synthetic_data_generator.engine import domain as domains


NAME = re.compile(r"^[a-z][a-z0-9_]*$")


FILES = {

"domain.yaml": '''# The {name} domain. See documentation/domains.md.

name: {name}

description: >
  {description}

# Regex for generated IDs, masked when datapoints are compared for
# duplicates. This example uses no generated IDs.
generated_id_pattern: null

# Wording of the opening system message (engine/robot_context.py).
robot_context:
  today: "Today is {{today}}."
  location: "You are in {{location}}."
  numeric_location: "room {{value}}"
  records:
    customer: "Customer: {{full_name}}."
  speakers:
    customer: "You are speaking with a customer."
    staff: "You are speaking with a member of staff."
''',

"config.yaml": '''# Generation settings of the {name} domain (amounts, tool shares).

default_amount: 200

# Per-template overrides, keyed by the template's leaf name
important_templates: {{}}

# Per-category amounts, keyed by template-path prefix
category_amounts: {{}}

# Minimum share of all tool calls per tool
tool_share_targets: {{}}

tool_share_max_scale: 2.0
''',

"entities/customer.yaml": '''entity: customer


fields:

  first_name:
    type: string
    generator: first_name

  last_name:
    type: string
    generator: last_name


computed:

  full_name:
    template: "{{{{first_name}}}} {{{{last_name}}}}"
''',

"tools/check_order_status.yaml": '''tool: check_order_status

side_effects: false

description: Looks up the delivery status of an order.


input:

  order_number:
    type: string
    required: true
    description: The order number the customer gave.
    source: mentioned


output:

  order_number:
    type: string

  status:
    type: enum
    values: [processing, shipped, delivered]
''',

"templates/orders/order_status.json": '''{{
  "messages": [
    {{ "role": "system", "content": "{{{{robot_context}}}}" }},
    {{ "role": "user", "content": "{{{{request}}}}" }},
    {{
      "role": "assistant",
      "tool_call": {{
        "name": "check_order_status",
        "arguments": {{ "order_number": "{{{{order_number}}}}" }}
      }}
    }},
    {{
      "role": "tool",
      "name": "check_order_status",
      "content": {{ "order_number": "{{{{order_number}}}}", "status": "{{{{status.value}}}}" }}
    }},
    {{ "role": "assistant", "content": "{{{{status.answer}}}}" }}
  ]
}}
''',

"scenarios/orders/order_status.yaml": '''name: order_status

entities:
  customer:
    type: customer

language_schema: order_status

robot_context:
  customer: customer
  speaker: customer

tags: [example]
''',

"language/orders/order_status.yaml": '''variables:

  # Values a language schema provides need no Python generator.
  order_number:
    - "48213"
    - "55120"
    - "61877"
    - "70342"

  request:
    - "Hi, I'm {{{{customer.full_name}}}}. Where is my order {{{{order_number}}}}?"
    - "Could you check on order {{{{order_number}}}} for me?"
    - "What's the status of my order {{{{order_number}}}}, please?"

  # The status and the answer about it belong together (a bundle).
  status:
    - value: "processing"
      answer: "Your order {{{{order_number}}}} is still being prepared and hasn't shipped yet."
    - value: "shipped"
      answer: "Good news: order {{{{order_number}}}} has shipped and is on its way."
    - value: "delivered"
      answer: "According to the record, order {{{{order_number}}}} has already been delivered."
''',
}


def create_domain(name, description, domains_dir=None):
    """Write the example pack to <domains_dir>/<name>/ and return its path."""

    if not NAME.match(name):
        raise ValueError(
            f"Invalid domain name {name!r}: use lowercase letters, digits "
            f"and underscores, starting with a letter."
        )

    root = (domains_dir or domains.DOMAINS_DIR) / name

    if root.exists():
        raise FileExistsError(f"{root} already exists")

    for relative, content in FILES.items():

        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            content.format(name=name, description=description),
            encoding="utf-8"
        )

    return root


def main(argv=None):

    parser = argparse.ArgumentParser(description="Create a new domain pack.")
    parser.add_argument("name", help="domain name, e.g. retail_store")
    parser.add_argument("--description", default="Describe the domain here.")

    args = parser.parse_args(argv)

    root = create_domain(args.name, args.description)

    print(f"Created {root} with one example template (orders/order_status).")
    print(
        f"Try it: python -m synthetic_data_generator.engine.orchestrator "
        f"--domain {args.name}"
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
