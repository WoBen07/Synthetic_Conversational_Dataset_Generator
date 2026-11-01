"""The home_assistant domain, and the engine features it brought along:
non-English domains, numeric ranges, tool schemas as JSON files."""

import json
import tempfile
import unittest
from pathlib import Path

import helpers

from synthetic_data_generator.engine import dataset_merger as merger
from synthetic_data_generator.engine import orchestrator
from synthetic_data_generator.engine.domain import configured_domains, load_domain
from synthetic_data_generator.engine.robot_context import build_robot_context
from synthetic_data_generator.engine.template_renderer import TemplateRenderer
from synthetic_data_generator.engine.tool_definitions import tool_definitions, write_tool_schemas
from synthetic_data_generator.engine.validators.grounding_validator import GroundingValidator
from synthetic_data_generator.engine.validators.language_validator import LanguageValidator
from synthetic_data_generator.engine.validators.tool_schema_validator import ToolSchemaValidator
from synthetic_data_generator.domains.home_assistant.generators import devices
from synthetic_data_generator.domains.home_assistant.validators import LightCapabilityValidator


DOMAIN = load_domain("home_assistant")


def call(tool_name, /, **arguments):
    return {"tool_call": {"name": tool_name, "arguments": arguments}}


def tool_result(tool_name, content):
    return {"name": tool_name, "content": content}


def pool(template_id, variable="request"):
    return helpers.DatasetGenerator(1, domain=DOMAIN).schemaloader.load(
        DOMAIN.language_path(template_id)
    )["variables"][variable]


class TemplatesTest(unittest.TestCase):

    def test_every_template_produces_valid_datapoints(self):

        generator = helpers.DatasetGenerator(3, domain=DOMAIN)

        for template_id in helpers.all_templates(DOMAIN):
            with self.subTest(template=template_id):
                self.assertIsNotNone(helpers.generate_valid(generator, template_id))

    def test_scenario_and_language_exist_and_leaf_names_are_unique(self):

        # The output folder and important_templates go by the leaf name.
        templates = helpers.all_templates(DOMAIN)

        self.assertEqual(
            len({template.split("/")[-1] for template in templates}),
            len(templates)
        )

        for template_id in templates:
            with self.subTest(template=template_id):
                self.assertTrue(DOMAIN.scenario_path(template_id).exists())
                self.assertTrue(DOMAIN.language_path(template_id).exists())

    def test_every_tool_is_used(self):

        used = set()

        for template_id in helpers.all_templates(DOMAIN):
            for message in json.loads(DOMAIN.template_path(template_id).read_text(encoding="utf-8"))["messages"]:
                if message.get("tool_call"):
                    used.add(message["tool_call"]["name"])

        self.assertEqual(used, set(DOMAIN.tools))

    def test_limited_templates_can_reach_their_amount(self):
        # The templates with few conversations have their amount set by hand;
        # above what exists, generate_many gives up on the template.

        limited = DOMAIN.load_config()["important_templates"]

        amounts = orchestrator.plan_amounts(DOMAIN, verbose=False)

        for template_id, amount in amounts.items():

            if template_id.split("/")[-1] not in limited:
                continue

            generator = helpers.DatasetGenerator(9, domain=DOMAIN)

            seen = {
                json.dumps(generator.generate_one(*DOMAIN.paths(template_id))["messages"], sort_keys=True)
                for _ in range(amount * 3)
            }

            with self.subTest(template=template_id):
                self.assertGreaterEqual(len(seen), amount)


