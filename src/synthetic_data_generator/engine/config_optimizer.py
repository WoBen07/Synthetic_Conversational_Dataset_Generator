#!/usr/bin/env python3
"""Cap template amounts so the generated dataset does not repeat itself.

Optional step. It samples every template, measures how many differently
worded datapoints the template can actually produce, and writes a
``uniqueness_caps`` block into the domain's config.yaml. The
orchestrator never generates more datapoints of a template than its cap,
including after tool_share_targets scaling.

Why sampling: names, rooms and days change in every datapoint, so the
generator's exact-duplicate check almost never fires, yet two datapoints
with the same phrases and only a different name are near duplicates. A
datapoint's *skeleton* is therefore the set of language options it used
(see LanguageGenerator.choices and TemplateRenderer.used_paths). Two
limits are derived from it:

1. Near-duplicate rate. From the pool sizes of the variables the
   template really uses, and the share of combinations that pass the
   validators (the weather templates reject most), the optimizer
   estimates the number of distinct skeletons D. If a sample of the
   template already repeats skeletons, the Chao1 estimate from the
   sample replaces it. The cap is the largest amount whose expected
   share of repeated skeletons stays below ``max_duplicate_rate``.

2. Phrase repetition. Even with millions of combinations, a variable
   with 6 phrases repeats each of them amount / 6 times. The cap keeps
   every used phrase pool below ``max_phrase_repeats`` uses per phrase.
   Pools with a single option are constants by design and are ignored.

The cap is the smaller of the two, but never below ``min_amount``, so
every template stays represented. Settings live in the
``uniqueness_optimizer`` section of config/generation_config.yaml; flags
override them.

Usage (from the directory that contains synthetic_data_generator/)::

    python -m synthetic_data_generator.engine.config_optimizer            # report only (default domain)
    python -m synthetic_data_generator.engine.config_optimizer --domain hospital
    python -m synthetic_data_generator.engine.config_optimizer --write    # write the caps
    python -m synthetic_data_generator.engine.config_optimizer --clear    # remove them
    python -m synthetic_data_generator.engine.orchestrator --optimize     # optimise, then generate
"""

import argparse
import json
import math
import random
import re
import sys
from collections import Counter
from datetime import datetime

import yaml

from synthetic_data_generator.engine import orchestrator
from synthetic_data_generator.engine.dataset_generator import DatasetGenerator
from synthetic_data_generator.engine.domain import resolve_domain

BLOCK_START = "# >>> uniqueness_caps"
BLOCK_END = "# <<< uniqueness_caps"

BLOCK_PATTERN = re.compile(
    rf"\n*{re.escape(BLOCK_START)}.*?{re.escape(BLOCK_END)}[^\n]*\n?",
    re.S
)

DEFAULTS = {
    "samples": 200,
    "max_duplicate_rate": 0.05,
    "max_phrase_repeats": 100,
    "min_amount": 100,
    "seed": 1234,
}


# ==========================
# Estimation
# ==========================

def duplicate_share(amount, distinct):
    """Expected share of datapoints whose skeleton already occurred when
    drawing ``amount`` times uniformly from ``distinct`` skeletons."""

    if amount <= 1:
        return 0.0

    if distinct <= 1:
        return 1 - 1 / amount

    expected_distinct = distinct * -math.expm1(amount * math.log1p(-1 / distinct))

    return 1 - expected_distinct / amount


def max_amount_for_duplicate_rate(distinct, rate, limit=10_000_000):
    """Largest amount whose expected duplicate share stays <= rate."""

    if duplicate_share(limit, distinct) <= rate:
        return limit

    low, high = 1, limit

    while low < high:

        middle = (low + high + 1) // 2

        if duplicate_share(middle, distinct) <= rate:
            low = middle
        else:
            high = middle - 1

    return low


def chao1(counts):
    """Chao1 estimate of the number of distinct skeletons."""

    observed = len(counts)
    singletons = sum(1 for count in counts.values() if count == 1)
    doubletons = sum(1 for count in counts.values() if count == 2)

    if doubletons:
        return observed + singletons ** 2 / (2 * doubletons)

    return observed + singletons * (singletons - 1) / 2


