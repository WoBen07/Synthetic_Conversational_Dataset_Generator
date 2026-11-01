"""The GUI's server. Nothing here starts the real generator: the command of
a generation run is replaced."""

import json
import sys
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from unittest import mock

import helpers

from synthetic_data_generator.engine import gui


class ServerTestCase(unittest.TestCase):

    def setUp(self):

        self.server = gui.create_server(0)

        thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        thread.start()

        self.addCleanup(thread.join)
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)

        self.port = self.server.server_address[1]

    def request(self, path, body=None, headers=None):
        """(status, parsed JSON or raw page)"""

        data = None if body is None else json.dumps(body).encode("utf-8")

        headers = {
            **({"Content-Type": "application/json"} if body is not None else {}),
            **(headers or {}),
        }

        request = urllib.request.Request(
            f"http://127.0.0.1:{self.port}{path}",
            data=data,
            headers=headers
        )

        try:
            with urllib.request.urlopen(request) as response:
                status, raw, kind = response.status, response.read(), response.headers["Content-Type"]

        except urllib.error.HTTPError as error:
            status, raw, kind = error.code, error.read(), error.headers["Content-Type"]

        return status, json.loads(raw) if "json" in kind else raw


class ReadingTest(ServerTestCase):

    def test_page(self):

        status, page = self.request("/")

        self.assertEqual(status, 200)
        self.assertIn(b"Dataset Generator", page)

    def test_domains(self):

        status, domains = self.request("/api/domains")

        self.assertEqual(status, 200)

        by_name = {domain["name"]: domain for domain in domains}

        self.assertEqual(by_name["hospital"]["language"], "en")
        self.assertEqual(by_name["home_assistant"]["language"], "de")
        self.assertEqual(by_name["home_assistant"]["tools"], 10)

    def test_broken_domain_does_not_hide_the_others(self):

        real = gui.load_domain

        def load(name):
            if name == "hospital":
                raise ValueError("broken pack")
            return real(name)

        load.cache_clear = real.cache_clear

        with mock.patch.object(gui, "load_domain", load):
            _, domains = self.request("/api/domains")

        by_name = {domain["name"]: domain for domain in domains}

        self.assertEqual(by_name["hospital"]["error"], "broken pack")
        self.assertEqual(by_name["home_assistant"]["tools"], 10)

    def test_domain_detail(self):

        status, detail = self.request("/api/domain?name=home_assistant")

        self.assertEqual(status, 200)
        self.assertEqual(len(detail["templates"]), 24)

        tools = {tool["name"]: tool for tool in detail["tools"]}

        self.assertFalse(tools["get_light_capabilities"]["side_effects"])
        self.assertTrue(tools["set_light_power"]["side_effects"])
        self.assertEqual(tools["set_light_power"]["definition"]["type"], "function")

    def test_preview_is_valid_and_explains_itself(self):

        for domain, template in (
            ("home_assistant", "light/light_color_supported"),
            ("hospital", "tool_use/patient_reminder"),
        ):
            with self.subTest(domain=domain):

                status, result = self.request(f"/api/preview?domain={domain}&template={template}")

                self.assertEqual(status, 200)
                self.assertEqual(result["errors"], [])
                self.assertEqual(result["messages"][0]["role"], "system")
                self.assertTrue(result["tools"])
                self.assertEqual(result["behaviour"], "action")

                for wording in result["wording"]:
                    self.assertTrue(1 <= wording["choice"] <= wording["size"])

    def test_preview_shows_why_a_template_fails(self):

        with mock.patch("synthetic_data_generator.engine.validators.validator.Validator.validate", return_value=["nope"]):
            status, result = self.request("/api/preview?domain=home_assistant&template=heating/heating_off")

        self.assertEqual(status, 200)
        self.assertEqual(result["errors"], ["nope"])
        self.assertEqual(result["rejected"], gui.PREVIEW_ATTEMPTS)
        self.assertTrue(result["messages"])

    def test_only_known_names_reach_the_file_system(self):

        cases = [
            "/api/domain?name=../../etc",
            "/api/domain?name=hospital@../../etc",
            "/api/preview?domain=hospital&template=../../../etc/passwd",
            "/api/preview?domain=../hospital&template=tool_use/patient_reminder",
            "/api/plan?domain=../hospital",
            "/etc/passwd",
        ]

        for path in cases:
            with self.subTest(path=path):
                self.assertEqual(self.request(path)[0], 404)

    def test_missing_parameter(self):

        self.assertEqual(self.request("/api/domain")[0], 400)


class OtherSitesTest(ServerTestCase):

    def test_wrong_host_is_rejected(self):

        self.assertEqual(self.request("/api/domains", headers={"Host": "evil.example"})[0], 403)

    def test_localhost_is_accepted(self):

        self.assertEqual(self.request("/api/domains", headers={"Host": f"localhost:{self.port}"})[0], 200)

    def test_wrong_origin_is_rejected(self):

        self.assertEqual(
            self.request("/api/stop", {}, {"Origin": "http://evil.example"})[0],
            403
        )

    def test_post_needs_json(self):

        status, _ = self.request("/api/stop", {}, {"Content-Type": "text/plain"})

        self.assertEqual(status, 415)

    def test_listens_on_localhost_only(self):

        self.assertEqual(self.server.server_address[0], "127.0.0.1")


