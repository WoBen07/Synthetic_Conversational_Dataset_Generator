"""Checks over all templates, plus fixed-seed regression outputs."""

import json
import os
import re
import unittest

import yaml

import helpers

from synthetic_data_generator.engine import lint_templates
from synthetic_data_generator.engine.tool_registry import load_tools


ROOT = helpers.PACKAGE_ROOT
PLACEHOLDER = re.compile(r"\{\{(.*?)\}\}")

# Fixed-seed outputs compared with tests/golden/. A difference means the
# generated data changed: intended -> rerun with UPDATE_GOLDEN=1.
GOLDEN_TEMPLATES = [
    "tool_use/patient_reminder",
    "safety_and_refusals/consent_seeking",
    "trust_and_honesty/honest_uncertainty/recheck_returns_different_day",
]


def load_template(template_id):
    return json.loads((ROOT / "templates" / f"{template_id}.json").read_text(encoding="utf-8"))


def load_yaml(kind, template_id):
    return yaml.safe_load((ROOT / "schemas" / kind / f"{template_id}.yaml").read_text(encoding="utf-8"))


class TemplateFilesTest(unittest.TestCase):

    def test_every_template_has_scenario_and_language(self):

        for template_id in helpers.all_templates():
            with self.subTest(template=template_id):
                self.assertTrue((ROOT / "schemas/scenarios" / f"{template_id}.yaml").exists())
                self.assertTrue((ROOT / "schemas/language" / f"{template_id}.yaml").exists())

    def test_placeholders_resolve_to_known_names(self):

        for template_id in helpers.all_templates():

            scenario = load_yaml("scenarios", template_id)
            language = load_yaml("language", template_id)["variables"]

            known = (
                set(scenario.get("entities", {}))
                | set(scenario.get("aliases", {}))
                | set(language)
                | {"today", "robot_context"}
            )

            text = json.dumps(load_template(template_id))

            for placeholder in PLACEHOLDER.findall(text):
                with self.subTest(template=template_id, placeholder=placeholder):
                    self.assertIn(placeholder.split(".")[0], known)

    def test_robot_context_declared_and_used_together(self):

        for template_id in helpers.all_templates():
            with self.subTest(template=template_id):
                used = "{{robot_context}}" in json.dumps(load_template(template_id))
                declared = "robot_context" in load_yaml("scenarios", template_id)
                self.assertEqual(used, declared)

    def test_tools_exist(self):

        tools = load_tools()

        for template_id in helpers.all_templates():
            for message in load_template(template_id)["messages"]:
                call = message.get("tool_call")
                if call:
                    with self.subTest(template=template_id, tool=call["name"]):
                        self.assertIn(call["name"], tools)

    def test_no_consecutive_user_or_tool_messages(self):

        # Consecutive assistant messages are folded by the normaliser at
        # render time (lint_templates only warns about them); two user or
        # tool messages in a row cannot be repaired automatically.
        problems = [
            (path.name, description)
            for path, _index, description in lint_templates.lint()
            if "'assistant'" not in description
        ]

        self.assertEqual(problems, [])


class TemplateGenerationTest(unittest.TestCase):

    def test_every_template_produces_valid_datapoints(self):

        generator = helpers.DatasetGenerator(21)

        for template_id in helpers.all_templates():
            with self.subTest(template=template_id):
                self.assertIsNotNone(
                    helpers.generate_valid(generator, template_id),
                    "no valid datapoint in 150 attempts"
                )


class GoldenOutputTest(unittest.TestCase):

    def test_fixed_seed_output(self):

        update = os.environ.get("UPDATE_GOLDEN") == "1"

        for template_id in GOLDEN_TEMPLATES:

            helpers.reset_generators(2024)
            generator = helpers.DatasetGenerator(None)
            produced = [helpers.generate_valid(generator, template_id) for _ in range(3)]

            path = ROOT / "tests" / "golden" / f"{template_id.replace('/', '__')}.json"

            if update:
                path.write_text(json.dumps(produced, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
                continue

            with self.subTest(template=template_id):
                self.assertTrue(path.exists(), "missing golden file - run with UPDATE_GOLDEN=1")
                expected = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(produced, expected)


if __name__ == "__main__":
    unittest.main()
