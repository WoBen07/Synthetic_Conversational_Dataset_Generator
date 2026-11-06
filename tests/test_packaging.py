"""Packaging features: project config, seeds, the Python API, project
init, installable domain packs and the command line."""

import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import yaml

import helpers  # noqa: F401  (sets up the import path)

from dataset_forge import Forge, __version__
from dataset_forge import cli
from dataset_forge.engine import dataset_merger, orchestrator
from dataset_forge.engine import domain as domain_module
from dataset_forge.engine.domain import Domain, load_global_config
from dataset_forge.engine.new_domain import create_package
from dataset_forge.engine.project import init_project

TEMPLATE = "tool_use/patient_reminder"


def write_yaml(path, data):

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data), encoding="utf-8")


class ProjectConfigTest(unittest.TestCase):

    def setUp(self):

        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.folder = Path(directory.name)

        self.default = self.folder / "default.yaml"
        self.project = self.folder / "project.yaml"

        write_yaml(self.default, {
            "domains": [],
            "merged_dataset": "dataset",
            "uniqueness_optimizer": {"samples": 200, "seed": 1},
        })

        for name, path in (("DEFAULT_GLOBAL_CONFIG_FILE", self.default), ("PROJECT_GLOBAL_CONFIG_FILE", self.project)):
            patcher = mock.patch.object(domain_module, name, path)
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_defaults_without_project_file(self):

        self.assertEqual(load_global_config()["merged_dataset"], "dataset")

    def test_project_overrides_key_by_key(self):

        write_yaml(self.project, {"merged_dataset": "mine", "uniqueness_optimizer": {"samples": 5}})

        config = load_global_config()

        self.assertEqual(config["merged_dataset"], "mine")
        self.assertEqual(config["uniqueness_optimizer"], {"samples": 5, "seed": 1})
        self.assertEqual(config["domains"], [])

    def test_merged_dataset_names_the_output_folder(self):

        write_yaml(self.project, {"merged_dataset": "release_1"})

        self.assertEqual(dataset_merger.default_output_folder().name, "release_1")

    def test_merged_dataset_falls_back_to_dataset(self):

        write_yaml(self.default, {})

        self.assertEqual(dataset_merger.default_output_folder().name, dataset_merger.DEFAULT_MERGED_DATASET)


class SeedTest(unittest.TestCase):

    config = {"random_seed_range": {"min": 1, "max": 999999}}

    def test_template_seed_is_stable_and_in_range(self):

        seed = orchestrator.template_seed(7, "hospital", TEMPLATE, self.config)

        self.assertEqual(seed, orchestrator.template_seed(7, "hospital", TEMPLATE, self.config))
        self.assertTrue(1 <= seed <= 999999)

    def test_template_seeds_differ(self):

        seeds = {
            orchestrator.template_seed(7, "hospital", TEMPLATE, self.config),
            orchestrator.template_seed(8, "hospital", TEMPLATE, self.config),
            orchestrator.template_seed(7, "hospital", "tool_use/appointment_note", self.config),
            orchestrator.template_seed(7, "home_assistant", TEMPLATE, self.config),
        }

        self.assertEqual(len(seeds), 4)

    def test_run_seed_precedence(self):

        config = {**self.config, "seed": 5}

        self.assertEqual(orchestrator.run_seed(SimpleNamespace(seed=3), config), 3)
        self.assertEqual(orchestrator.run_seed(SimpleNamespace(seed=None), config), 5)
        self.assertTrue(1 <= orchestrator.run_seed(SimpleNamespace(seed=None), self.config) <= 999999)


class ForgeTest(unittest.TestCase):

    def test_same_seed_same_datapoints(self):

        first = list(Forge("hospital", seed=11).generate(TEMPLATE, n=3))
        second = list(Forge("hospital", seed=11).generate(TEMPLATE, n=3))

        self.assertEqual(len(first), 3)
        self.assertEqual(first, second)

    def test_other_seed_other_datapoints(self):

        first = list(Forge("hospital", seed=11).generate(TEMPLATE, n=3))
        other = list(Forge("hospital", seed=12).generate(TEMPLATE, n=3))

        self.assertNotEqual(first, other)

    def test_datapoints_carry_metadata(self):

        datapoint = next(Forge("hospital", seed=1).generate(TEMPLATE))

        metadata = datapoint["metadata"]

        self.assertEqual(metadata["template"], TEMPLATE)
        self.assertEqual(metadata["generator_version"], __version__)
        self.assertRegex(metadata["template_hash"], r"^[0-9a-f]{12}$")

    def test_generate_all_with_amounts(self):

        forge = Forge("hospital", seed=2)
        templates = forge.templates[:2]

        datapoints = list(forge.generate_all(n={templates[0]: 2, templates[1]: 1}, templates=templates))

        self.assertEqual([d["metadata"]["template"] for d in datapoints], [templates[0]] * 2 + [templates[1]])

    def test_unknown_template(self):

        with self.assertRaises(KeyError):
            next(Forge("hospital", seed=1).generate("no/such_template"))

    def test_tools(self):

        names = {tool["function"]["name"] for tool in Forge("hospital", seed=1).tools}

        self.assertIn("find_patient", names)