def sample_template(generator, template_id, samples):
    """Render up to ``samples`` valid datapoints and collect skeletons."""

    scenario, _, language = generator.domain.paths(template_id)

    skeletons = Counter()
    used_pools = {}
    evaluated = 0
    valid = 0
    attempts = 0

    while valid < samples and attempts < samples * 20:

        attempts += 1

        try:
            datapoint, trace = generator.generate_one_traced(
                scenario,
                template_id,
                language
            )

        except ValueError:
            # Constraint violations only redraw entities, they say
            # nothing about which wordings are possible.
            continue

        evaluated += 1

        if generator.validator.validate(datapoint):
            continue

        valid += 1

        choices = trace["choices"]

        for name in choices:
            used_pools[name] = trace["pool_sizes"][name]

        skeletons[tuple(sorted(choices.items()))] += 1

    return {
        "skeletons": skeletons,
        "used_pools": used_pools,
        "valid": valid,
        "acceptance": valid / evaluated if evaluated else 0.0,
    }


def analyse(sample, settings):
    """Turn a sample into the template's uniqueness cap."""

    if not sample["valid"]:
        return None

    pools = {
        name: size
        for name, size in sample["used_pools"].items()
        if size > 1
    }

    combinations = math.prod(pools.values()) if pools else 1

    distinct = max(1.0, combinations * sample["acceptance"])

    skeletons = sample["skeletons"]

    # Repeated skeletons inside a small sample mean the space is small
    # (or validators keep only a corner of it) - trust the sample then.
    if len(skeletons) < sample["valid"]:
        distinct = min(distinct, chao1(skeletons))

    distinct = max(distinct, len(skeletons))

    duplicate_cap = max_amount_for_duplicate_rate(
        distinct,
        settings["max_duplicate_rate"]
    )

    if pools:
        bottleneck = min(pools, key=pools.get)
        phrase_cap = pools[bottleneck] * settings["max_phrase_repeats"]
    else:
        bottleneck = None
        phrase_cap = duplicate_cap

    if duplicate_cap <= phrase_cap:
        limit, reason = duplicate_cap, "near-duplicates"
    else:
        limit, reason = phrase_cap, f"pool '{bottleneck}' ({pools[bottleneck]} phrases)"

    cap = max(settings["min_amount"], limit)

    return {
        "cap": cap,
        "limited_by": reason if cap == limit else f"min_amount (would be {limit}, {reason})",
        "distinct_skeletons": round(distinct),
        "smallest_pool": bottleneck,
        "smallest_pool_size": pools.get(bottleneck),
        "acceptance": round(sample["acceptance"], 3),
    }


# ==========================
# Config block
# ==========================

def render_block(caps, details, settings, merged_from_previous):

    lines = [
        BLOCK_START + " (generated by engine/config_optimizer.py, do not edit by hand)",
        f"# {datetime.now():%Y-%m-%d %H:%M}, {settings['samples']} samples per template, "
        f"max_duplicate_rate {settings['max_duplicate_rate']}, "
        f"max_phrase_repeats {settings['max_phrase_repeats']}, "
        f"min_amount {settings['min_amount']}.",
        "# Upper limit per template; the orchestrator never generates more,",
        "# also not when scaling for tool_share_targets. Remove this block",
        "# (config_optimizer --clear) to generate the configured amounts again.",
        "uniqueness_caps:",
    ]

    for template in sorted(caps):

        detail = details.get(template)

        note = (
            f"  # {detail['limited_by']}"
            if detail
            else "  # kept from the previous run"
        )

        lines.append(f"  {template}: {caps[template]}{note}")

    if merged_from_previous:
        lines.insert(5, f"# {merged_from_previous} cap(s) kept from the previous run.")

    lines.append(BLOCK_END)

    return "\n".join(lines) + "\n"


def write_block(block, config_file):

    text = config_file.read_text(encoding="utf-8") if config_file.exists() else ""

    text = BLOCK_PATTERN.sub("\n", text).rstrip("\n") + "\n"

    if block:
        text += "\n\n" + block

    # Never leave a broken config behind.
    yaml.safe_load(text)

    config_file.write_text(text, encoding="utf-8")


# ==========================
# Main
# ==========================

def parse_args(argv):

    parser = argparse.ArgumentParser(
        description=(
            "Estimate how many non-repetitive datapoints every template "
            "can produce and cap the amounts in generation_config.yaml."
        )
    )

    parser.add_argument("--domain", metavar="NAME",
                        help="domain to optimise (default: the first configured domain)")
    parser.add_argument("--samples", type=int,
                        help="valid datapoints sampled per template")
    parser.add_argument("--max-duplicate-rate", type=float,
                        help="accepted share of datapoints that repeat another one's wording")
    parser.add_argument("--max-phrase-repeats", type=int,
                        help="how often a single phrase may be used per template")
    parser.add_argument("--min-amount", type=int,
                        help="never cap a template below this amount")
    parser.add_argument("--seed", type=int,
                        help="random seed for sampling")
    parser.add_argument("--templates", nargs="+", metavar="PREFIX",
                        help="only these templates (path prefixes); other caps are kept")
    parser.add_argument("--write", action="store_true",
                        help="write the caps into the domain's config.yaml (default: report only)")
    parser.add_argument("--clear", action="store_true",
                        help="remove the domain's uniqueness_caps block and exit")
    parser.add_argument("--report", metavar="FILE",
                        help="also save the per-template analysis as JSON")

    return parser.parse_args(argv)


