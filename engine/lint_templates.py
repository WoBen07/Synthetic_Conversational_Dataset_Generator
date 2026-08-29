#!/usr/bin/env python3
"""Static lint for conversation templates.

Flags every ``templates/**/*.json`` message list that contains two
consecutive entries with the same ``role`` - the shape that renders into
back-to-back ``<|im_start|>assistant`` blocks. The renderer's
``normalize_conversation`` step folds these automatically at generation
time, so this lint does not block generation; it surfaces the offending
file and line so the template can be cleaned up at the source.

Run directly::

    python -m synthetic_data_generator.engine.lint_templates
"""

import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_DIR = PROJECT_ROOT / "templates"


def _role_line_numbers(path):
    """1-based line number of every ``"role"`` key, in file order.

    Every message object in these templates puts ``"role"`` on its own
    line, so the n-th entry here lines up with the n-th message.
    """

    numbers = []

    for line_number, text in enumerate(
        path.read_text(encoding="utf-8").splitlines(),
        start=1,
    ):
        if '"role"' in text:
            numbers.append(line_number)

    return numbers


def find_consecutive_roles(path):
    """Return ``(message_index, role, line)`` for each message whose role
    matches the previous message's role."""

    data = json.loads(path.read_text(encoding="utf-8"))

    messages = data.get("messages", [])

    role_lines = _role_line_numbers(path)

    aligned = len(role_lines) == len(messages)

    findings = []

    for i in range(1, len(messages)):

        if messages[i].get("role") == messages[i - 1].get("role"):

            line = role_lines[i] if aligned else None

            findings.append((i, messages[i].get("role"), line))

    return findings


def lint(template_dir=TEMPLATE_DIR):
    """Return a list of ``(path, message_index, description)`` problems."""

    problems = []

    for path in sorted(Path(template_dir).rglob("*.json")):

        try:
            findings = find_consecutive_roles(path)

        except (json.JSONDecodeError, OSError) as error:
            problems.append((path, None, f"could not read template: {error}"))
            continue

        for message_index, role, line in findings:

            where = (
                f"line {line}"
                if line is not None
                else f"messages[{message_index}]"
            )

            problems.append(
                (
                    path,
                    message_index,
                    f"consecutive '{role}' message at {where}",
                )
            )

    return problems


def main():

    problems = lint()

    if not problems:
        print("Template lint OK: no consecutive same-role messages.")
        return 0

    print(f"Template lint: {len(problems)} issue(s) found:")

    for path, _message_index, description in problems:

        try:
            shown = path.relative_to(PROJECT_ROOT)
        except ValueError:
            shown = path

        print(f"  {shown}: {description}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
