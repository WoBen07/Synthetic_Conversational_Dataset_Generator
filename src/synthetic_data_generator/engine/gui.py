#!/usr/bin/env python3
"""Local web GUI: browse domains, render conversations, inspect tool
schemas and run the generator.

    python -m synthetic_data_generator.engine.gui [--port 8765] [--no-browser]

Standard library only. It listens on localhost and rejects requests from
other sites, since it can start a generation run. Generation is the
orchestrator in a subprocess; it never publishes, and replacing a merged
dataset needs an explicit confirmation. See documentation/gui.md.
"""

import argparse
import json
import os
import subprocess
import sys
import threading
import webbrowser
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import yaml

from synthetic_data_generator.engine import dataset_merger, orchestrator, publish_to_hub, tool_registry
from synthetic_data_generator.engine.datapoint_metadata import behaviour, tool_calls
from synthetic_data_generator.engine.dataset_generator import DatasetGenerator
from synthetic_data_generator.engine.domain import list_domains, load_domain
from synthetic_data_generator.engine.paths import PACKAGE_DIR, PROJECT_ENV_VAR, PROJECT_ROOT, display
from synthetic_data_generator.engine.tool_definitions import function_definition


PAGE = Path(__file__).with_name("gui_page.html")

DEFAULT_PORT = 8765

# Same as generate_many: draws a template may need before one passes
PREVIEW_ATTEMPTS = 50

LOG_LINES = 400

# Rendering uses the global random generator and module-level generator
# state, requests come in on several threads.
RENDER_LOCK = threading.Lock()


class RequestError(Exception):

    def __init__(self, status, message):

        super().__init__(message)
        self.status = status


# ==========================
# Reading domains
# ==========================

def get_domain(name):
    """Only names from list_domains: a name becomes part of a path."""

    if name not in list_domains():
        raise RequestError(404, f"Unknown domain {name!r}")

    return load_domain(name)


def get_template(domain, template_id):
    """Only ids from templates(): an id becomes part of a path."""

    if template_id not in domain.templates():
        raise RequestError(404, f"Unknown template {template_id!r} in {domain.name}")

    return template_id


def domain_summaries():
    """All domains, read from disk again so edited files show up. A broken
    pack is reported, and does not take the others down."""

    with RENDER_LOCK:

        load_domain.cache_clear()
        tool_registry._load.cache_clear()

        summaries = []

        for name in list_domains():

            try:
                domain = load_domain(name)

                summaries.append({
                    "name": name,
                    "base": domain.base_name,
                    "variant": domain.variant,
                    "language": domain.language,
                    "description": domain.description,
                    "templates": len(domain.templates()),
                    "tools": len(domain.tools),
                    "gaps": len(domain.translation_gaps()),
                })

            except Exception as error:
                summaries.append({"name": name, "error": str(error)})

    return summaries


def domain_detail(name):

    domain = get_domain(name)

    amounts = orchestrator.plan_amounts(domain, verbose=False)

    return {
        "name": domain.name,
        "language": domain.language,
        "description": domain.description,
        "templates": [
            {"id": template_id, "amount": amounts[template_id]}
            for template_id in domain.templates()
        ],
        "tools": [
            {
                **function_definition(schema)["function"],
                "side_effects": tool_registry.has_side_effects(tool, domain.tools),
                "definition": function_definition(schema),
            }
            for tool, schema in sorted(domain.tools.items())
        ],
        "gaps": domain.translation_gaps(),
    }