class InitialDataTest(unittest.TestCase):
    """The phrases of Data/inital_data.txt can all be generated."""

    def rendered(self, template_id, context, variable="request"):

        renderer = TemplateRenderer(context, fix_articles=False)

        return {renderer.render(phrase) for phrase in pool(template_id, variable)}

    def light(self, room, phrase="das Licht"):

        return {
            "phrase": phrase,
            "phrase_cap": phrase.capitalize(),
            "dative": "dem Licht",
            "pronoun_acc": "es",
            "color_subject": "die Lichtfarbe",
            "room": room,
            **devices.room_forms(room),
        }

    def test_light_phrases(self):

        living_room = self.light("Wohnzimmer")
        office = self.light("Büro")

        cases = [
            ("light/light_power", {"light": living_room, "power": {"word": "an"}}, "Mach das Licht im Wohnzimmer an."),
            ("light/light_power", {"light": living_room, "power": {"word": "aus"}}, "Mach das Licht im Wohnzimmer aus."),
            ("light/light_power", {"light": living_room, "power": {"word": "an"}}, "Schalte das Licht im Wohnzimmer an."),
            ("light/light_power", {"light": self.light("Schlafzimmer", "die Lichterkette"), "power": {"word": "aus"}}, "Schalte die Lichterkette im Schlafzimmer aus."),
            ("light/light_dimmer", {"light": office}, "Dimme das Licht im Büro."),
            ("light/light_brightness_set", {"light": office, "brightness": {"pct": 40}}, "Dimme das Licht im Büro auf 40%."),
            ("light/light_brightness_set", {"light": self.light("Wohnzimmer", "die Lichterkette"), "brightness": {"pct": 40}}, "Dimme die Lichterkette im Wohnzimmer auf 40%."),
            ("light/light_dimmer", {"light": self.light("Wohnzimmer", "die Lichterkette")}, "Dimme die Lichterkette im Wohnzimmer."),
            ("light/light_brighter", {"light": office}, "Mache das Licht im Büro heller."),
            ("light/light_color_supported", {"light": living_room, "color": {"german": "rot"}}, "Ändere die Lichtfarbe im Wohnzimmer zu rot."),
            ("light/light_color_temperature_supported", {"light": living_room, "direction": {"comparative": "wärmer"}}, "Mache das Licht im Wohnzimmer wärmer."),
            ("light/light_color_temperature_supported", {"light": living_room, "direction": {"comparative": "kälter"}}, "Mache das Licht im Wohnzimmer kälter."),
        ]

        for template_id, context, phrase in cases:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.rendered(template_id, context))

    def test_heating_phrases(self):

        context = {
            "room": {"name": "Wohnzimmer", **devices.room_forms("Wohnzimmer")},
            "temperature": {"value": 25},
        }

        requests = self.rendered("heating/heating_set_temperature", context)

        self.assertIn("Heize das Wohnzimmer auf 25 Grad.", requests)
        self.assertIn("Stelle die Heizung im Wohnzimmer auf 25 Grad.", requests)
        self.assertIn("Schalte die Heizung aus.", pool("heating/heating_off"))
        self.assertIn("Schalte die Heizung an.", pool("heating/heating_on"))

    def test_vacuum_phrases(self):

        fridolin = {"vacuum": {"nominative_cap": "Fridolin", "accusative": "Fridolin"}}
        saugen = {"mode": {"infinitive": "saugen", "noun": "Saugen"}}
        wischen = {"mode": {"infinitive": "wischen", "noun": "Wischen"}}
        kitchen = {"room": {"name": "Küche", **devices.room_forms("Küche")}}

        whole_home = "vacuum/vacuum_clean_whole_home"

        self.assertIn("Lass Fridolin die ganze Wohnung saugen.", self.rendered(whole_home, {**fridolin, **saugen}))
        self.assertIn("Fridolin soll alles saugen.", self.rendered(whole_home, {**fridolin, **saugen}))
        self.assertIn("Fridolin soll alles wischen.", self.rendered(whole_home, {**fridolin, **wischen}))
        self.assertIn("Fridolin soll die Küche saugen.", self.rendered("vacuum/vacuum_clean_room", {**fridolin, **saugen, **kitchen}))
        self.assertIn("Pausiere Fridolin.", self.rendered("vacuum/vacuum_pause", fridolin))
        self.assertIn("Starte Fridolin.", self.rendered("vacuum/vacuum_start", fridolin))
        self.assertIn("Schicke Fridolin nach Hause.", self.rendered("vacuum/vacuum_return_home", fridolin))


