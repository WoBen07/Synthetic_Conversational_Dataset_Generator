"""The home_assistant domain: a German assistant for any home, and the engine
features it brought along."""

import json
import re
import tempfile
import unittest
from collections import Counter
from pathlib import Path
from unittest import mock

import helpers

from dataset_forge.engine import dataset_merger as merger
from dataset_forge.engine import orchestrator
from dataset_forge.engine.domain import configured_domains, load_domain
from dataset_forge.engine.robot_context import build_robot_context
from dataset_forge.engine.template_renderer import TemplateRenderer
from dataset_forge.engine.tool_definitions import tool_definitions, write_tool_schemas
from dataset_forge.engine.validators.grounding_validator import GroundingValidator
from dataset_forge.engine.validators.language_validator import LanguageValidator
from dataset_forge.engine.validators.tool_schema_validator import ToolSchemaValidator
from dataset_forge.domains.home_assistant import finish_context
from dataset_forge.domains.home_assistant.generators import devices
from dataset_forge.domains.home_assistant.hass_mapping import to_home_assistant_intents
from dataset_forge.domains.home_assistant.postprocess import _as_speech, postprocess
from dataset_forge.domains.home_assistant.validators import (
    LightCapabilityValidator,
    SecurityConfirmationValidator,
)


DOMAIN = load_domain("home_assistant")
HASS = load_domain("home_assistant@hass")

# A capitalized article or preposition form in the middle of a sentence
MID_SENTENCE_CAPITAL = re.compile(r"(?<=[a-zäöüß,] )(Der|Die|Das|Den|Dem|Des|Im|In|Auf)\b")


def call(tool_name, /, **arguments):
    return {"tool_call": {"name": tool_name, "arguments": arguments}}


def tool_result(tool_name, content):
    return {"name": tool_name, "content": content}


def pool(template_id, variable="request"):
    return helpers.DatasetGenerator(1, domain=DOMAIN).schemaloader.load(
        DOMAIN.language_path(template_id)
    )["variables"][variable]


def generator(seed=5, domain=DOMAIN):
    return helpers.DatasetGenerator(seed, domain=domain)


def samples(template_id, amount=30, domain=DOMAIN):

    made = generator(domain=domain)

    return [helpers.generate_valid(made, template_id) for _ in range(amount)]


def calls(datapoint):
    return [m["tool_call"] for m in datapoint["messages"] if m.get("tool_call")]


def tool_names(datapoint):
    return [c["name"] for c in calls(datapoint)]


def inventory(datapoint):
    return datapoint["messages"][0]["content"].split("Geräte im Zuhause:\n")[1]


def home_of(scenario=None, **entities):

    context = {"home": {"kind": "home"}, **entities}

    finish_context(context, {"home": scenario or {}})

    return context["home"]["inventory"]


def line_of(text, room):
    return next((line for line in text.split("\n") if line.startswith(f"- {room}:")), None)


class TemplatesTest(unittest.TestCase):

    def test_every_template_produces_valid_datapoints(self):

        made = generator(3)

        for template_id in helpers.all_templates(DOMAIN):
            with self.subTest(template=template_id):
                self.assertIsNotNone(helpers.generate_valid(made, template_id))

    def test_scenario_and_language_exist_and_leaf_names_are_unique(self):
        # The output folder and important_templates go by the leaf name.

        templates = helpers.all_templates(DOMAIN)

        self.assertEqual(len({t.split("/")[-1] for t in templates}), len(templates))

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

    def test_amounts_are_reachable(self):
        # An amount above what exists makes generate_many give up.

        for template_id, amount in orchestrator.plan_amounts(DOMAIN, verbose=False).items():

            made = generator(9)

            seen = {
                json.dumps(helpers.generate_valid(made, template_id)["messages"], sort_keys=True)
                for _ in range(40)
            }

            with self.subTest(template=template_id):
                # Nearly all draws differ, so the space is far above the amount.
                self.assertGreater(len(seen), 30)
                self.assertLess(amount, 1000)


