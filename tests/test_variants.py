"""Domain variants: the same pack in another language and/or with other
tool schemas, plus the per-language rules of the engine."""

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import helpers
import yaml

from synthetic_data_generator.engine import dataset_merger as merger
from synthetic_data_generator.engine import domain as domain_module
from synthetic_data_generator.engine import lint_templates, orchestrator
from synthetic_data_generator.engine.config_optimizer import render_block, write_block
from synthetic_data_generator.engine.dataset_generator import DatasetGenerator
from synthetic_data_generator.engine.domain import Domain, deep_merge, list_domains, load_domain
from synthetic_data_generator.engine.languages import LANGUAGES
from synthetic_data_generator.engine.linguistic_resolver import LinguisticResolver
from synthetic_data_generator.engine.new_domain import create_domain
from synthetic_data_generator.engine.tool_definitions import tool_definitions
from synthetic_data_generator.engine.validators.validator import Validator


TEMPLATE = "orders/order_status"

GERMAN_SPEC = {
    "language": "de",
    "robot_context": {
        "today": "Heute ist {today}.",
        "location": "Du bist hier: {location}.",
        "numeric_location": "Raum {value}",
        "records": {"customer": "Kunde: {full_name}."},
        "speakers": {
            "customer": "Du sprichst mit einem Kunden.",
            "staff": "Du sprichst mit dem Personal.",
        },
    },
}

GERMAN_PHRASES = {
    "variables": {
        "order_number": ["48213", "55120"],
        "request": ["Wo ist meine Bestellung {{order_number}}, sagt {{customer.title_last_name}}?"],
        "status": [
            {"value": "shipped", "answer": "Bestellung {{order_number}} ist unterwegs."},
            {"value": "delivered", "answer": "Bestellung {{order_number}} ist angekommen."},
        ],
    }
}

GERMAN_TOOL = {
    "tool": "check_order_status",
    "description": "Sucht den Lieferstatus einer Bestellung.",
    "input": {"order_number": {"description": "Die genannte Bestellnummer."}},
}

# The same tool with another argument name and a second tool
RENAMED_TOOL = {
    "tool": "check_order_status",
    "input": {
        "order_number": None,
        "order_id": {"type": "string", "required": True, "source": "mentioned"},
    },
}

NEW_TOOL = {
    "tool": "cancel_order",
    "description": "Cancels an order.",
    "input": {"order_id": {"type": "string", "required": True}},
    "output": {"status": {"type": "enum", "values": ["cancelled"]}},
}


def write_yaml(path, data):

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")


def add_german(root):

    overlay = root / "variants" / "de"

    write_yaml(overlay / "domain.yaml", GERMAN_SPEC)
    write_yaml(overlay / "language" / "orders" / "order_status.yaml", GERMAN_PHRASES)
    write_yaml(overlay / "tools" / "check_order_status.yaml", GERMAN_TOOL)


def add_other_schema(root, with_template=True):

    overlay = root / "variants" / "v2"

    write_yaml(overlay / "domain.yaml", {})
    write_yaml(overlay / "tools" / "check_order_status.yaml", RENAMED_TOOL)
    write_yaml(overlay / "tools" / "cancel_order.yaml", NEW_TOOL)

    if not with_template:
        return

    template = json.loads((root / "templates" / f"{TEMPLATE}.json").read_text(encoding="utf-8"))

    for message in template["messages"]:
        if message.get("tool_call"):
            message["tool_call"]["arguments"] = {"order_id": "{{order_number}}"}

    path = overlay / "templates" / f"{TEMPLATE}.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(template), encoding="utf-8")


class PackTestCase(unittest.TestCase):

    def setUp(self):

        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)

        self.folder = Path(directory.name)
        self.root = create_domain("shop", "Shop assistant.", self.folder)


class NamesTest(PackTestCase):

    def test_variant_is_addressed_by_qualified_name(self):

        add_german(self.root)

        variant = Domain("shop@de", self.root)

        self.assertEqual((variant.name, variant.base_name, variant.variant), ("shop@de", "shop", "de"))
        self.assertIsNone(Domain("shop", self.root).variant)

    def test_unknown_variant(self):

        with self.assertRaises(FileNotFoundError):
            Domain("shop@fr", self.root)

    def test_unknown_language(self):

        write_yaml(self.root / "variants" / "xx" / "domain.yaml", {"language": "xx"})

        with self.assertRaisesRegex(ValueError, "languages.py"):
            Domain("shop@xx", self.root)

    def test_list_domains_includes_variants(self):

        add_german(self.root)

        with mock.patch.object(domain_module, "DOMAINS_DIR", self.folder):
            self.assertEqual(list_domains(), ["shop", "shop@de"])


