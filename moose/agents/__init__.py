"""Moose agent stubs.

These classes define the first architecture contracts. Imports are resolved lazily
so app startup does not eagerly import every agent module.
"""

from importlib import import_module

__all__ = [
    "ClaimExtractor",
    "FileIdentifier",
    "ModelBriefAgent",
    "ReasoningAgent",
    "WorkbookOrientationAgent",
]

_EXPORTS = {
    "ClaimExtractor": ".claim_extractor",
    "FileIdentifier": ".file_identifier",
    "ModelBriefAgent": ".model_brief",
    "ReasoningAgent": ".reasoning",
    "WorkbookOrientationAgent": ".workbook_orientation",
}


def __getattr__(name: str):
    if name not in _EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module = import_module(_EXPORTS[name], __name__)
    value = getattr(module, name)
    globals()[name] = value
    return value