class GermanTextTest(unittest.TestCase):

    def test_no_capitalized_article_mid_sentence(self):

        for template_id in helpers.all_templates(DOMAIN):

            for datapoint in samples(template_id, 25):

                for message in datapoint["messages"]:

                    if message["role"] not in ("user", "assistant") or not message.get("content"):
                        continue

                    with self.subTest(template=template_id, text=message["content"]):
                        self.assertIsNone(MID_SENTENCE_CAPITAL.search(message["content"]))

    def test_every_noun_form_has_the_right_article(self):

        led = devices.noun_forms("LED-Streifen", "m", "s")

        self.assertEqual((led["nom"], led["acc"], led["dat"], led["gen"], led["pron_acc"]),
                         ("der LED-Streifen", "den LED-Streifen", "dem LED-Streifen", "des LED-Streifens", "ihn"))

    def test_an_unnamed_robot_is_declined(self):

        with mock.patch.object(devices.random, "random", return_value=0.0):
            robot = devices.vacuum()

        self.assertEqual(robot["value"], "")
        self.assertEqual((robot["reply"], robot["reply_acc"], robot["reply_dat"]),
                         ("der Saugroboter", "den Saugroboter", "dem Saugroboter"))


class AnyHomeTest(unittest.TestCase):

    def test_every_conversation_has_another_home(self):

        homes = {inventory(d) for d in samples("light/light_power", 30)}

        self.assertGreater(len(homes), 25)

    def test_the_target_is_in_the_home(self):

        for datapoint in samples("light/light_power", 40):

            arguments = calls(datapoint)[0]["arguments"]

            line = line_of(inventory(datapoint), arguments["room"])

            self.assertIsNotNone(line)
            self.assertIn("Licht", line)

            if "light" in arguments:
                self.assertIn(arguments["light"], line)

    def test_robot_name_is_a_variable(self):

        said = Counter()

        for datapoint in samples("vacuum/vacuum_start", 120):

            line = next(l for l in inventory(datapoint).split("\n") if l.startswith("- Saugroboter"))

            said[line] += 1

            name = line.partition(": ")[2]

            if name:
                self.assertIn(name, datapoint["messages"][-1]["content"])

        self.assertGreater(len(said), 12)
        self.assertIn("- Saugroboter", said)

    def test_no_name_of_one_home_is_left(self):

        self.assertIn("Fridolin", [name for name, _ in devices.ROBOT_NAMES])

        for folder in ("language", "tools", "templates", "scenarios", "entities"):
            for path in (DOMAIN.root / folder).rglob("*"):
                if path.is_file():
                    with self.subTest(path=path.name):
                        self.assertNotIn("Fridolin", path.read_text(encoding="utf-8"))

        self.assertNotIn("Fridolin", (DOMAIN.root / "domain.yaml").read_text(encoding="utf-8"))

    def test_system_message_is_tidy(self):

        system = samples("light/light_power", 1)[0]["messages"][0]["content"]

        self.assertTrue(system.startswith("Du bist der Sprachassistent"))
        self.assertNotIn("Today", system)
        self.assertNotIn("\n ", system)
        self.assertEqual(system, system.strip())