def main(argv=None):

    args = parse_args(sys.argv[1:] if argv is None else argv)

    domain = resolve_domain(args.domain)

    if args.clear:
        write_block(None, domain.config_file)
        print(f"Removed uniqueness_caps from {domain.config_file}.")
        return 0

    # Settings are engine-wide, caps and amounts belong to the domain.
    config = domain.load_config()

    settings = dict(DEFAULTS)
    settings.update(orchestrator.load_config().get("uniqueness_optimizer") or {})

    for key in DEFAULTS:
        value = getattr(args, key)
        if value is not None:
            settings[key] = value

    templates = domain.templates()

    selected = [
        template for template in templates
        if not args.templates
        or any(template == p or template.startswith(f"{p}/") for p in args.templates)
    ]

    print(
        f"Sampling {len(selected)} template(s) of domain {domain.name}, up to "
        f"{settings['samples']} valid datapoints each..."
    )

    random.seed(settings["seed"])

    generator = DatasetGenerator(random_seed=None, domain=domain)

    details = {}
    broken = []

    for template in selected:

        result = analyse(
            sample_template(generator, template, settings["samples"]),
            settings
        )

        if result is None:
            broken.append(template)
        else:
            details[template] = result

    # Caps of templates that still exist but were not sampled this time
    previous = {
        template: cap
        for template, cap in (config.get("uniqueness_caps") or {}).items()
        if template in templates and template not in details
    }

    caps = dict(previous)
    caps.update({template: detail["cap"] for template, detail in details.items()})

    # Compare what the orchestrator generates without and with the caps.
    uncapped_config = dict(config)
    uncapped_config.pop("uniqueness_caps", None)

    capped_config = dict(uncapped_config)
    capped_config["uniqueness_caps"] = caps

    before = orchestrator.plan_amounts(domain, uncapped_config, verbose=False)
    after = orchestrator.plan_amounts(domain, capped_config, verbose=False)

    print(
        f"\n{'template':<62} {'distinct':>10} {'planned':>8} {'capped':>7}"
        f" {'near-dup':>9}  limited by"
    )

    for template in selected:

        detail = details.get(template)

        if detail is None:
            continue

        changed = after[template] < before[template]

        detail["planned"] = before[template]
        detail["final"] = after[template]
        detail["expected_duplicate_share"] = round(
            duplicate_share(after[template], detail["distinct_skeletons"]), 4
        )

        print(
            f"{template:<62} {detail['distinct_skeletons']:>10,} "
            f"{before[template]:>8} {after[template] if changed else '':>7} "
            f"{detail['expected_duplicate_share']:>8.1%}  "
            f"{detail['limited_by'] if changed else ''}"
        )

    for template in broken:
        print(f"{template:<62} no valid datapoint in sampling - template broken?")

    capped = [t for t in selected if t in details and after[t] < before[t]]

    print(
        f"\n{len(capped)} of {len(details)} template(s) capped. Total "
        f"datapoints: {sum(before.values()):,} -> {sum(after.values()):,}."
    )

    floored = [t for t in capped if details[t]["limited_by"].startswith("min_amount")]

    if floored:
        print(
            f"{len(floored)} template(s) sit at min_amount although their "
            f"pools allow less without repetition - add phrases to the "
            f"listed pools:"
        )
        for template in floored:
            print(f"  {template}: {details[template]['limited_by']}")

    # Tool shares with the caps, to see whether targets still hold.
    orchestrator.apply_tool_share_targets(
        orchestrator.apply_uniqueness_caps(
            {t: orchestrator.get_amount(t, capped_config) for t in templates},
            capped_config
        ),
        capped_config,
        domain
    )

    if args.report:
        with open(args.report, "w", encoding="utf-8") as file:
            json.dump(
                {"settings": settings, "templates": details, "broken": broken},
                file,
                indent=2,
                ensure_ascii=False
            )
        print(f"\nReport written to {args.report}")

    if args.write:
        write_block(render_block(caps, details, settings, len(previous)), domain.config_file)
        print(f"\nWrote {len(caps)} uniqueness cap(s) to {domain.config_file}.")
    else:
        print("\nReport only - run with --write to store the caps in the config.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