class BehaviourTest(unittest.TestCase):

    def calls(self, datapoint):
        return [m["tool_call"] for m in datapoint["messages"] if m.get("tool_call")]

    def generate(self, template_id):
        return helpers.generate_valid(helpers.DatasetGenerator(5, domain=DOMAIN), template_id)

    def test_heating_off_means_frost_protection(self):

        for template_id in ("heating/heating_off", "heating/heating_off_room"):
            with self.subTest(template=template_id):
                self.assertEqual(self.calls(self.generate(template_id))[0]["arguments"]["mode"], "frost_protection")

    def test_white_only_light_gets_no_color_call(self):

        for template_id in ("light/light_color_not_supported", "light/light_color_temperature_not_supported"):
            with self.subTest(template=template_id):
                self.assertEqual(
                    [c["name"] for c in self.calls(self.generate(template_id))],
                    ["get_light_capabilities"]
                )

    def test_white_is_never_refused_to_a_white_only_light(self):

        self.assertEqual(
            {devices.non_white_light_color()["value"] for _ in range(200)} & {"white"},
            set()
        )

    def test_string_lights_only_in_their_rooms(self):

        for _ in range(200):
            light = devices.light()
            if light["value"] == "string_lights":
                self.assertIn(light["room"], devices.STRING_LIGHT_ROOMS)

    def test_unsupported_device_calls_nothing(self):

        self.assertEqual(self.calls(self.generate("no_tool/unsupported_device")), [])

    def test_system_message_has_no_weekday(self):

        system = self.generate("light/light_power")["messages"][0]["content"]

        self.assertTrue(system.startswith("Du bist der Sprachassistent"))
        self.assertNotIn("Today", system)


class LightCapabilityValidatorTest(unittest.TestCase):

    TARGET = {"room": "Büro", "light": "main"}

    def errors(self, *messages):
        return LightCapabilityValidator().validate(helpers.conversation(*messages))

    def check(self, **capabilities):
        return [
            ("assistant", call("get_light_capabilities", **self.TARGET)),
            ("tool", tool_result("get_light_capabilities", {"status": "ok", **capabilities})),
        ]

    def test_needs_a_confirmed_check(self):

        change = ("assistant", call("set_light_color", **self.TARGET, color="red"))

        self.assertEqual(len(self.errors(change)), 1)
        self.assertEqual(len(self.errors(*self.check(supports_color=False), change)), 1)
        self.assertEqual(self.errors(*self.check(supports_color=True), change), [])

    def test_capabilities_are_per_capability_and_per_light(self):

        self.assertEqual(len(self.errors(
            *self.check(supports_color=True),
            ("assistant", call("adjust_light_color_temperature", **self.TARGET, direction="warmer")),
        )), 1)

        self.assertEqual(len(self.errors(
            *self.check(supports_color=True),
            ("assistant", call("set_light_color", room="Büro", light="string_lights", color="red")),
        )), 1)


class GroundingTest(unittest.TestCase):

    def errors(self, *messages):
        return GroundingValidator(DOMAIN.tools).validate(helpers.conversation(*messages))

    def test_values_must_have_been_said(self):

        request = ("user", "Stelle die Heizung im Wohnzimmer auf 25 Grad.")

        self.assertEqual(self.errors(request, ("assistant", call("set_room_temperature", room="Wohnzimmer", temperature=25))), [])
        self.assertEqual(len(self.errors(request, ("assistant", call("set_room_temperature", room="Wohnzimmer", temperature=22)))), 1)
        self.assertEqual(len(self.errors(request, ("assistant", call("set_room_temperature", room="Küche", temperature=25)))), 1)


class NumericRangeTest(unittest.TestCase):

    def errors(self, **arguments):
        return ToolSchemaValidator(DOMAIN.tools).validate(helpers.conversation(
            ("assistant", call("set_light_brightness", room="Büro", light="main", **arguments)),
        ))

    def test_range_is_validated(self):

        self.assertEqual(self.errors(brightness_pct=100), [])
        self.assertEqual(len(self.errors(brightness_pct=0)), 1)
        self.assertEqual(len(self.errors(brightness_pct=101)), 1)

    def test_range_is_exported(self):

        definition = tool_definitions(DOMAIN, ["set_light_brightness"])[0]
        parameter = definition["function"]["parameters"]["properties"]["brightness_pct"]

        self.assertEqual((parameter["minimum"], parameter["maximum"]), (1, 100))