def preview(name, template_id):
    """Render one conversation the way generate_many does: draws the
    validators reject are redrawn. If none passes, the last one is returned
    with its errors, because that is what there is to fix."""

    domain = get_domain(name)

    get_template(domain, template_id)

    with RENDER_LOCK:

        generator = DatasetGenerator(None, domain=domain)

        datapoint = trace = None
        errors = []
        rejected = 0

        for _ in range(PREVIEW_ATTEMPTS):

            try:
                drawn, drawn_trace = generator.generate_one_traced(*domain.paths(template_id))

            except ValueError as error:
                # A constraint violation; the generator redraws as well.
                rejected += 1
                errors = [str(error)]
                continue

            datapoint, trace = drawn, drawn_trace

            errors = generator.validator.validate(datapoint)

            if not errors:
                break

            rejected += 1

    if datapoint is None:
        return {"messages": [], "errors": errors, "rejected": rejected, "tools": [], "wording": [], "tags": []}

    tools = [
        call["name"]
        for message in datapoint["messages"]
        for call in tool_calls(message)
    ]

    scenario = yaml.safe_load(domain.scenario_path(template_id).read_text(encoding="utf-8")) or {}

    return {
        "messages": datapoint["messages"],
        "errors": errors,
        "rejected": rejected,
        "tools": tools,
        "behaviour": behaviour(tools, domain.tools),
        "tags": scenario.get("tags") or [],
        "wording": [
            {"name": variable, "choice": choice + 1, "size": trace["pool_sizes"][variable]}
            for variable, choice in sorted(trace["choices"].items())
        ],
    }


# ==========================
# Generating
# ==========================

def merge_target(names):
    """The folder the merger will write for this selection."""

    return Path(orchestrator.merged_dataset_folder(names) or dataset_merger.OUTPUT_FOLDER)


def approved_for_publishing(target):

    try:
        approved = publish_to_hub.load_publish_config().get("approved_datasets") or []

    except OSError:
        return False

    return target.parent == publish_to_hub.DATASETS_DIR and target.name in approved


def relative(path):

    return display(path)


def generation_plan(names):

    if not names:
        raise RequestError(400, "Select at least one domain")

    amounts = {name: orchestrator.plan_amounts(get_domain(name), verbose=False) for name in names}

    target = merge_target(names)

    return {
        "domains": names,
        "planned": sum(sum(plan.values()) for plan in amounts.values()),
        "templates": sum(len(plan) for plan in amounts.values()),
        "target": relative(target),
        "exists": (target / dataset_merger.TRAIN_OUTPUT).exists(),
        "approved": approved_for_publishing(target),
    }


def generation_command(names):
    """Never with --publish: publishing stays a decision made on purpose."""

    command = [sys.executable, "-u", "-m", "synthetic_data_generator.engine.orchestrator"]

    for name in names:
        command += ["--domain", name]

    return command


def subprocess_environment():
    """The child process works on the same project and can import the
    package even when it is not installed."""

    environment = dict(os.environ)
    environment[PROJECT_ENV_VAR] = str(PROJECT_ROOT)

    paths = [str(PACKAGE_DIR.parent), environment.get("PYTHONPATH")]
    environment["PYTHONPATH"] = os.pathsep.join(p for p in paths if p)

    return environment


class GenerationJob:
    """The one generation run the GUI can have at a time."""

    def __init__(self):

        self.lock = threading.Lock()
        self.process = None
        self.state = {"status": "idle", "log": deque(maxlen=LOG_LINES)}


    def snapshot(self):

        with self.lock:
            return {**self.state, "log": list(self.state["log"])}


    def start(self, plan):

        with self.lock:

            if self.state["status"] == "running":
                raise RequestError(409, "A generation run is already in progress")

            self.state = {
                **plan,
                "status": "running",
                "done": 0,
                "skipped": 0,
                "gave_up": 0,
                "exit_code": None,
                "log": deque(maxlen=LOG_LINES),
            }

            self.process = subprocess.Popen(
                generation_command(plan["domains"]),
                cwd=PROJECT_ROOT,
                env=subprocess_environment(),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
            )

        threading.Thread(target=self._follow, args=(self.process,), daemon=True).start()


    def _follow(self, process):

        with process.stdout:

            for line in process.stdout:
                self._record(line.rstrip())

        exit_code = process.wait()

        with self.lock:

            self.state["exit_code"] = exit_code

            if self.state["status"] == "running":
                self.state["status"] = "finished" if exit_code == 0 else "failed"


    def _record(self, line):

        with self.lock:

            if line.startswith("Generated "):
                self.state["done"] += 1

            elif "Skipping datapoint after" in line:
                self.state["skipped"] += 1

            elif "Regenerating datapoint" in line or (line.startswith("[") and line.endswith("]")):
                # Validators filtering, the normal case
                pass

            else:
                if "Giving up after" in line:
                    self.state["gave_up"] += 1

                self.state["log"].append(line)


    def stop(self):

        with self.lock:

            if self.state["status"] != "running":
                raise RequestError(409, "No generation run in progress")

            self.state["status"] = "stopped"
            self.process.terminate()


