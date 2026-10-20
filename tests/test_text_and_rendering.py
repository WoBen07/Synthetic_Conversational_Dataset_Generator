import random
import unittest

import helpers  # noqa: F401  (sets up the import path)

from synthetic_data_generator.engine.text_utils import (
    article_mismatches,
    doubled_words,
    wants_an,
)
from synthetic_data_generator.engine.template_renderer import TemplateRenderer
from synthetic_data_generator.engine.language_generator import LanguageGenerator


class ArticleTest(unittest.TestCase):

    def test_vowel_sounds(self):

        for phrase in ["MRI scan", "ENT appointment", "ECG appointment",
                       "X-ray appointment", "eye examination",
                       "oncology appointment", "ultrasound examination",
                       "hour", "honest answer", "8th floor"]:
            with self.subTest(phrase=phrase):
                self.assertTrue(wants_an(phrase))

    def test_consonant_sounds(self):

        for phrase in ["CT scan", "blood test", "urology appointment",
                       "unique record", "user", "European clinic",
                       "one-off", "hearing test", "1004"]:
            with self.subTest(phrase=phrase):
                self.assertFalse(wants_an(phrase))

    def test_mismatches_are_found(self):

        self.assertEqual(
            article_mismatches("You have a MRI scan and an blood test."),
            ["a MRI", "an blood"]
        )
        self.assertEqual(article_mismatches("You have an MRI scan."), [])

    def test_grades_and_labels_are_ignored(self):

        self.assertEqual(article_mismatches("That is Plan A of three."), [])

    def test_doubled_words(self):

        self.assertEqual(
            doubled_words("your cardiology appointment appointment"),
            ["appointment appointment"]
        )
        self.assertEqual(doubled_words("Bye bye, no no, that that"), [])


class RendererTest(unittest.TestCase):

    def render(self, value, context):
        return TemplateRenderer(context).render(value)

    def test_article_follows_inserted_text(self):

        context = {"t": "MRI scan", "u": "blood test"}

        self.assertEqual(self.render("You have a {{t}}.", context), "You have an MRI scan.")
        self.assertEqual(self.render("An {{u}} is due.", context), "A blood test is due.")

    def test_nested_placeholders(self):

        context = {"phrase": "Hello {{patient.first_name}}", "patient": {"first_name": "Anna"}}

        self.assertEqual(self.render("{{phrase}}!", context), "Hello Anna!")

    def test_whole_entity_keeps_type_without_phrasing_fields(self):

        patient = {"patient_id": "p1", "last_name": "Weber",
                   "title": "Ms.", "title_last_name": "Ms. Weber"}

        rendered = self.render({"matches": ["{{patient}}"]}, {"patient": patient})

        self.assertEqual(rendered, {"matches": [{"patient_id": "p1", "last_name": "Weber"}]})

    def test_used_paths_are_recorded(self):

        renderer = TemplateRenderer({"a": "{{b.c}}", "b": {"c": "x"}, "unused": "y"})

        renderer.render(["{{a}}"])

        self.assertEqual(renderer.used_paths, {"a", "b.c"})

    def test_missing_variable_raises(self):

        with self.assertRaises(KeyError):
            self.render("{{nope}}", {})


class LanguageGeneratorTest(unittest.TestCase):

    def test_records_choices_and_keeps_random_sequence(self):

        schema = {"variables": {"a": ["x", "y", "z"], "b": [{"text": "t1"}, {"text": "t2"}]}}

        random.seed(5)
        expected = [{k: random.choice(v) for k, v in schema["variables"].items()} for _ in range(20)]

        random.seed(5)
        generator = LanguageGenerator(schema)
        produced = []
        for _ in range(20):
            produced.append(generator.generate())
            for name, index in generator.choices.items():
                self.assertEqual(schema["variables"][name][index], produced[-1][name])

        self.assertEqual(produced, expected)


if __name__ == "__main__":
    unittest.main()
