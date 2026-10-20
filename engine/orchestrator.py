import argparse
import json
import math
import os
import random
import subprocess
import yaml

from synthetic_data_generator.engine.dataset_generator import DatasetGenerator
from synthetic_data_generator.engine import dataset_merger
from synthetic_data_generator.engine import lint_templates
from synthetic_data_generator.engine import publish_to_hub
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


TEMPLATE_DIR = PROJECT_ROOT / "templates"
CONFIG_FILE = PROJECT_ROOT / "config" / "generation_config.yaml"

SCENARIO_DIR = PROJECT_ROOT / "schemas" / "scenarios"
LANGUAGE_DIR = PROJECT_ROOT / "schemas" / "language"

OUTPUT_ROOT = PROJECT_ROOT / "Synthetic_Data"

GENERATOR_VERSION = "0.2.0"


def load_config():
    with open(CONFIG_FILE, "r") as f:
        return yaml.safe_load(f)


def get_templates():

    templates = []

    for file in sorted(TEMPLATE_DIR.rglob("*.json")):

        relative = file.relative_to(TEMPLATE_DIR).with_suffix("")

        # POSIX-style id so it works the same as a lookup path
        # regardless of the subfolder it lives in, e.g.
        # "safety_and_refusals/medical_advice_refusal"
        templates.append(relative.as_posix())

    return templates


def get_amount(template_id, config):

    important = config.get("important_templates", {})

    # important_templates is keyed by the template's own name,
    # not its subfolder path, so look it up by the leaf name
    name = Path(template_id).name

    if name in important:
        return important[name]["amount"]

    # category_amounts is keyed by a template-path prefix: a top-level
    # category ("safety_and_refusals") or a nested sub-folder
    # ("conversational/off_topic_mid_task"). The longest matching prefix
    # wins, so a sub-folder can override its parent category.
    category_amounts = config.get("category_amounts", {})

    best_prefix = None

    for prefix, amount in category_amounts.items():

        if template_id == prefix or template_id.startswith(f"{prefix}/"):

            if best_prefix is None or len(prefix) > len(best_prefix):
                best_prefix = prefix
                best_amount = amount

    if best_prefix is not None:
        return best_amount

    return config["default_amount"]


def count_tool_calls(template_id):
    """Count the tool calls one datapoint of a template makes, by tool."""

    path = TEMPLATE_DIR / f"{template_id}.json"

    messages = json.loads(path.read_text(encoding="utf-8")).get("messages", [])

    counts = {}

    for message in messages:

        call = message.get("tool_call")

        if call:
            counts[call["name"]] = counts.get(call["name"], 0) + 1

    return counts


def tool_shares(amounts, calls):

    totals = {}

    for template, amount in amounts.items():

        for tool, count in calls[template].items():
            totals[tool] = totals.get(tool, 0) + amount * count

    overall = sum(totals.values()) or 1

    return {tool: total / overall for tool, total in totals.items()}


def apply_uniqueness_caps(amounts, config):
    """Lower every template to its uniqueness cap, if one is set.

    The caps are written into the config by engine/config_optimizer.py
    (uniqueness_caps block). Without that block nothing changes.
    """

    caps = config.get("uniqueness_caps") or {}

    return {
        template: min(amount, caps.get(template, amount))
        for template, amount in amounts.items()
    }


def plan_amounts(templates, config, verbose=True):
    """Final amount per template: configured amount, uniqueness cap,
    then tool-share scaling (which never exceeds the cap either)."""

    amounts = {
        template: get_amount(template, config)
        for template in templates
    }

    amounts = apply_uniqueness_caps(amounts, config)

    return apply_tool_share_targets(amounts, config, verbose=verbose)