# ==========================
# HTTP
# ==========================

class Handler(BaseHTTPRequestHandler):

    job = None

    def log_message(self, *_):
        pass


    def _send(self, status, body, content_type):

        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; style-src 'unsafe-inline'; script-src 'unsafe-inline'"
        )
        self.end_headers()
        self.wfile.write(body)


    def _send_json(self, status, data):

        self._send(status, json.dumps(data, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")


    def _check_origin(self):
        """Another site in the browser must not reach this server: a wrong
        Host means DNS rebinding, a wrong Origin a cross-site request."""

        port = self.server.server_address[1]

        allowed = {f"127.0.0.1:{port}", f"localhost:{port}"}

        if self.headers.get("Host") not in allowed:
            raise RequestError(403, "Wrong Host header")

        origin = self.headers.get("Origin")

        if origin is not None and origin.removeprefix("http://") not in allowed:
            raise RequestError(403, "Wrong Origin header")


    def _handle(self, route):

        try:
            self._check_origin()
            route()

        except RequestError as error:
            self._send_json(error.status, {"error": str(error)})

        except Exception as error:
            # A broken template, schema or config: show it in the GUI.
            self._send_json(500, {"error": f"{type(error).__name__}: {error}"})


    def do_GET(self):
        self._handle(self._get)


    def do_POST(self):
        self._handle(self._post)


    def _get(self):

        url = urlparse(self.path)

        query = parse_qs(url.query)

        def first(key):

            if key not in query:
                raise RequestError(400, f"Missing parameter {key!r}")

            return query[key][0]

        if url.path == "/":
            self._send(200, PAGE.read_bytes(), "text/html; charset=utf-8")

        elif url.path == "/api/domains":
            self._send_json(200, domain_summaries())

        elif url.path == "/api/domain":
            self._send_json(200, domain_detail(first("name")))

        elif url.path == "/api/preview":
            self._send_json(200, preview(first("domain"), first("template")))

        elif url.path == "/api/plan":
            self._send_json(200, generation_plan(query.get("domain", [])))

        elif url.path == "/api/job":
            self._send_json(200, self.job.snapshot())

        else:
            raise RequestError(404, "Not found")


    def _post(self):

        # A plain form on another site cannot send this content type
        # without a preflight, which this server does not answer.
        if self.headers.get("Content-Type", "").split(";")[0] != "application/json":
            raise RequestError(415, "Expected application/json")

        length = int(self.headers.get("Content-Length") or 0)

        body = json.loads(self.rfile.read(length) or b"{}")

        path = urlparse(self.path).path

        if path == "/api/generate":

            plan = generation_plan(list(body.get("domains") or []))

            if plan["exists"] and not body.get("replace_existing"):
                raise RequestError(409, f"{plan['target']} exists; confirm replacing it first")

            self.job.start(plan)

            self._send_json(202, self.job.snapshot())

        elif path == "/api/stop":

            self.job.stop()

            self._send_json(200, self.job.snapshot())

        else:
            raise RequestError(404, "Not found")


def create_server(port=DEFAULT_PORT):
    """Localhost only. Port 0 picks a free one (tests)."""

    handler = type("BoundHandler", (Handler,), {"job": GenerationJob()})

    return ThreadingHTTPServer(("127.0.0.1", port), handler)


def main(argv=None):

    parser = argparse.ArgumentParser(description="Local web GUI of the generator.")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--no-browser", action="store_true", help="do not open a browser")

    args = parser.parse_args(argv)

    try:
        server = create_server(args.port)

    except OSError as error:
        print(f"Cannot listen on port {args.port}: {error}. Try another one with --port.")
        return 1

    url = f"http://127.0.0.1:{server.server_address[1]}/"

    print(f"Generator GUI on {url} (Ctrl+C to quit)")

    if not args.no_browser:
        webbrowser.open(url)

    try:
        server.serve_forever()

    except KeyboardInterrupt:
        pass

    finally:

        server.server_close()

        job = server.RequestHandlerClass.job

        if job.snapshot()["status"] == "running":
            job.stop()

    return 0


if __name__ == "__main__":
    sys.exit(main())