class HomeTest(unittest.TestCase):

    def room(self, name):
        return {"home_room": name}

    def test_required_devices_are_there(self):

        for _ in range(20):
            text = home_of({"require": {"room": ["heating", "blinds"]}}, room=self.room("Küche"))
            self.assertIn("Heizung", line_of(text, "Küche"))
            self.assertIn("Rollläden", line_of(text, "Küche"))

    def test_absent_devices_are_not(self):

        for _ in range(40):

            text = home_of({"absent": ["vacuum", "locks", "alarm", "garage"], "room_absent": {"room": ["blinds"]}}, room=self.room("Küche"))

            self.assertNotIn("Saugroboter", text)
            self.assertNotIn("Schlösser", text)
            self.assertNotIn("Alarmanlage", text)
            self.assertNotIn("Garagentor", text)
            self.assertNotIn("Rollläden", line_of(text, "Küche"))

    def test_a_missing_room_stays_missing(self):

        for _ in range(40):

            text = home_of(missing={"home_room": "Keller", "absent": True})

            self.assertIsNone(line_of(text, "Keller"))

    def test_a_missing_room_cannot_also_be_needed(self):

        with self.assertRaises(ValueError):
            home_of(missing={"home_room": "Keller", "absent": True}, room=self.room("Keller"))

    def test_only_one_name_of_a_room(self):

        for _ in range(60):

            text = home_of(room=self.room("Bad"))

            self.assertIsNone(line_of(text, "Badezimmer"))

        with self.assertRaises(ValueError):
            home_of(room=self.room("Bad"), other=self.room("Badezimmer"))

    def test_single_room(self):

        text = home_of({"single_room": True}, light={"home_room": "Küche", "home_light": ""})

        self.assertEqual(sum(": " in line and line.split(":")[0][2:] in devices.ROOMS for line in text.split("\n")), 1)

    def test_more_than_one_room_to_mean(self):

        for _ in range(40):

            text = home_of({"min_light_rooms": 2}, light={"home_room": "Küche", "home_light": ""})

            rooms = [l for l in text.split("\n") if l.split(":")[0][2:] in devices.ROOMS and "Licht" in l]

            self.assertGreaterEqual(len(rooms), 2)

    def test_a_whole_home_request_finds_the_device(self):

        for _ in range(80):

            text = home_of({"require_some": ["heating"]})

            indoor = [l for l in text.split("\n") if l.split(":")[0][2:] in devices.INDOOR_ROOMS]

            self.assertTrue(any("Heizung" in l for l in indoor), text)

    def test_outdoor_rooms_are_not_heated(self):

        for _ in range(40):

            text = home_of(room=self.room("Balkon"))

            self.assertNotIn("Heizung", line_of(text, "Balkon"))

    def test_absent_scene_and_switch_are_not_drawn(self):

        for _ in range(60):

            text = home_of(scene={"home_absent_scene": "Kino"}, switch={"home_absent_switch": "Radio"})

            self.assertNotIn("Kino", text)
            self.assertNotIn("Radio", text)

    def test_same_light_in_two_rooms_only_when_asked_for(self):

        for datapoint in samples("light/light_power", 40):

            names = [
                name
                for line in inventory(datapoint).split("\n")
                for match in re.findall(r"Licht \((.*?)\)", line)
                for name in match.split(", ")
            ]

            self.assertEqual(len(names), len(set(names)))


