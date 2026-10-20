import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

import helpers

from synthetic_data_generator.engine import dataset_merger as merger
from synthetic_data_generator.engine.dataset_generator import DatasetGenerator
from synthetic_data_generator.engine.domain import Domain, list_domains, load_domain
from synthetic_data_generator.engine.new_domain import create_domain


def load_script(relative):
    """Import a preprocessor script (they are not part of a package)."""

    path = helpers.PACKAGE_ROOT / relative
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class DomainLoadingTest(unittest.TestCase):

    def test_hospital_is_a_domain(self):

        self.assertIn("hospital", list_domains())

        hospital = load_domain("hospital")

        self.assertTrue(hospital.templates())
        self.assertIn("alert_staff", hospital.tools)
        self.assertIn("appointment_type", hospital.generators)   # domain generator
        self.assertIn("first_name", hospital.generators)         # shared generator
        self.assertTrue(hospital.create_validators())

    def test_unknown_domain(self):

        with self.assertRaises(FileNotFoundError):
            Domain("no_such_domain")


class NewDomainTest(unittest.TestCase):
    """A scaffolded pack works without any hospital code."""

    def test_scaffold_generates_valid_data(self):

        with tempfile.TemporaryDirectory() as directory:

            root = create_domain("shop", "Shop assistant robot.", Path(directory))
            shop = Domain("shop", root)

            self.assertEqual(shop.templates(), ["orders/order_status"])
            self.assertEqual(shop.create_validators(), [])
            self.assertNotIn("appointment_type", shop.generators)

            generator = DatasetGenerator(5, domain=shop)

            for _ in range(10):
                datapoint = generator.generate_one(*shop.paths("orders/order_status"))
                self.assertEqual(generator.validator.validate(datapoint), [])

            self.assertIn("You are speaking with a customer.", datapoint["messages"][0]["content"])

    def test_invalid_or_existing_name(self):

        with tempfile.TemporaryDirectory() as directory:

            with self.assertRaises(ValueError):
                create_domain("Bad Name", "", Path(directory))

            create_domain("shop", "", Path(directory))

            with self.assertRaises(FileExistsError):
                create_domain("shop", "", Path(directory))


class MergerLayoutTest(unittest.TestCase):

    def write(self, folder, metadata, datapoints):

        folder.mkdir(parents=True)
        (folder / "metadata.json").write_text(json.dumps(metadata))

        for index, datapoint in enumerate(datapoints):
            (folder / f"example_{index:05d}.json").write_text(json.dumps(datapoint))

    def test_loads_domain_folders_and_skips_old_layout(self):

        with tempfile.TemporaryDirectory() as directory:

            root = Path(directory)
            datapoint = {"messages": [{"role": "user", "content": "hi"}]}

            self.write(root / "hospital" / "consent_seeking",
                       {"domain": "hospital", "template": "safety_and_refusals/consent_seeking", "amount": 2},
                       [datapoint, datapoint])
            self.write(root / "shop" / "order_status",
                       {"domain": "shop", "template": "orders/order_status", "amount": 1},
                       [datapoint])
            # flat folder from before domain packs
            self.write(root / "consent_seeking",
                       {"template": "safety_and_refusals/consent_seeking"},
                       [datapoint])

            everything = merger.load_dataset_by_template(root)
            only_shop = merger.load_dataset_by_template(root, ["shop"])

        self.assertEqual(
            {key: len(value) for key, value in everything.items()},
            {"hospital/safety_and_refusals/consent_seeking": 2, "shop/orders/order_status": 1}
        )
        self.assertEqual(list(only_shop), ["shop/orders/order_status"])
        self.assertEqual(merger.domains_of(everything), ["hospital", "shop"])


class PreprocessorToolsTest(unittest.TestCase):

    def test_tools_follow_the_example_domain(self):

        qwen = load_script("Model_Specific_Preprocessors/qwen_preprossor.py")
        gemma = load_script("Model_Specific_Preprocessors/Gemma_preprocessor.py")

        tools = {"hospital": ["h"], "shop": ["s"]}
        example = {"messages": [], "metadata": {"domain": "shop"}}

        for module in (qwen, gemma):
            with self.subTest(module=module.__name__):
                self.assertEqual(module.tools_for(example, tools), ["s"])
                # single-domain file or old list format
                self.assertEqual(module.tools_for({"messages": []}, {"hospital": ["h"]}), ["h"])
                self.assertEqual(module.tools_for(example, ["x"]), ["x"])
                with self.assertRaises(ValueError):
                    module.tools_for({"messages": []}, tools)


if __name__ == "__main__":
    unittest.main()