class NonEnglishDomainTest(unittest.TestCase):

    def test_language_comes_from_the_domain(self):

        self.assertEqual(DOMAIN.language, "de")
        self.assertEqual(helpers.HOSPITAL.language, "en")

    def test_renderer_leaves_german_an_alone(self):

        text = "Schalte das Licht an {{x}}"
        context = {"x": "der Decke"}

        self.assertEqual(TemplateRenderer(context, fix_articles=False).render(text), "Schalte das Licht an der Decke")
        self.assertEqual(TemplateRenderer(context).render(text), "Schalte das Licht a der Decke")

    def test_language_validator_leaves_german_an_alone(self):

        datapoint = helpers.conversation(("user", "Ich mache das Licht an der Decke an."))

        self.assertEqual(LanguageValidator(check_articles=False).validate(datapoint), [])
        self.assertEqual(len(LanguageValidator().validate(datapoint)), 1)

    def test_doubled_words_are_still_checked(self):

        datapoint = helpers.conversation(("user", "Mach das Licht Licht an."))

        self.assertEqual(len(LanguageValidator(check_articles=False).validate(datapoint)), 1)

    def test_weekday_is_optional(self):

        wording = {"today": None, "speakers": {"x": "Hallo."}}

        self.assertEqual(build_robot_context({"today": "Monday"}, {"speaker": "x"}, wording), "Hallo.")


class ToolSchemaFilesTest(unittest.TestCase):

    def test_one_json_file_per_tool(self):

        with tempfile.TemporaryDirectory() as directory:

            paths = write_tool_schemas(DOMAIN, directory)

            self.assertEqual({path.stem for path in paths}, set(DOMAIN.tools))

            for path in paths:
                with self.subTest(tool=path.stem):
                    self.assertEqual(
                        json.loads(path.read_text(encoding="utf-8")),
                        tool_definitions(DOMAIN, [path.stem])[0]
                    )

    def test_on_and_off_stay_strings(self):
        # Unquoted in YAML, on/off would load as booleans.

        definition = tool_definitions(DOMAIN, ["set_light_power"])[0]

        self.assertEqual(
            definition["function"]["parameters"]["properties"]["state"]["enum"],
            ["on", "off"]
        )

    def test_umlauts_are_written_as_is(self):

        with tempfile.TemporaryDirectory() as directory:

            text = (Path(directory) / "set_light_color.json")
            write_tool_schemas(DOMAIN, directory)

            self.assertIn("Ändert", text.read_text(encoding="utf-8"))

    def test_stale_schemas_are_removed(self):

        with tempfile.TemporaryDirectory() as directory:

            stale = Path(directory) / "removed_tool.json"
            stale.write_text("{}")

            write_tool_schemas(DOMAIN, directory)

            self.assertFalse(stale.exists())


class MergeTest(unittest.TestCase):

    def test_selecting_other_domains_keeps_the_configured_dataset(self):

        self.assertIsNone(orchestrator.merged_dataset_folder(configured_domains()))

        self.assertEqual(
            orchestrator.merged_dataset_folder(["home_assistant"]),
            orchestrator.PROJECT_ROOT / "Datasets" / "home_assistant"
        )

        self.assertEqual(
            orchestrator.merged_dataset_folder(["home_assistant", "hospital"]).name,
            "home_assistant+hospital"
        )

    def test_merger_writes_schema_files_to_the_given_folder(self):

        with tempfile.TemporaryDirectory() as directory:

            root = Path(directory)
            source = root / "input"
            output = root / "output"

            generator = helpers.DatasetGenerator(11, domain=DOMAIN)

            scenario, template, language = DOMAIN.paths("light/light_power")

            generator.generate_many(
                scenario=scenario,
                template=template,
                amount=20,
                output_dir=str(source / "home_assistant" / "light_power"),
                language_schema=language
            )

            original = merger.INPUT_FOLDER
            merger.INPUT_FOLDER = source

            try:
                merger.main(domains=["home_assistant"], output_folder=output)
            finally:
                merger.INPUT_FOLDER = original

            schemas = output / "tool_schemas" / "home_assistant"

            self.assertEqual({path.stem for path in schemas.glob("*.json")}, set(DOMAIN.tools))
            self.assertEqual(
                list(json.loads((output / "tools.json").read_text(encoding="utf-8"))),
                ["home_assistant"]
            )
            self.assertTrue((output / "train.jsonl").exists())


if __name__ == "__main__":
    unittest.main()
