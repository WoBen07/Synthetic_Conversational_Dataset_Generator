"""Command line entry point: ``dforge <command> [options]``.

Each command forwards its options to the module that implements it, so
``dforge generate --help`` shows the orchestrator's own options.
"""

import argparse
import importlib
import os
import sys

from dataset_forge import __version__

# command -> (module with a main(), one-line help)
COMMANDS = {
    "init": (
        "dataset_forge.engine.project",
        "set up a project folder (config, domains/, .gitignore)",
    ),
    "generate": (
        "dataset_forge.engine.orchestrator",
        "lint, generate and merge the selected domains",
    ),
    "lint": (
        "dataset_forge.engine.lint_templates",
        "check the templates of every domain",
    ),
    "optimize": (
        "dataset_forge.engine.config_optimizer",
        "measure uniqueness and cap template amounts",
    ),
    "new-domain": (
        "dataset_forge.engine.new_domain",
        "create a domain pack in the project's domains/ (--package: pip-installable)",
    ),
    "publish": (
        "dataset_forge.engine.publish_to_hub",
        "push an approved dataset to the Hugging Face Hub (needs the [hub] extra)",
    ),
    "gui": (
        "dataset_forge.engine.gui",
        "start the local web GUI",
    ),
}


def list_domains():
    """``dforge domains``: every domain and where it was found."""

    from dataset_forge.engine.domain import find_pack, list_domains, plugin_packs, VARIANT_SEPARATOR
    from dataset_forge.engine.paths import PROJECT_DOMAINS_DIR, PROJECT_ROOT, display

    print(f"Project: {PROJECT_ROOT}")

    for name in list_domains():

        root = find_pack(name.partition(VARIANT_SEPARATOR)[0])

        if root.parent == PROJECT_DOMAINS_DIR:
            source = "project"
        elif any(root == folder for folder, _module in plugin_packs().values()):
            source = "installed"
        else:
            source = "built-in"

        print(f"  {name:<30} {source:<10} {display(root)}")

    return 0


def main(argv=None):

    parser = argparse.ArgumentParser(
        prog="dforge",
        description="Synthetic conversational dataset generator.",
    )
    parser.add_argument(
        "--project", metavar="DIR",
        help="project folder with domains/, config/ and the output "
             "(default: $DFORGE_PROJECT_DIR, else the current directory)",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    commands = parser.add_subparsers(dest="command", required=True, metavar="COMMAND")

    for name, (_module, help_text) in COMMANDS.items():
        commands.add_parser(name, help=help_text, add_help=False)

    commands.add_parser("domains", help="list the available domains")

    args, rest = parser.parse_known_args(argv)

    # Before any engine module is imported: they resolve their paths on import.
    if args.project:
        os.environ["DFORGE_PROJECT_DIR"] = os.path.abspath(args.project)

    from dataset_forge.log import configure_cli_logging

    configure_cli_logging()

    if args.command == "domains":
        return list_domains()

    module = importlib.import_module(COMMANDS[args.command][0])

    # The modules parse sys.argv themselves.
    sys.argv = [f"dforge {args.command}", *rest]

    return module.main()


if __name__ == "__main__":
    sys.exit(main())
