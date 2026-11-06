"""Command line entry point: ``sdg <command> [options]``.

Each command forwards its options to the module that implements it, so
``sdg generate --help`` shows the orchestrator's own options.
"""

import argparse
import importlib
import os
import sys

from synthetic_data_generator import __version__

# command -> (module with a main(), one-line help)
COMMANDS = {
    "generate": (
        "synthetic_data_generator.engine.orchestrator",
        "lint, generate and merge the selected domains",
    ),
    "lint": (
        "synthetic_data_generator.engine.lint_templates",
        "check the templates of every domain",
    ),
    "optimize": (
        "synthetic_data_generator.engine.config_optimizer",
        "measure uniqueness and cap template amounts",
    ),
    "new-domain": (
        "synthetic_data_generator.engine.new_domain",
        "create a domain pack in the project's domains/ folder",
    ),
    "publish": (
        "synthetic_data_generator.engine.publish_to_hub",
        "push an approved dataset to the Hugging Face Hub (needs the [hub] extra)",
    ),
    "gui": (
        "synthetic_data_generator.engine.gui",
        "start the local web GUI",
    ),
}


def list_domains():
    """``sdg domains``: every domain and where it was found."""

    from synthetic_data_generator.engine.domain import find_pack, list_domains, VARIANT_SEPARATOR
    from synthetic_data_generator.engine.paths import PROJECT_ROOT, display

    print(f"Project: {PROJECT_ROOT}")

    for name in list_domains():
        print(f"  {name:<30} {display(find_pack(name.partition(VARIANT_SEPARATOR)[0]))}")

    return 0


def main(argv=None):

    parser = argparse.ArgumentParser(
        prog="sdg",
        description="Synthetic conversational dataset generator.",
    )
    parser.add_argument(
        "--project", metavar="DIR",
        help="project folder with domains/, config/ and the output "
             "(default: $SDG_PROJECT_DIR, else the current directory)",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    commands = parser.add_subparsers(dest="command", required=True, metavar="COMMAND")

    for name, (_module, help_text) in COMMANDS.items():
        commands.add_parser(name, help=help_text, add_help=False)

    commands.add_parser("domains", help="list the available domains")

    args, rest = parser.parse_known_args(argv)

    # Before any engine module is imported: they resolve their paths on import.
    if args.project:
        os.environ["SDG_PROJECT_DIR"] = os.path.abspath(args.project)

    if args.command == "domains":
        return list_domains()

    module = importlib.import_module(COMMANDS[args.command][0])

    # The modules parse sys.argv themselves.
    sys.argv = [f"sdg {args.command}", *rest]

    return module.main()


if __name__ == "__main__":
    sys.exit(main())