def apply_tool_share_targets(amounts, config, verbose=True):
    """Scale up templates that use under-represented tools.

    Per-template amounts alone say nothing about how often each tool is
    called overall, so rare tools (alert_staff) ended up far below the
    others. tool_share_targets in the config sets a minimum share of all
    tool calls per tool; templates that call a tool below its target are
    raised step by step, up to max_scale times their configured amount.
    """

    targets = config.get("tool_share_targets", {})

    if not targets:
        return amounts

    max_scale = config.get("tool_share_max_scale", 3.0)

    caps = config.get("uniqueness_caps") or {}

    calls = {template: count_tool_calls(template) for template in amounts}

    base = dict(amounts)
    amounts = dict(amounts)

    for _ in range(50):

        shares = tool_shares(amounts, calls)

        below = [
            tool for tool, target in targets.items()
            if shares.get(tool, 0) < target
        ]

        if not below:
            break

        changed = False

        for tool in below:

            for template, counts in calls.items():

                if tool not in counts:
                    continue

                ceiling = min(
                    int(base[template] * max_scale),
                    caps.get(template, float("inf"))
                )

                raised = min(ceiling, math.ceil(amounts[template] * 1.1))

                if raised > amounts[template]:
                    amounts[template] = raised
                    changed = True

        if not changed:
            break

    if not verbose:
        return amounts

    shares = tool_shares(amounts, calls)

    print("\nTool share after applying tool_share_targets:")

    for tool, share in sorted(shares.items(), key=lambda item: -item[1]):

        target = targets.get(tool)

        note = f" (target {target:.1%})" if target else ""

        if target and share < target:
            note += " - not reached, add more templates using this tool"

        print(f"  {tool:<25} {share:6.1%}{note}")

    return amounts


def create_seed(config):

    seed_range = config["random_seed_range"]

    return random.randint(
        seed_range["min"],
        seed_range["max"]
    )


def run_template(template_id, amount, seed):

    print(
        f"\nGenerating {template_id}"
        f" | amount={amount}"
        f" | seed={seed}"
    )

    generator = DatasetGenerator(
        random_seed=seed
    )

    # Output stays flat, keyed by the template's own name, so the
    # subfolder grouping under templates/ and schemas/ doesn't
    # ripple into Synthetic_Data/ or the merger step.
    name = Path(template_id).name

    output_dir = (
        f"{OUTPUT_ROOT}/{name}"
    )

    generator.generate_many(

        scenario=f"{SCENARIO_DIR}/{template_id}.yaml",

        template=template_id,

        amount=amount,

        output_dir=output_dir,

        language_schema=f"{LANGUAGE_DIR}/{template_id}.yaml",

    )




def parse_args():

    parser = argparse.ArgumentParser(
        description="Generate every template and merge the results."
    )

    parser.add_argument(
        "--publish",
        action="store_true",
        help=(
            "After merging, push whatever is listed in "
            "approved_datasets in config/publish_config.yaml to "
            "HuggingFace Hub. Generating a dataset does not approve it - "
            "that list is edited by hand once a dataset's been reviewed."
        ),
    )

    parser.add_argument(
        "--optimize",
        action="store_true",
        help=(
            "Before generating, run engine/config_optimizer.py and write "
            "uniqueness caps into config/generation_config.yaml, so no "
            "template is generated beyond what its phrase pools can make "
            "without repeating itself."
        ),
    )

    parser.add_argument(
        "--dry-run-publish",
        action="store_true",
        help="With --publish, print what would be published without "
             "uploading anything.",
    )

    return parser.parse_args()


def main():

    args = parse_args()

    # Surface templates that still encode consecutive same-role messages.
    # The renderer folds them automatically, so this is a warning, not a
    # gate - but it keeps sloppy templates visible so they get cleaned up.
    template_problems = lint_templates.lint()

    if template_problems:

        print(
            f"\nTemplate lint: {len(template_problems)} template(s) contain "
            f"consecutive same-role messages (auto-merged at render time):"
        )

        for path, _index, description in template_problems:
            print(f"  {path.relative_to(PROJECT_ROOT)}: {description}")

        print()

    if args.optimize:

        from synthetic_data_generator.engine import config_optimizer

        config_optimizer.main(["--write"])

    config = load_config()

    templates = get_templates()

    print(
        f"Found {len(templates)} templates:"
    )

    for t in templates:
        print(" -", t)


    amounts = plan_amounts(templates, config)

    for template in templates:

        amount = amounts[template]

        seed = create_seed(
            config
        )

        run_template(
            template,
            amount,
            seed
        )


    # IMPORTANT:
    # Only called once after everything finished
    dataset_merger.main()

    if args.publish:

        publish_args = ["--dry-run"] if args.dry_run_publish else []

        exit_code = publish_to_hub.main(publish_args)

        if exit_code:
            raise SystemExit(exit_code)


if __name__ == "__main__":
    main()