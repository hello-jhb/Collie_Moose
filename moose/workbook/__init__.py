"""Moose workbook comprehension.

Day 3 workbook comprehension inspects workbook structure, orients the workbook, and
produces a model brief. Exports are lazy so apps can import only the pieces they use.
"""

from importlib import import_module

__all__ = [
    "ModelBriefBuilder",
    "ModelBriefResult",
    "ClaimGroundingResult",
    "FallbackWorkbookClaimExtractor",
    "WorkbookClaimExtractionResult",
    "WorkbookClaimDiscoveryAgent",
    "WorkbookClaimDiscoveryUnavailable",
    "WorkbookClaimExtractor",
    "WorkbookComprehensionResult",
    "WorkbookEvidencePackBuilder",
    "WorkbookEvidencePackResult",
    "WorkbookClaimGroundingValidator",
    "WorkbookInspectionResult",
    "WorkbookInspector",
    "WorkbookMentalModelBuilder",
    "WorkbookMentalModelResult",
    "WorkbookOrientationBuilder",
    "WorkbookOrientationResult",
]

_EXPORTS = {
    "ModelBriefBuilder": ".model_brief",
    "FallbackWorkbookClaimExtractor": ".claim_extractor",
    "WorkbookClaimExtractor": ".claim_extractor",
    "WorkbookClaimDiscoveryAgent": ".discovery_agent",
    "WorkbookClaimDiscoveryUnavailable": ".discovery_agent",
    "WorkbookEvidencePackBuilder": ".evidence_pack",
    "WorkbookClaimGroundingValidator": ".grounding",
    "WorkbookMentalModelBuilder": ".mental_model",
    "WorkbookInspector": ".workbook_inspector",
    "WorkbookOrientationBuilder": ".workbook_orientation",
    "ClaimGroundingResult": ".workbook_result",
    "WorkbookEvidencePackResult": ".workbook_result",
    "WorkbookClaimExtractionResult": ".workbook_result",
    "ModelBriefResult": ".workbook_result",
    "WorkbookComprehensionResult": ".workbook_result",
    "WorkbookInspectionResult": ".workbook_result",
    "WorkbookMentalModelResult": ".workbook_result",
    "WorkbookOrientationResult": ".workbook_result",
}


def __getattr__(name: str):
    if name not in _EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module = import_module(_EXPORTS[name], __name__)
    value = getattr(module, name)
    globals()[name] = value
    return value