class DeepMergeTest(unittest.TestCase):

    def test_merges_dictionaries_and_replaces_the_rest(self):

        base = {"a": {"x": 1, "y": 2}, "b": [1, 2]}

        self.assertEqual(
            deep_merge(base, {"a": {"y": 3}, "b": [9]}),
            {"a": {"x": 1, "y": 3}, "b": [9]}
        )

        self.assertEqual(base, {"a": {"x": 1, "y": 2}, "b": [1, 2]})


class LanguageVariantTest(PackTestCase):

    def setUp(self):

        super().setUp()
        add_german(self.root)
        self.variant = Domain("shop@de", self.root)

    def generate(self, domain=None):

        domain = domain or self.variant
        generator = DatasetGenerator(4, domain=domain)

        return generator, generator.generate_one(*domain.paths(TEMPLATE))

    def test_generates_in_the_language_of_the_variant(self):

        generator, datapoint = self.generate()

        self.assertEqual(generator.validator.validate(datapoint), [])
        self.assertEqual(self.variant.language, "de")
        self.assertIn("Wo ist meine Bestellung", datapoint["messages"][1]["content"])
        self.assertIn("Du sprichst mit einem Kunden.", datapoint["messages"][0]["content"])

    def test_engine_text_follows_the_language(self):

        _, datapoint = self.generate()

        self.assertRegex(
            datapoint["messages"][0]["content"],
            rf"^Heute ist ({'|'.join(LANGUAGES['de']['weekdays'])})\."
        )
        self.assertRegex(datapoint["messages"][1]["content"], r"sagt (Herr|Frau) ")
        self.assertIn(self.variant.generators["weekday"](), LANGUAGES["de"]["weekdays"])

    def test_pack_is_unchanged(self):

        pack = Domain("shop", self.root)

        _, datapoint = self.generate(pack)

        self.assertEqual(pack.language, "en")
        self.assertIn("Today is", datapoint["messages"][0]["content"])
        self.assertEqual(
            pack.tools["check_order_status"]["description"],
            "Looks up the delivery status of an order."
        )

    def test_tool_patch_keeps_what_it_does_not_change(self):

        tool = self.variant.tools["check_order_status"]

        self.assertEqual(tool["description"], GERMAN_TOOL["description"])
        self.assertEqual(tool["input"]["order_number"]["description"], "Die genannte Bestellnummer.")
        self.assertEqual(tool["input"]["order_number"]["source"], "mentioned")
        self.assertEqual(tool["output"]["status"]["values"], ["processing", "shipped", "delivered"])

    def test_untranslated_template_is_skipped_never_mixed(self):

        (self.variant.overlay / "language" / "orders" / "order_status.yaml").unlink()

        self.assertEqual(self.variant.templates(), [])
        self.assertEqual(
            self.variant.translation_gaps(),
            [f"template {TEMPLATE}: no language file (skipped)"]
        )

    def test_complete_translation_has_no_gaps(self):

        self.assertEqual(self.variant.translation_gaps(), [])

    def test_gaps_name_inherited_text(self):

        (self.variant.overlay / "tools" / "check_order_status.yaml").unlink()
        write_yaml(self.variant.overlay / "domain.yaml", {"language": "de"})

        gaps = Domain("shop@de", self.root).translation_gaps()

        self.assertIn("tool check_order_status: description", gaps)
        self.assertIn("tool check_order_status: description of order_number", gaps)
        self.assertIn("domain.yaml: robot_context.speakers.customer", gaps)

    def test_gaps_name_literal_template_text(self):

        path = self.root / "templates" / f"{TEMPLATE}.json"
        template = json.loads(path.read_text(encoding="utf-8"))
        template["messages"][-1]["content"] = "All done: {{status.answer}}"
        path.write_text(json.dumps(template), encoding="utf-8")

        self.assertEqual(
            self.variant.translation_gaps(),
            [f"template {TEMPLATE}: literal text in the template"]
        )

    def test_language_defaults_of_the_system_message(self):

        write_yaml(self.root / "domain.yaml", {"name": "shop", "robot_context": {"speakers": {"customer": "x"}}})

        self.assertEqual(Domain("shop@de", self.root).robot_context["today"], "Heute ist {today}.")
        self.assertEqual(Domain("shop", self.root).robot_context["today"], "Today is {today}.")

    def test_a_pack_template_without_phrases_stays_visible(self):
        # Only translated variants skip them; in a pack it is a broken
        # template, which has to fail.

        (self.root / "language" / "orders" / "order_status.yaml").unlink()

        self.assertEqual(Domain("shop", self.root).templates(), [TEMPLATE])