class InitialDataTest(unittest.TestCase):
    """The phrases of Data/inital_data.txt can all be generated."""

    def rendered(self, template_id, context, variable="request"):

        renderer = TemplateRenderer(context, fix_articles=False)

        return {renderer.render(phrase) for phrase in pool(template_id, variable)}

    def light(self, room, name="Licht", gender="n", genitive="s", color_subject="die Lichtfarbe"):

        return {"color_subject": color_subject, "room": room, **devices.noun_forms(name, gender, genitive), **devices.room_forms(room)}

    def string_lights(self, room):
        return self.light(room, "Lichterkette", "f", "", "die Farbe der Lichterkette")

    def test_light_phrases(self):

        living_room = self.light("Wohnzimmer")
        office = self.light("Büro")

        cases = [
            ("light/light_power", {"light": living_room, "power": {"word": "an"}}, "Mach das Licht im Wohnzimmer an."),
            ("light/light_power", {"light": living_room, "power": {"word": "aus"}}, "Mach das Licht im Wohnzimmer aus."),
            ("light/light_power", {"light": living_room, "power": {"word": "an"}}, "Schalte das Licht im Wohnzimmer an."),
            ("light/light_power", {"light": self.string_lights("Schlafzimmer"), "power": {"word": "aus"}}, "Schalte die Lichterkette im Schlafzimmer aus."),
            ("light/light_dimmer", {"light": office}, "Dimme das Licht im Büro."),
            ("light/light_brightness_set", {"light": office, "brightness": {"pct": 40}}, "Dimme das Licht im Büro auf 40%."),
            ("light/light_brightness_set", {"light": self.string_lights("Wohnzimmer"), "brightness": {"pct": 40}}, "Dimme die Lichterkette im Wohnzimmer auf 40%."),
            ("light/light_dimmer", {"light": self.string_lights("Wohnzimmer")}, "Dimme die Lichterkette im Wohnzimmer."),
            ("light/light_brighter", {"light": office}, "Mache das Licht im Büro heller."),
            ("light/light_color_supported", {"light": living_room, "color": {"german": "rot"}}, "Ändere die Lichtfarbe im Wohnzimmer zu rot."),
            ("light/light_color_temperature_supported", {"light": living_room, "direction": {"comparative": "wärmer"}}, "Mache das Licht im Wohnzimmer wärmer."),
            ("light/light_color_temperature_supported", {"light": living_room, "direction": {"comparative": "kälter"}}, "Mache das Licht im Wohnzimmer kälter."),
        ]

        for template_id, context, phrase in cases:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.rendered(template_id, context))

    def test_heating_phrases(self):

        context = {"room": {"name": "Wohnzimmer", **devices.room_forms("Wohnzimmer")}, "temperature": {"spoken": "25"}}

        requests = self.rendered("heating/heating_set_temperature", context)

        self.assertIn("Heize das Wohnzimmer auf 25 Grad.", requests)
        self.assertIn("Stelle die Heizung im Wohnzimmer auf 25 Grad.", requests)
        self.assertIn("Schalte die Heizung aus.", pool("heating/heating_off"))
        self.assertIn("Schalte die Heizung an.", pool("heating/heating_on"))

    def test_vacuum_phrases(self):

        fridolin = {"vacuum": {"nom_cap": "Fridolin", "nom": "Fridolin", "acc": "Fridolin", "pronoun": "er"}}
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

    def test_heating_off_means_frost_protection(self):

        for template_id in ("heating/heating_off", "heating/heating_off_room", "multi/multi_leaving_home"):
            with self.subTest(template=template_id):
                modes = [c["arguments"].get("mode") for c in calls(samples(template_id, 1)[0])]
                self.assertIn("frost_protection", modes)

    def test_the_light_of_a_room_has_no_light_argument(self):

        names = {
            "light" in calls(d)[0]["arguments"]
            for d in samples("light/light_power", 40)
        }

        self.assertEqual(names, {True, False})

        for datapoint in samples("known_room/known_room_light", 10):
            self.assertNotIn("light", calls(datapoint)[0]["arguments"])

    def test_room_comes_from_the_list_when_the_user_does_not_say_it(self):

        for datapoint in samples("light/light_power_named", 20):

            arguments = calls(datapoint)[0]["arguments"]

            self.assertNotIn(arguments["room"].lower(), datapoint["messages"][1]["content"].lower())
            self.assertIn(arguments["light"], line_of(inventory(datapoint), arguments["room"]))

    def test_white_only_light_gets_no_color_call(self):

        for template_id in ("light/light_color_not_supported", "light/light_color_temperature_not_supported"):
            with self.subTest(template=template_id):
                self.assertEqual(tool_names(samples(template_id, 1)[0]), ["get_light_capabilities"])

    def test_white_is_never_refused_to_a_white_only_light(self):

        self.assertNotIn("white", {devices.non_white_light_color()["value"] for _ in range(200)})

    def test_known_room_asks_nothing_and_says_where(self):

        for datapoint in samples("known_room/known_room_light", 10):

            self.assertEqual(datapoint["messages"][2].get("tool_call", {}).get("name"), "set_light_power")

            room = calls(datapoint)[0]["arguments"]["room"]

            self.assertIn(f"aus diesem Raum mit dir: {room}.", datapoint["messages"][0]["content"])

    def test_question_back_only_without_a_location(self):

        self.assertNotIn("aus diesem Raum", samples("clarification/clarify_light_room", 1)[0]["messages"][0]["content"])
        self.assertTrue(samples("clarification/clarify_light_room", 1)[0]["messages"][2]["content"])

    def test_single_room_home_asks_nothing(self):

        for datapoint in samples("clarification/single_room_no_question", 10):
            self.assertEqual(tool_names(datapoint), ["set_light_power"])
            self.assertEqual(datapoint["messages"][2].get("tool_call", {}).get("name"), "set_light_power")

    def test_same_device_in_two_rooms_is_a_real_question(self):

        for datapoint in samples("clarification/clarify_same_device", 15):

            name = calls(datapoint)[0]["arguments"]["light"]

            self.assertEqual(inventory(datapoint).count(name), 2, inventory(datapoint))

    def test_several_actions_are_several_calls(self):

        self.assertEqual(tool_names(samples("multi/multi_two_rooms", 1)[0]), ["set_light_power", "set_light_power"])
        self.assertEqual(tool_names(samples("multi/multi_light_and_heating", 1)[0]), ["set_light_power", "set_heating_mode"])
        self.assertEqual(tool_names(samples("multi/multi_leaving_home", 1)[0]), ["set_all_lights_power", "set_heating_mode"])

    def test_correction_undoes_the_wrong_room(self):

        first, undo, right = calls(samples("followup/followup_correction", 1)[0])

        self.assertEqual(first["arguments"]["state"], "on")
        self.assertEqual(undo["arguments"], {**first["arguments"], "state": "off"})
        self.assertEqual(right["arguments"]["state"], "on")
        self.assertNotEqual(right["arguments"]["room"], first["arguments"]["room"])

    def test_thanks_calls_nothing_more(self):

        self.assertEqual(tool_names(samples("followup/followup_thanks", 1)[0]), ["set_light_power"])

    def test_what_is_not_possible_calls_nothing(self):

        templates = [
            t for t in helpers.all_templates(DOMAIN)
            if t.split("/")[0] in ("not_in_home", "impossible", "no_tool")
        ]

        self.assertGreater(len(templates), 10)

        for template_id in templates:
            with self.subTest(template=template_id):
                self.assertEqual(tool_names(samples(template_id, 1)[0]), [])

    def test_not_in_home_is_true_for_the_home(self):

        for datapoint in samples("not_in_home/no_vacuum", 15):
            self.assertNotIn("Saugroboter", inventory(datapoint))

        for datapoint in samples("not_in_home/no_garage", 15):
            self.assertNotIn("Garagentor", inventory(datapoint))

        for datapoint in samples("not_in_home/no_alarm", 15):
            self.assertNotIn("Alarmanlage", inventory(datapoint))

        for datapoint in samples("not_in_home/no_lock", 15):
            self.assertNotIn("Schlösser", inventory(datapoint))

        for datapoint in samples("not_in_home/unknown_scene", 15):

            line = next((l for l in inventory(datapoint).split("\n") if l.startswith("- Szenen")), "")

            self.assertFalse(any(
                scene.lower() in datapoint["messages"][1]["content"].lower()
                for scene in line.removeprefix("- Szenen: ").split(", ") if scene
            ))

    def test_a_room_without_the_device_says_so_truthfully(self):

        for template_id, device in (
            ("not_in_home/no_blinds_in_room", "Rollläden"),
            ("not_in_home/no_heating_in_room", "Heizung"),
            ("not_in_home/no_media_in_room", "Musik"),
        ):

            made = generator()

            for _ in range(15):

                scenario = DOMAIN.paths(template_id)

                from dataset_forge.engine.scenario_builder import ScenarioBuilder

                context = ScenarioBuilder(scenario[0], DOMAIN).generate()

                with self.subTest(template=template_id):
                    self.assertNotIn(device, line_of(context["home"]["inventory"], context["room"]["name"]))

    def test_whole_home_requests_find_the_device(self):

        for datapoint in samples("heating/heating_off", 40):
            self.assertIn("Heizung", inventory(datapoint))

        for datapoint in samples("light/light_all", 40):
            self.assertIn("Licht", inventory(datapoint))

    def test_half_degrees(self):

        spoken = {devices.target_temperature()["spoken"] for _ in range(300)}

        self.assertTrue(any("," in value for value in spoken))

        found = False

        for datapoint in samples("heating/heating_set_temperature", 80):

            value = calls(datapoint)[0]["arguments"]["temperature"]

            if isinstance(value, float):
                found = True
                self.assertIn(str(value).replace(".", ","), datapoint["messages"][1]["content"])

        self.assertTrue(found)

    def test_opening_up_asks_first_and_a_no_calls_nothing(self):

        for template_id, tool in (
            ("security/lock_open_confirmed", "set_lock"),
            ("security/alarm_disarm_confirmed", "set_alarm"),
            ("security/garage_open_confirmed", "set_garage_door"),
        ):
            with self.subTest(template=template_id):

                datapoint = samples(template_id, 1)[0]

                self.assertEqual(tool_names(datapoint), [tool])
                self.assertTrue(datapoint["messages"][2]["content"].endswith("?"))

        for template_id in ("security/lock_open_declined", "security/alarm_disarm_declined", "security/garage_open_declined"):
            with self.subTest(template=template_id):
                self.assertEqual(tool_names(samples(template_id, 1)[0]), [])

    def test_locking_up_does_not_ask(self):

        for template_id in ("security/lock_close", "security/alarm_arm", "security/garage_close"):
            with self.subTest(template=template_id):
                self.assertTrue(samples(template_id, 1)[0]["messages"][2].get("tool_call"))


