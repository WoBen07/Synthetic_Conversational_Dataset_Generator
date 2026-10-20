import unittest

import helpers

from synthetic_data_generator.engine.constraint_resolver import ConstraintResolver
from synthetic_data_generator.engine.entity_refresh import EntityRefresher
from synthetic_data_generator.engine.robot_context import build_robot_context
from synthetic_data_generator.engine.scenario_builder import ScenarioBuilder
from synthetic_data_generator.domains.hospital.generators.appointments import TYPE_LOCATIONS, locations_for
from synthetic_data_generator.domains.hospital.generators.rooms import ALL_FACILITY_ROOMS, PATIENT_ROOMS


class ConstraintTest(unittest.TestCase):

    def test_equal_copies_first_value(self):

        context = {"today": "Monday", "a": {"day": "Friday"}, "b": {"day": "Sunday"}}

        ConstraintResolver().resolve(
            context, [{"type": "equal", "fields": ["today", "a.day", "b.day"]}]
        )

        self.assertEqual((context["a"]["day"], context["b"]["day"]), ("Monday", "Monday"))

    def test_different_rejects_repeats(self):

        with self.assertRaises(ValueError):
            ConstraintResolver().resolve(
                {"a": {"x": 1}, "b": {"x": 1}},
                [{"type": "different", "fields": ["a.x", "b.x"]}]
            )

    def test_refresh_redraws_location_that_does_not_fit(self):

        appointment = {"appointment_type": "blood test", "location": "MRI Room 1"}

        EntityRefresher(helpers.HOSPITAL.refresh_entity).refresh({"appointment": appointment})

        self.assertIn(appointment["location"], locations_for("blood test"))


class RoomPoolTest(unittest.TestCase):

    def test_pools_are_separate(self):

        self.assertFalse(set(PATIENT_ROOMS) & set(ALL_FACILITY_ROOMS))

    def test_every_type_has_two_rooms(self):

        # Templates need two different locations for the same type.
        for appointment_type in TYPE_LOCATIONS:
            with self.subTest(type=appointment_type):
                self.assertGreaterEqual(len(set(locations_for(appointment_type))), 2)


class ScenarioBuilderTest(unittest.TestCase):

    def test_today_constraint_and_context(self):

        helpers.reset_generators(3)

        context = ScenarioBuilder(
            helpers.HOSPITAL.scenario_path("trust_and_honesty/appointment_trust_dispute"),
            helpers.HOSPITAL
        ).generate()

        self.assertEqual(context["appointment"]["day"], context["today"])
        self.assertIn(context["patient"]["patient_id"], context["robot_context"])
        self.assertTrue(context["robot_context"].startswith(f"Today is {context['today']}."))

    def test_appointment_location_fits_type(self):

        helpers.reset_generators(4)

        for _ in range(30):
            context = ScenarioBuilder(
                helpers.HOSPITAL.scenario_path("tool_use/appointment_escort"),
                helpers.HOSPITAL
            ).generate()
            appointment = context["appointment"]
            self.assertIn(appointment["location"], locations_for(appointment["appointment_type"]))
            self.assertIn(context["patient"]["room_number"], PATIENT_ROOMS)


class RobotContextTest(unittest.TestCase):

    def test_full_context(self):

        context = {
            "today": "Tuesday",
            "patient": {"full_name": "Anna Weber", "patient_id": "p7", "room_number": "2004"},
        }

        text = build_robot_context(context, {
            "location": "patient.room_number",
            "patient": "patient",
            "speaker": "patient",
            "note": "You have just entered the room.",
        }, helpers.HOSPITAL.robot_context)

        self.assertEqual(
            text,
            "Today is Tuesday. You are in room 2004. Patient: Anna Weber "
            "(patient_id: p7, room 2004). You are speaking with the patient. "
            "You have just entered the room."
        )

    def test_literal_location_and_minimal_context(self):

        context = {"today": "Friday"}

        wording = helpers.HOSPITAL.robot_context

        self.assertEqual(
            build_robot_context(context, {"location": "the nurses' station", "speaker": "staff"}, wording),
            "Today is Friday. You are in the nurses' station. You are speaking with a member of staff."
        )
        self.assertEqual(build_robot_context(context, {}, wording), "Today is Friday.")

    def test_unknown_speaker_or_record_kind(self):

        context = {"today": "Friday", "x": {}}

        with self.assertRaises(ValueError):
            build_robot_context(context, {"speaker": "pirate"}, helpers.HOSPITAL.robot_context)

        with self.assertRaises(ValueError):
            build_robot_context(context, {"customer": "x"}, helpers.HOSPITAL.robot_context)


if __name__ == "__main__":
    unittest.main()
