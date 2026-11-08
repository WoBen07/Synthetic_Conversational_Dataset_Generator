"""Dataset Forge: template-based synthetic conversational datasets.

    from dataset_forge import Forge
    forge = Forge("hospital", seed=42)
    datapoints = list(forge.generate("tool_use/patient_reminder", n=5))

See dataset_forge/api.py and documentation/.
"""

__version__ = "0.3.0"

__all__ = ["Forge", "list_domains", "load_domain", "__version__"]


def __getattr__(name):
    # Imported on first use: the engine resolves the project folder when it
    # is imported, and the command line sets that folder first.

    if name == "Forge":
        from dataset_forge.api import Forge
        return Forge

    if name in ("list_domains", "load_domain"):
        from dataset_forge.engine import domain
        return getattr(domain, name)

    raise AttributeError(f"module 'dataset_forge' has no attribute {name!r}")