class SpeechTest(unittest.TestCase):

    def test_looks_like_a_recognizer(self):

        with mock.patch("random.random", return_value=0.9):
            self.assertEqual(_as_speech("Mach das Licht, bitte, an."), "mach das licht bitte an")

    def test_keeps_numbers(self):

        with mock.patch("random.random", return_value=0.9):
            self.assertEqual(_as_speech("Stell auf 21,5 Grad."), "stell auf 21,5 grad")
            self.assertEqual(_as_speech("Dimme auf 40%."), "dimme auf 40 prozent")

    def test_only_the_user_side_of_some_conversations(self):

        made = samples("light/light_power", 150)

        spoken = [
            d for d in made
            if d["messages"][1]["content"] == d["messages"][1]["content"].lower()
        ]

        self.assertTrue(20 < len(spoken) < 90, len(spoken))

        for datapoint in spoken:
            self.assertTrue(datapoint["messages"][-1]["content"][0].isupper())

    def test_grounding_survives_it(self):

        for datapoint in samples("heating/heating_set_temperature", 40):
            self.assertEqual(generator().validator.validate(datapoint), [])


class ValidatorsTest(unittest.TestCase):

    TARGET = {"room": "Büro"}

    def errors(self, *messages):
        return LightCapabilityValidator().validate(helpers.conversation(*messages))

    def check(self, target=None, **capabilities):
        return [
            ("assistant", call("get_light_capabilities", **(target or self.TARGET))),
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
            ("assistant", call("set_light_color", room="Büro", light="Stehlampe", color="red")),
        )), 1)

    def security(self, *messages):
        return SecurityConfirmationValidator().validate(helpers.conversation(*messages))

    def test_opening_needs_a_question_and_an_answer(self):

        unlock = ("assistant", call("set_lock", lock="Haustür", action="unlock"))

        self.assertEqual(len(self.security(("user", "Schließ auf."), unlock)), 1)
        self.assertEqual(self.security(("user", "Schließ auf."), ("assistant", "Wirklich?"), ("user", "Ja."), unlock), [])

    def test_closing_needs_nothing(self):

        self.assertEqual(self.security(("user", "Schließ ab."), ("assistant", call("set_lock", lock="Haustür", action="lock"))), [])

    def grounding(self, *messages):
        return GroundingValidator(DOMAIN.tools, *[DOMAIN.language_rules[k] for k in ("name_prefixes", "decimal_separator")]).validate(helpers.conversation(*messages))

    def test_values_must_have_been_said_or_listed(self):

        system = ("system", "Geräte im Zuhause:\n- Wohnzimmer: Licht, Heizung")
        request = ("user", "Stelle die Heizung im Wohnzimmer auf 25 Grad.")

        self.assertEqual(self.grounding(system, request, ("assistant", call("set_room_temperature", room="Wohnzimmer", temperature=25))), [])
        self.assertEqual(len(self.grounding(system, request, ("assistant", call("set_room_temperature", room="Wohnzimmer", temperature=22)))), 1)
        self.assertEqual(len(self.grounding(system, request, ("assistant", call("set_room_temperature", room="Küche", temperature=25)))), 1)

    def test_a_room_must_be_named_as_listed(self):
        # "Bad" must not pass because of "Badezimmer".

        system = ("system", "- Badezimmer: Licht")

        self.assertEqual(len(self.grounding(system, ("user", "Licht an."), ("assistant", call("set_light_power", room="Bad", state="on")))), 1)

    def test_decimal_comma(self):

        request = ("user", "Stell auf 21,5 Grad, Küche.")

        self.assertEqual(self.grounding(request, ("assistant", call("set_room_temperature", room="Küche", temperature=21.5))), [])
        self.assertEqual(len(self.grounding(request, ("assistant", call("set_room_temperature", room="Küche", temperature=22.5)))), 1)