class InitProjectTest(unittest.TestCase):

    def test_creates_project_with_domain(self):

        with tempfile.TemporaryDirectory() as directory:

            project = Path(directory) / "proj"

            init_project(project, domain="shop")

            config = yaml.safe_load((project / "config" / "generation_config.yaml").read_text())

            self.assertEqual(config["domains"], ["shop"])
            self.assertTrue((project / "domains" / "shop" / "domain.yaml").exists())
            self.assertIn("config/publish_config.yaml", (project / ".gitignore").read_text())

            with self.assertRaises(FileExistsError):
                init_project(project)

    def test_keeps_existing_files(self):

        with tempfile.TemporaryDirectory() as directory:

            readme = Path(directory) / "README.md"
            readme.write_text("mine")

            init_project(directory)

            self.assertEqual(readme.read_text(), "mine")


class InstallablePackTest(unittest.TestCase):
    """A pack created with ``new-domain --package``, made importable as if it
    were installed, and registered through a mocked entry point."""

    def test_package_pack_is_found_and_generates(self):

        with tempfile.TemporaryDirectory() as directory:

            project = create_package("shop", "Shop assistant robot.", directory)

            pyproject = (project / "pyproject.toml").read_text()
            self.assertIn('[project.entry-points."dataset_forge.domains"]', pyproject)
            self.assertIn('shop = "dforge_shop"', pyproject)

            sys.path.insert(0, str(project / "src"))
            self.addCleanup(sys.path.remove, str(project / "src"))
            self.addCleanup(sys.modules.pop, "dforge_shop", None)

            root = project / "src" / "dforge_shop"

            domain_module.load_domain.cache_clear()
            self.addCleanup(domain_module.load_domain.cache_clear)

            with mock.patch.object(domain_module, "plugin_packs", return_value={"shop": (root, "dforge_shop")}):

                self.assertIn("shop", domain_module.list_domains())
                self.assertEqual(domain_module.find_pack("shop"), root)

                shop = domain_module.load_domain("shop")

                self.assertEqual(shop.module.__name__, "dforge_shop")

                datapoints = list(Forge(shop, seed=3).generate(shop.templates()[0], n=2))

                self.assertEqual(len(datapoints), 2)

    def test_project_pack_shadows_installed_pack(self):

        with tempfile.TemporaryDirectory() as directory:

            folder = Path(directory)
            write_yaml(folder / "project" / "shop" / "domain.yaml", {"name": "shop"})
            write_yaml(folder / "installed" / "shop" / "domain.yaml", {"name": "shop"})

            with mock.patch.object(domain_module, "DOMAIN_DIRS", [folder / "project", folder / "builtin"]), \
                    mock.patch.object(domain_module, "plugin_packs", return_value={"shop": (folder / "installed" / "shop", "x")}):

                self.assertEqual(domain_module.find_pack("shop"), folder / "project" / "shop")


class CliTest(unittest.TestCase):

    def run_cli(self, *argv):

        output = io.StringIO()

        with contextlib.redirect_stdout(output):
            code = cli.main(list(argv))

        return code, output.getvalue()

    def test_version(self):

        output = io.StringIO()

        with contextlib.redirect_stdout(output), self.assertRaises(SystemExit):
            cli.main(["--version"])

        self.assertIn(__version__, output.getvalue())

    def test_domains_lists_built_in_packs(self):

        code, output = self.run_cli("domains")

        self.assertEqual(code, 0)
        self.assertRegex(output, r"hospital\s+built-in")

    def test_init(self):

        with tempfile.TemporaryDirectory() as directory:

            code, output = self.run_cli("init", str(Path(directory) / "p"))

            self.assertEqual(code, 0)
            self.assertTrue((Path(directory) / "p" / "config" / "generation_config.yaml").exists())


if __name__ == "__main__":
    unittest.main()