class ToolSchemaVariantTest(PackTestCase):

    def test_tool_argument_renamed_and_tool_added(self):

        add_other_schema(self.root)

        tools = Domain("shop@v2", self.root).tools

        self.assertEqual(set(tools), {"check_order_status", "cancel_order"})
        self.assertEqual(set(tools["check_order_status"]["input"]), {"order_id"})

        pack = Domain("shop", self.root).tools

        self.assertEqual(set(pack), {"check_order_status"})
        self.assertEqual(set(pack["check_order_status"]["input"]), {"order_number"})

    def test_export_follows_the_variant(self):

        add_other_schema(self.root)

        variant = Domain("shop@v2", self.root)

        definitions = {d["function"]["name"]: d["function"] for d in tool_definitions(variant)}

        self.assertEqual(
            list(definitions["check_order_status"]["parameters"]["properties"]),
            ["order_id"]
        )
        self.assertEqual(definitions["check_order_status"]["parameters"]["required"], ["order_id"])
        self.assertIn("cancel_order", definitions)

    def test_variant_template_is_used_and_validated_against_its_schema(self):

        add_other_schema(self.root)

        variant = Domain("shop@v2", self.root)
        generator = DatasetGenerator(4, domain=variant)

        datapoint = generator.generate_one(*variant.paths(TEMPLATE))

        call = next(m["tool_call"] for m in datapoint["messages"] if m.get("tool_call"))

        self.assertEqual(list(call["arguments"]), ["order_id"])
        self.assertEqual(generator.validator.validate(datapoint), [])

    def test_template_of_the_old_schema_is_rejected(self):

        add_other_schema(self.root, with_template=False)

        variant = Domain("shop@v2", self.root)
        generator = DatasetGenerator(4, domain=variant)

        errors = Validator(variant).validate(generator.generate_one(*variant.paths(TEMPLATE)))

        self.assertTrue(any("unknown argument 'order_number'" in error for error in errors))

    def test_no_translation_means_phrases_are_inherited(self):

        add_other_schema(self.root)

        variant = Domain("shop@v2", self.root)

        self.assertFalse(variant.translated)
        self.assertEqual(variant.language_path(TEMPLATE), self.root / "language" / "orders" / "order_status.yaml")
        self.assertEqual(variant.translation_gaps(), [])

    def test_tools_and_templates_can_be_removed(self):

        write_yaml(self.root / "variants" / "small" / "domain.yaml", {
            "remove_tools": ["check_order_status"],
            "remove_templates": ["orders"],
        })

        variant = Domain("shop@small", self.root)

        self.assertEqual(variant.tools, {})
        self.assertEqual(variant.templates(), [])


class ConfigTest(PackTestCase):

    def test_inherits_settings_but_not_uniqueness_caps(self):

        pack_config = self.root / "config.yaml"
        write_block(render_block({TEMPLATE: 7}, {}, {
            "samples": 1, "max_duplicate_rate": 0, "max_phrase_repeats": 1, "min_amount": 1
        }, 0), pack_config)

        add_german(self.root)

        variant = Domain("shop@de", self.root)

        self.assertEqual(variant.load_config()["default_amount"], 200)
        self.assertNotIn("uniqueness_caps", variant.load_config())

        write_yaml(variant.config_file, {"default_amount": 50})

        self.assertEqual(variant.load_config()["default_amount"], 50)
        self.assertEqual(Domain("shop", self.root).load_config()["uniqueness_caps"], {TEMPLATE: 7})

    def test_optimizer_writes_to_the_variant(self):

        add_other_schema(self.root)

        variant = Domain("shop@v2", self.root)

        self.assertEqual(variant.config_file, self.root / "variants" / "v2" / "config.yaml")


