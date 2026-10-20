import unittest

from helpers import HOSPITAL, conversation

from synthetic_data_generator.engine.validators.grounding_validator import GroundingValidator
from synthetic_data_generator.engine.validators.language_validator import LanguageValidator
from synthetic_data_generator.engine.validators.structure_validator import StructureValidator


def call(tool_name, /, **arguments):
    return {"tool_call": {"name": tool_name, "arguments": arguments}}


def tool(name, content):
    return {"name": name, "content": content}


class GroundingTest(unittest.TestCase):

    def errors(self, *messages):
        return GroundingValidator(HOSPITAL.tools).validate(conversation(*messages))

    def test_unknown_patient_id(self):

        errors = self.errors(
            ("user", "What is my appointment?"),
            ("assistant", call("get_patient_appointment", patient_id="p9")),
        )

        self.assertEqual(len(errors), 1)
        self.assertIn("p9", errors[0])

    def test_patient_id_from_context_or_tool(self):

        self.assertEqual(self.errors(
            ("system", "Patient: Anna Weber (patient_id: p9, room 2004)."),
            ("user", "What is my appointment?"),
            ("assistant", call("get_patient_appointment", patient_id="p9")),
        ), [])

        self.assertEqual(self.errors(
            ("user", "Find Weber."),
            ("assistant", call("find_patient", name="Weber")),
            ("tool", tool("find_patient", {"matches": [{"patient_id": "p4"}]})),
            ("assistant", call("remind_patient", patient_id="p4", message="Reminder.")),
        ), [])

    def test_search_term_nobody_said(self):

        errors = self.errors(
            ("user", "Can you look up my appointment?"),
            ("assistant", call("find_patient", name="Vogel")),
        )

        self.assertEqual(len(errors), 1)

    def test_search_term_from_earlier_turns(self):

        # first and last name in separate turns, room from a tool result
        self.assertEqual(self.errors(
            ("user", "Please remind Anna."),
            ("user", "Her last name is Weber."),
            ("assistant", call("find_patient", name="Anna Weber")),
            ("tool", tool("find_patient", {"matches": [{"room_number": "2004"}]})),
            ("assistant", call("find_patient", room_number="2004")),
        ), [])

    def test_reason_copied_from_user(self):

        errors = self.errors(
            ("system", "Patient: A (patient_id: p1, room 1001)."),
            ("user", "Can you check my blood pressure?"),
            ("assistant", call("notify_staff", patient_id="p1", reason="Can you check my blood pressure?")),
        )

        self.assertTrue(any("copies a user message" in e for e in errors))

    def test_room_with_article(self):

        errors = self.errors(
            ("user", "Take me to the Sunroom."),
            ("assistant", call("navigate_to", room="the Sunroom")),
        )

        self.assertTrue(any("article" in e for e in errors))


class StructureTest(unittest.TestCase):

    def errors(self, *messages):
        return StructureValidator().validate(conversation(*messages))

    def test_must_start_with_user_or_system(self):

        self.assertTrue(self.errors(("assistant", "Hello!"), ("user", "Hi")))
        self.assertEqual(self.errors(("system", "Today is Monday."), ("assistant", "Hello!")), [])

    def test_system_only_first(self):

        self.assertTrue(self.errors(("user", "Hi"), ("system", "Context")))

    def test_tool_result_needs_assistant_reaction(self):

        self.assertTrue(self.errors(
            ("user", "Find Weber"),
            ("assistant", call("find_patient", name="Weber")),
            ("tool", tool("find_patient", {"matches": []})),
            ("user", "While that loads, tell me a joke."),
        ))

    def test_empty_assistant_message(self):

        self.assertTrue(self.errors(("user", "Hi"), ("assistant", "  ")))


class LanguageTest(unittest.TestCase):

    def test_checks_text_and_tool_arguments(self):

        errors = LanguageValidator().validate(conversation(
            ("user", "Is it a ECG appointment?"),
            ("assistant", call("remind_patient", patient_id="p1",
                               message="Your neurology appointment appointment is today.")),
        ))

        self.assertEqual(len(errors), 2)

    def test_tool_results_are_not_checked(self):

        self.assertEqual(LanguageValidator().validate(conversation(
            ("user", "Hi"),
            ("tool", tool("x", "a MRI a MRI")),
        )), [])


if __name__ == "__main__":
    unittest.main()
