"""Moose code-based trust engine."""

from importlib import import_module

__all__ = [
    "AuthorityResolver",
    "ReconciliationEngine",
    "TrustVerifier",
    "VerifiedFact",
    "VerificationRunResult",
]

_EXPORTS = {
    "AuthorityResolver": ".authority",
    "ReconciliationEngine": ".reconciliation",
    "TrustVerifier": ".verifier",
    "VerifiedFact": ".verification_result",
    "VerificationRunResult": ".verification_result",
}


def __getattr__(name: str):
    if name not in _EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module = import_module(_EXPORTS[name], __name__)
    value = getattr(module, name)
    globals()[name] = value
    return value