class MergeTest(PackTestCase):

    def test_each_example_gets_the_tools_of_its_variant(self):

        add_german(self.root)
        add_other_schema(self.root)

        source = self.folder / "input"
        output = self.folder / "output"

        with mock.patch.object(domain_module, "DOMAINS_DIR", self.folder), \
                mock.patch.object(merger, "INPUT_FOLDER", source):

            domain_module.load_domain.cache_clear()
            self.addCleanup(domain_module.load_domain.cache_clear)

            names = ["shop", "shop@de", "shop@v2"]

            for name in names:

                variant = load_domain(name)

                scenario, template, language = variant.paths(TEMPLATE)

                DatasetGenerator(3, domain=variant).generate_many(
                    scenario=scenario,
                    template=template,
                    amount=2,
                    output_dir=str(source / name / "order_status"),
                    language_schema=language
                )

            merger.main(domains=names, output_folder=output)

        tools = json.loads((output / "tools.json").read_text(encoding="utf-8"))

        self.assertEqual(sorted(tools), names)

        parameters = {
            name: {
                d["function"]["name"]: list(d["function"]["parameters"]["properties"])
                for d in definitions
            }
            for name, definitions in tools.items()
        }

        self.assertEqual(parameters["shop"], {"check_order_status": ["order_number"]})
        self.assertEqual(parameters["shop@de"], {"check_order_status": ["order_number"]})
        self.assertEqual(parameters["shop@v2"]["check_order_status"], ["order_id"])

        for name in names:

            schema = output / "tool_schemas" / name / "check_order_status.json"

            self.assertEqual(
                json.loads(schema.read_text(encoding="utf-8")),
                next(d for d in tools[name] if d["function"]["name"] == "check_order_status")
            )

        metadata = json.loads((output / "metadata.json").read_text(encoding="utf-8"))

        self.assertEqual(metadata["languages"], {"shop": "en", "shop@de": "de", "shop@v2": "en"})

        path = helpers.PACKAGE_ROOT / "Model_Specific_Preprocessors" / "qwen_preprossor.py"
        spec = importlib.util.spec_from_file_location("qwen_for_variants", path)
        qwen = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(qwen)

        rows = [
            json.loads(line)
            for file in ("train.jsonl", "validation.jsonl")
            for line in (output / file).read_text(encoding="utf-8").splitlines()
        ]

        self.assertEqual({row["metadata"]["domain"] for row in rows}, set(names))

        for row in rows:

            self.assertEqual(qwen.tools_for(row, tools), tools[row["metadata"]["domain"]])

            self.assertEqual(
                row["metadata"]["language"],
                "de" if row["metadata"]["domain"] == "shop@de" else "en"
            )

    def test_dataset_folder_of_a_variant(self):

        self.assertEqual(
            orchestrator.merged_dataset_folder(["home_assistant@en"]).name,
            "home_assistant@en"
        )


class LanguageRulesTest(unittest.TestCase):

    def test_every_language_is_complete(self):

        for code, rules in LANGUAGES.items():
            with self.subTest(language=code):
                self.assertEqual(set(rules), set(LANGUAGES["en"]))
                self.assertEqual(len(rules["weekdays"]), 7)
                self.assertEqual(set(rules["pronouns"]), {"male", "female", "other"})

    def test_german_pronouns_and_title(self):

        context = {"p": {"gender": "female", "last_name": "Weber"}}

        LinguisticResolver(LANGUAGES["de"]["pronouns"]).resolve(context)

        self.assertEqual(context["p"]["pronoun"], "sie")
        self.assertEqual(context["p"]["title_last_name"], "Frau Weber")

    def test_no_title_leaves_no_stray_space(self):

        context = {"p": {"gender": "other", "last_name": "Weber"}}

        LinguisticResolver(LANGUAGES["de"]["pronouns"]).resolve(context)

        self.assertEqual(context["p"]["title_last_name"], "Weber")

    def test_hospital_keeps_english(self):

        context = {"p": {"gender": "male", "last_name": "Weber"}}

        LinguisticResolver(helpers.HOSPITAL.language_rules["pronouns"]).resolve(context)

        self.assertEqual(context["p"]["title_last_name"], "Mr. Weber")
        self.assertIn(helpers.HOSPITAL.weekday(), LANGUAGES["en"]["weekdays"])

    def test_german_room_argument_must_be_bare(self):

        home = load_domain("home_assistant")

        def errors(room):
            return Validator(home).validate(helpers.conversation(
                ("user", "Heize das Wohnzimmer im Wohnzimmer auf 25 Grad."),
                ("assistant", {"tool_call": {"name": "set_room_temperature", "arguments": {"room": room, "temperature": 25}}}),
                ("tool", {"name": "set_room_temperature", "content": {"status": "ok"}}),
                ("assistant", "Erledigt."),
            ))

        self.assertEqual(errors("Wohnzimmer"), [])
        self.assertEqual(len(errors("im Wohnzimmer")), 1)

    def test_german_doubled_article_is_allowed(self):

        home = load_domain("home_assistant")

        self.assertEqual(Validator(home).validate(helpers.conversation(
            ("user", "Das ist die Lampe, die die Küche beleuchtet."),
            ("assistant", "Verstanden."),
        )), [])


class RealVariantsTest(unittest.TestCase):
    """Whatever variants the domain packs have (none need be there)."""

    def test_every_variant_is_complete_and_generates(self):

        for name in list_domains():

            if "@" not in name:
                continue

            variant = load_domain(name)
            generator = DatasetGenerator(21, domain=variant)

            with self.subTest(variant=name):
                self.assertEqual(variant.translation_gaps(), [])

            for template_id in variant.templates():
                with self.subTest(variant=name, template=template_id):
                    self.assertIsNotNone(helpers.generate_valid(generator, template_id))

    def test_lint_covers_variants(self):

        self.assertEqual(
            [p for p in lint_templates.lint() if "'assistant'" not in p[2]],
            []
        )


if __name__ == "__main__":
    unittest.main()