class NumericRangeTest(unittest.TestCase):

    def errors(self, **arguments):
        return ToolSchemaValidator(DOMAIN.tools).validate(helpers.conversation(
            ("assistant", call("set_light_brightness", room="Büro", **arguments)),
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

    def test_weekday_is_optional_and_intro_comes_first(self):

        wording = {"today": None, "intro": "Hallo.", "speakers": {"x": "Du."}}

        self.assertEqual(build_robot_context({"today": "Monday"}, {"speaker": "x"}, wording), "Hallo. Du.")


class HomeAssistantIntentsTest(unittest.TestCase):

    # Names from https://github.com/OHF-Voice/intents (intents.yaml)
    INTENTS = {
        "HassTurnOn", "HassTurnOff", "HassLightSet", "HassGetState", "HassSetPosition",
        "HassClimateSetTemperature", "HassClimateGetTemperature", "HassVacuumStart",
        "HassVacuumReturnToBase", "HassVacuumCleanArea", "HassMediaPause",
        "HassMediaUnpause", "HassMediaNext", "HassMediaSearchAndPlay",
    }

    def mapped(self, name, **arguments):

        datapoint = {"messages": [
            {"role": "assistant", "tool_call": {"name": name, "arguments": arguments}},
            {"role": "tool", "name": name, "content": {"status": "ok"}},
        ]}

        to_home_assistant_intents(datapoint)

        return datapoint["messages"]

    def test_only_real_intents_are_offered(self):

        self.assertEqual(set(HASS.tools), self.INTENTS)

    def test_every_template_of_the_variant_uses_only_them(self):

        made = generator(domain=HASS)

        for template_id in helpers.all_templates(HASS):
            with self.subTest(template=template_id):

                datapoint = helpers.generate_valid(made, template_id)

                self.assertIsNotNone(datapoint)
                self.assertLessEqual(set(tool_names(datapoint)), self.INTENTS)

    def test_light(self):

        call_message, result = self.mapped("set_light_power", room="Küche", light="Stehlampe", state="on")

        self.assertEqual(call_message["tool_call"], {"name": "HassTurnOn", "arguments": {"area": "Küche", "domain": "light", "name": "Stehlampe"}})
        self.assertEqual(result["name"], "HassTurnOn")

    def test_off_is_turn_off(self):

        self.assertEqual(self.mapped("set_light_power", room="Küche", state="off")[0]["tool_call"]["name"], "HassTurnOff")

    def test_colors_skip_the_check(self):

        datapoint = samples("light/light_color_supported", 1, HASS)[0]

        self.assertEqual(tool_names(datapoint), ["HassLightSet"])
        self.assertIn("color", calls(datapoint)[0]["arguments"])

    def test_what_has_no_intent_is_redrawn(self):

        for name, arguments in (
            ("start_cleaning", {"mode": "mop"}),
            ("control_vacuum", {"action": "pause"}),
            ("set_blinds", {"room": "Küche", "action": "stop"}),
            ("control_media", {"room": "Küche", "action": "volume_up"}),
        ):
            with self.subTest(tool=name):
                with self.assertRaises(ValueError):
                    self.mapped(name, **arguments)

    def test_templates_without_an_intent_are_removed(self):

        templates = helpers.all_templates(HASS)

        for removed in ("vacuum/vacuum_pause", "security/lock_close", "heating/heating_off", "light/light_color_not_supported", "blinds/blinds_stop"):
            self.assertNotIn(removed, templates)

    def test_the_pack_itself_is_not_affected(self):

        self.assertNotIn("HassTurnOn", DOMAIN.tools)
        self.assertEqual(tool_names(samples("light/light_power", 1)[0]), ["set_light_power"])


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

            write_tool_schemas(DOMAIN, directory)

            self.assertIn("Ändert", (Path(directory) / "set_light_color.json").read_text(encoding="utf-8"))

    def test_stale_schemas_are_removed(self):

        with tempfile.TemporaryDirectory() as directory:

            stale = Path(directory) / "removed_tool.json"
            stale.write_text("{}")

            write_tool_schemas(DOMAIN, directory)

            self.assertFalse(stale.exists())


class OutputTest(unittest.TestCase):

    def test_selecting_other_domains_keeps_the_configured_dataset(self):

        self.assertIsNone(orchestrator.merged_dataset_folder(configured_domains()))

        self.assertEqual(
            orchestrator.merged_dataset_folder(["home_assistant"]),
            orchestrator.PROJECT_ROOT / "Datasets" / "home_assistant"
        )

    def test_generating_replaces_old_examples(self):

        with tempfile.TemporaryDirectory() as directory:

            old = Path(directory) / "example_09999.json"
            old.write_text("{}")

            scenario, template, language = DOMAIN.paths("light/light_power")

            generator(11).generate_many(scenario=scenario, template=template, amount=2, output_dir=directory, language_schema=language)

            self.assertFalse(old.exists())
            self.assertEqual(len(list(Path(directory).glob("example_*.json"))), 2)

    def test_output_of_removed_templates_is_removed(self):

        with tempfile.TemporaryDirectory() as directory:

            root = Path(directory)
            (root / "home_assistant" / "light_power").mkdir(parents=True)
            (root / "home_assistant" / "old_template").mkdir()

            with mock.patch.object(orchestrator, "OUTPUT_ROOT", root):
                orchestrator.remove_stale_output(DOMAIN)

            self.assertTrue((root / "home_assistant" / "light_power").exists())
            self.assertFalse((root / "home_assistant" / "old_template").exists())

    def test_merger_writes_schema_files_to_the_given_folder(self):

        with tempfile.TemporaryDirectory() as directory:

            root = Path(directory)
            source = root / "input"
            output = root / "output"

            scenario, template, language = DOMAIN.paths("light/light_power")

            generator(11).generate_many(
                scenario=scenario,
                template=template,
                amount=20,
                output_dir=str(source / "home_assistant" / "light_power"),
                language_schema=language
            )

            with mock.patch.object(merger, "INPUT_FOLDER", source):
                merger.main(domains=["home_assistant"], output_folder=output)

            schemas = output / "tool_schemas" / "home_assistant"

            self.assertEqual({path.stem for path in schemas.glob("*.json")}, set(DOMAIN.tools))
            self.assertEqual(
                list(json.loads((output / "tools.json").read_text(encoding="utf-8"))),
                ["home_assistant"]
            )
            self.assertTrue((output / "train.jsonl").exists())


class PostprocessTest(unittest.TestCase):

    def test_empty_arguments_are_dropped(self):

        datapoint = {"messages": [{"role": "assistant", "tool_call": {"name": "x", "arguments": {"room": "Bad", "light": ""}}}]}

        postprocess(datapoint, DOMAIN)

        self.assertEqual(datapoint["messages"][0]["tool_call"]["arguments"], {"room": "Bad"})


if __name__ == "__main__":
    unittest.main()
