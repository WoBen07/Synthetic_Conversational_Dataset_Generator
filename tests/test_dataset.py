import json
import random
import tempfile
import unittest
from collections import Counter
from pathlib import Path

import helpers

from synthetic_data_generator.engine import config_optimizer as optimizer
from synthetic_data_generator.engine import dataset_merger as merger
from synthetic_data_generator.engine.datapoint_metadata import behaviour, build_metadata, wording_id


class OptimizerMathTest(unittest.TestCase):

    def test_duplicate_share(self):

        self.assertEqual(optimizer.duplicate_share(1, 100), 0.0)
        self.assertAlmostEqual(optimizer.duplicate_share(10, 1), 0.9)
        # small samples from a large space barely repeat
        self.assertLess(optimizer.duplicate_share(100, 1_000_000), 0.001)

    def test_cap_respects_rate(self):

        cap = optimizer.max_amount_for_duplicate_rate(2744, 0.05)

        self.assertLessEqual(optimizer.duplicate_share(cap, 2744), 0.05)
        self.assertGreater(optimizer.duplicate_share(cap + 1, 2744), 0.05)

    def test_chao1(self):

        self.assertEqual(optimizer.chao1(Counter({"a": 1, "b": 2})), 2 + 1 / 2)

    def test_analyse_picks_smaller_limit(self):

        settings = {"max_duplicate_rate": 0.05, "max_phrase_repeats": 10, "min_amount": 5}

        sample = {
            "skeletons": Counter({(("a", i),): 1 for i in range(50)}),
            "used_pools": {"a": 1000, "b": 3, "constant": 1},
            "valid": 50,
            "acceptance": 1.0,
        }

        result = optimizer.analyse(sample, settings)

        # pool b (3 phrases x 10 repeats) is tighter than the near-duplicate limit
        self.assertEqual(result["cap"], 30)
        self.assertEqual(result["smallest_pool"], "b")


class MetadataTest(unittest.TestCase):

    def test_behaviour_follows_side_effects(self):

        tools = helpers.HOSPITAL.tools

        self.assertEqual(behaviour(["find_patient", "remind_patient"], tools), "action")
        self.assertEqual(behaviour(["find_patient", "get_patient_appointment"], tools), "lookup_only")
        self.assertEqual(behaviour([], tools), "no_tool")
        self.assertEqual(behaviour(["unknown_tool"], tools), "action")

    def test_wording_id_ignores_choice_order(self):

        self.assertEqual(wording_id("t", {"a": 1, "b": 2}), wording_id("t", {"b": 2, "a": 1}))
        self.assertNotEqual(wording_id("t", {"a": 1}), wording_id("u", {"a": 1}))
        self.assertNotEqual(wording_id("t", {"a": 1}, "x"), wording_id("t", {"a": 1}, "y"))

    def test_build_metadata(self):

        datapoint = helpers.conversation(
            ("user", "Hi"),
            ("assistant", {"tool_call": {"name": "find_patient", "arguments": {}}}),
        )

        metadata = build_metadata(datapoint, helpers.HOSPITAL, "tool_use/x", {"a": 0}, ["tag"])

        self.assertEqual(metadata["domain"], "hospital")
        self.assertEqual(metadata["category"], "tool_use")
        self.assertEqual(metadata["tools"], ["find_patient"])
        self.assertEqual(metadata["behaviour"], "lookup_only")
        self.assertEqual(metadata["tags"], ["tag"])


class SplitTest(unittest.TestCase):

    def datapoints(self, wordings, copies):
        return [
            {"messages": [], "metadata": {"wording_id": f"w{w}"}}
            for w in range(wordings)
            for _ in range(copies)
        ]

    def test_no_wording_in_both_splits(self):

        samples = self.datapoints(wordings=40, copies=5)

        train, validation = merger.split_template(samples, random.Random(1))

        self.assertEqual(len(train) + len(validation), len(samples))
        self.assertEqual(merger.wording_overlap(train, validation), 0)
        self.assertGreaterEqual(len(validation), int(len(samples) * merger.VALIDATION_SPLIT))

    def test_single_wording_stays_in_train(self):

        train, validation = merger.split_template(self.datapoints(1, 20), random.Random(1))

        self.assertEqual((len(train), len(validation)), (20, 0))

    def test_old_datapoints_without_metadata(self):

        samples = [{"messages": []} for _ in range(30)]

        train, validation = merger.split_template(samples, random.Random(1))

        self.assertEqual((len(train), len(validation)), (27, 3))


class GenerateManyTest(unittest.TestCase):

    def test_files_metadata_and_no_duplicates(self):

        template = "safety_and_refusals/consent_seeking"
        scenario, _, language = helpers.paths(template)

        with tempfile.TemporaryDirectory() as directory:

            helpers.DatasetGenerator(11).generate_many(scenario, template, 20, directory, language)

            files = sorted(Path(directory).glob("example_*.json"))
            datapoints = [json.loads(f.read_text(encoding="utf-8")) for f in files]
            summary = json.loads((Path(directory) / "metadata.json").read_text(encoding="utf-8"))

        self.assertEqual(len(datapoints), 20)
        self.assertEqual(summary["generated"], 20)
        self.assertEqual(summary["domain"], "hospital")

        for datapoint in datapoints:
            self.assertEqual(datapoint["metadata"]["template"], template)
            self.assertEqual(datapoint["metadata"]["domain"], "hospital")
            self.assertEqual(datapoint["metadata"]["behaviour"], "action")
            self.assertEqual(datapoint["metadata"]["tags"], ["offer_accepted"])

        texts = [json.dumps(d["messages"], sort_keys=True) for d in datapoints]
        self.assertEqual(len(set(texts)), len(texts))


if __name__ == "__main__":
    unittest.main()