class PlanTest(unittest.TestCase):

    def test_plan_of_a_selection(self):

        plan = gui.generation_plan(["home_assistant"])

        self.assertEqual(plan["templates"], 24)
        self.assertEqual(plan["planned"], 6150)
        self.assertEqual(plan["target"], str(Path("Datasets") / "home_assistant"))
        self.assertFalse(plan["approved"])

    def test_target_of_the_configured_domains_is_the_merger_default(self):

        self.assertEqual(gui.merge_target(["hospital"]), Path(gui.dataset_merger.OUTPUT_FOLDER))

    def test_empty_selection(self):

        with self.assertRaises(gui.RequestError):
            gui.generation_plan([])

    def test_approved_dataset_is_recognised(self):

        with mock.patch.object(gui.publish_to_hub, "load_publish_config", return_value={"approved_datasets": ["Set"]}):

            self.assertTrue(gui.approved_for_publishing(gui.publish_to_hub.DATASETS_DIR / "Set"))
            self.assertFalse(gui.approved_for_publishing(gui.publish_to_hub.DATASETS_DIR / "Other"))

    def test_missing_publish_config_means_not_approved(self):

        with mock.patch.object(gui.publish_to_hub, "load_publish_config", side_effect=FileNotFoundError):
            self.assertFalse(gui.approved_for_publishing(gui.publish_to_hub.DATASETS_DIR / "Set"))

    def test_command_never_publishes(self):

        command = gui.generation_command(["hospital", "home_assistant@en"])

        self.assertNotIn("--publish", command)
        self.assertEqual(command[-4:], ["--domain", "hospital", "--domain", "home_assistant@en"])


FAKE_RUN = """
print("Generated a", flush=True)
print("[x] ['some error']", flush=True)
print("Regenerating datapoint after validation error.", flush=True)
print("Generated b", flush=True)
print("[x] Skipping datapoint after 50 failed attempts.", flush=True)
print("[x] Giving up after 2 datapoints: pool exhausted.", flush=True)
print("Finished", flush=True)
"""


class GenerateTest(ServerTestCase):

    def wait(self, *statuses):

        for _ in range(200):

            job = self.request("/api/job")[1]

            if job["status"] in statuses:
                return job

            time.sleep(0.02)

        self.fail(f"job did not reach {statuses}: {job}")

    def fake(self, code):
        return mock.patch.object(gui, "generation_command", lambda names: [sys.executable, "-c", code])

    def fresh_target(self):
        """A target that does not exist yet."""

        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)

        return mock.patch.object(gui, "merge_target", lambda names: Path(directory.name) / "new")

    def existing_target(self):

        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)

        (Path(directory.name) / "train.jsonl").write_text("")

        return mock.patch.object(gui, "merge_target", lambda names: Path(directory.name))

    def test_run_reports_progress_and_filters_noise(self):

        with self.fake(FAKE_RUN), self.fresh_target():
            status, _ = self.request("/api/generate", {"domains": ["home_assistant"]})

        self.assertEqual(status, 202)

        job = self.wait("finished")

        self.assertEqual((job["done"], job["skipped"], job["gave_up"], job["exit_code"]), (2, 1, 1, 0))
        self.assertEqual(job["planned"], 6150)
        self.assertEqual(job["log"], ["[x] Giving up after 2 datapoints: pool exhausted.", "Finished"])

    def test_failure_is_reported(self):

        with self.fake("raise SystemExit(3)"), self.fresh_target():
            self.request("/api/generate", {"domains": ["home_assistant"]})

        job = self.wait("failed")

        self.assertEqual(job["exit_code"], 3)

    def test_existing_dataset_needs_confirmation(self):

        with self.fake("print('ran')"), self.existing_target():

            status, result = self.request("/api/generate", {"domains": ["home_assistant"]})

            self.assertEqual(status, 409)
            self.assertIn("exists", result["error"])
            self.assertEqual(self.request("/api/job")[1]["status"], "idle")

            status, _ = self.request("/api/generate", {"domains": ["home_assistant"], "replace_existing": True})

        self.assertEqual(status, 202)
        self.wait("finished")

    def test_one_run_at_a_time_and_stop(self):

        with self.fake("import time; time.sleep(30)"), self.fresh_target():

            self.assertEqual(self.request("/api/generate", {"domains": ["home_assistant"]})[0], 202)
            self.assertEqual(self.request("/api/generate", {"domains": ["home_assistant"]})[0], 409)

            self.assertEqual(self.request("/api/stop", {})[0], 200)

        job = self.wait("stopped")

        self.assertEqual(job["status"], "stopped")
        self.assertEqual(self.request("/api/stop", {})[0], 409)

        self.server.RequestHandlerClass.job.process.wait(5)

    def test_unknown_domain_starts_nothing(self):

        with self.fake("print('ran')"):
            status, _ = self.request("/api/generate", {"domains": ["../hospital"]})

        self.assertEqual(status, 404)
        self.assertEqual(self.request("/api/job")[1]["status"], "idle")


if __name__ == "__main__":
    unittest.main()
