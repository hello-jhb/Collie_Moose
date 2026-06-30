"""Moose Intake Layer.

Day 2 intake identifies files, resolves business context from knowledge files, and returns
routing metadata. Exports are lazy to avoid eager import failures during Streamlit startup.
"""

from importlib import import_module

__all__ = [
    "ContextResolver",
    "DocumentIdentity",
    "FileIdentifier",
    "IntakeResult",
    "Router",
]

_EXPORTS = {
    "ContextResolver": ".context_resolver",
    "DocumentIdentity": ".intake_result",
    "FileIdentifier": ".file_identifier",
    "IntakeResult": ".intake_result",
    "Router": ".router",
}


def __getattr__(name: str):
    if name not in _EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module = import_module(_EXPORTS[name], __name__)
    value = getattr(module, name)
    globals()[name] = value
    return value
