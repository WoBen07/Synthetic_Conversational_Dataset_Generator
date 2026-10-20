import unittest

from helpers import conversation

from synthetic_data_generator.engine.tool_definitions import tool_definitions
from synthetic_data_generator.engine.tool_registry import load_tools
from synthetic_data_generator.engine.validators.grounding_validator import GroundingValidator
from synthetic_data_generator.engine.validators.tool_schema_validator import ToolSchemaValidator


def call(tool_name, /, **arguments):
    return {"tool_call": {"name": tool_name, "arguments": arguments}}


def result(tool_name, content):
    return {"name": tool_name, "content": content}


CONTEXT = ("system", "Today is Monday. Patient: Anna Weber (patient_id: p9, room 2004).")


class ToolSchemaValidatorTest(unittest.TestCase):

    def errors(self, *messages):
        return ToolSchemaValidator().validate(conversation(*messages))

    def test_valid_call_and_result(self):

        self.assertEqual(self.errors(
            CONTEXT,
            ("assistant", call("alert_staff", patient_id="p9", room_number="2004", urgency="high")),
            ("tool", result("alert_staff", {"status": "notified", "eta": "immediate"})),
        ), [])

    def test_call_problems(self):

        cases = {
            "unknown tool": call("teleport", room="2004"),
            "unknown argument": call("navigate_to", room="2004", speed="fast"),
            "missing argument": call("alert_staff", room_number="2004"),
            "enum": call("alert_staff", room_number="2004", urgency="extreme"),
            "type": call("remind_patient", patient_id="p9", message=42),
            "requires_one_of": call("find_patient"),
        }

        for case, message in cases.items():
            with self.subTest(case=case):
                self.assertEqual(len(self.errors(("assistant", message))), 1)

    def test_result_problems(self):

        self.assertEqual(len(self.errors(
            ("tool", result("remind_patient", {"status": "maybe"})),
        )), 1)
        self.assertEqual(len(self.errors(
            ("tool", result("remind_patient", {"status": "success", "extra": 1})),
        )), 1)

    def test_nullable_output(self):

        self.assertEqual(self.errors(
            ("tool", result("get_patient_appointment", {"patient_id": "p9", "name": "A", "appointment": None})),
        ), [])
        self.assertEqual(len(self.errors(
            ("tool", result("remind_patient", {"status": None})),
        )), 1)


class SchemaDrivenGroundingTest(unittest.TestCase):

    def errors(self, *messages):
        return GroundingValidator().validate(conversation(*messages))

    def test_known_values_must_match_exactly(self):

        self.assertEqual(self.errors(
            CONTEXT, ("assistant", call("get_patient_appointment", patient_id="p9")),
        ), [])
        # "p99" contains "p9" but is a different ID
        self.assertEqual(len(self.errors(
            CONTEXT, ("assistant", call("get_patient_appointment", patient_id="p99")),
        )), 1)

    def test_alert_room_must_be_known(self):

        self.assertEqual(len(self.errors(
            CONTEXT,
            ("assistant", call("alert_staff", patient_id="p9", room_number="3001", urgency="low")),
        )), 1)

    def test_robot_cannot_ground_its_own_claims(self):

        self.assertEqual(len(self.errors(
            ("user", "Take Anna to her appointment."),
            ("assistant", "The appointment moved to the Sunroom."),
            ("assistant", call("navigate_to", room="Sunroom")),
        )), 1)

    def test_room_from_tool_result(self):

        self.assertEqual(self.errors(
            ("user", "Take Anna to her appointment."),
            ("tool", result("get_patient_appointment", {"appointment": {"location": "MRI Room 1"}})),
            ("assistant", call("navigate_to", room="MRI Room 1")),
        ), [])


class ToolDefinitionsTest(unittest.TestCase):

    def test_every_tool_is_exported(self):

        definitions = {d["function"]["name"]: d for d in tool_definitions()}

        self.assertEqual(set(definitions), set(load_tools()))

        for name, definition in definitions.items():
            with self.subTest(tool=name):
                self.assertEqual(definition["type"], "function")
                self.assertTrue(definition["function"]["description"])
                self.assertEqual(definition["function"]["parameters"]["type"], "object")

    def test_parameters(self):

        alert = next(d for d in tool_definitions(["alert_staff"]))["function"]
        properties = alert["parameters"]["properties"]

        self.assertEqual(alert["parameters"]["required"], ["room_number", "urgency"])
        self.assertEqual(properties["urgency"], {"type": "string", "enum": ["low", "medium", "high"]})
        # generator-internal keys are not exported
        self.assertNotIn("source", properties["room_number"])
        self.assertNotIn("format", properties["room_number"])

    def test_requires_one_of_is_stated(self):

        find = tool_definitions(["find_patient"])[0]["function"]

        self.assertEqual(find["parameters"]["required"], [])
        self.assertIn("at least one of", find["description"].lower())


if __name__ == "__main__":
    unittest.main()
