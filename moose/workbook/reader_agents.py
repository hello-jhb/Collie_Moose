"""Agent-led workbook reading roles.

These classes prepare instructions and payload context for GPT. They do not extract
facts with Python rules; Python still only builds evidence and verifies citations.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .workbook_result import WorkbookEvidencePackResult, WorkbookMentalModelResult


GUIDANCE_DIR = Path(__file__).resolve().parents[1] / "guidance"


def load_guidance(name: str) -> str:
    path = GUIDANCE_DIR / name
    return path.read_text(encoding="utf-8")


class WorkbookReaderAgent:
    """Frames the workbook read and business question for downstream agents."""

    guidance_files = ("financial_model_reading.md", "source_authority_guidance.md")

    def instructions(self) -> str:
        return "\n\n".join(load_guidance(name) for name in self.guidance_files)

    def payload(
        self,
        mental_model: WorkbookMentalModelResult,
        evidence_pack: WorkbookEvidencePackResult,
    ) -> dict[str, Any]:
        return {
            "role": "WorkbookReaderAgent",
            "task": (
                "Determine the business question and the workbook context from evidence. "
                "Do not choose facts by hardcoded metric definitions."
            ),
            "mental_model_hint": {
                "document_type": mental_model.document_type,
                "workbook_type": mental_model.workbook_type,
                "business_purpose": mental_model.business_purpose,
                "decision_supported": mental_model.decision_supported,
                "important_sheets": mental_model.important_sheets,
                "expected_sections": mental_model.expected_sections,
                "caveats": mental_model.caveats,
            },
            "available_evidence": {
                "important_sheets": evidence_pack.important_sheet_names,
                "candidate_neighborhood_count": len(evidence_pack.candidate_neighborhoods),
                "caveats": evidence_pack.caveats,
            },
        }


class MetricInterpretationAgent:
    """Provides analyst guidance for interpreting metrics and subtypes."""

    guidance_files = (
        "noi_guidance.md",
        "debt_guidance.md",
        "return_metrics_guidance.md",
        "exit_assumptions_guidance.md",
    )

    def instructions(self) -> str:
        return "\n\n".join(load_guidance(name) for name in self.guidance_files)

    def payload(self) -> dict[str, Any]:
        return {
            "role": "MetricInterpretationAgent",
            "task": (
                "Classify metric subtype, period, source authority, alternatives, "
                "and uncertainty before selecting any claim."
            ),
        }


class ClaimDiscoveryAgent:
    """Defines the claim output contract for GPT-discovered facts."""

    def instructions(self) -> str:
        return (
            "Return workbook claims selected by agent interpretation. Each claim must "
            "include metric, value, metric_subtype, period, source, evidence, confidence, "
            "why_selected, alternatives_considered, and uncertainty. Cite sheet/cell."
        )

    def payload(self) -> dict[str, Any]:
        return {
            "role": "ClaimDiscoveryAgent",
            "task": (
                "Choose investment-relevant claims from evidence only after considering "
                "alternatives. Do not rely on Python metric definitions."
            ),
        }


class AmbiguityReviewAgent:
    """Guides GPT to preserve uncertainty instead of forcing single answers."""

    def instructions(self) -> str:
        return (
            "If the workbook contains competing plausible values, preserve ambiguity. "
            "Return alternatives_considered with source, value, and reason_not_selected. "
            "If uncertainty is material, lower confidence and explain uncertainty."
        )

    def payload(self) -> dict[str, Any]:
        return {
            "role": "AmbiguityReviewAgent",
            "task": "Review candidate claims for ambiguity, competing sources, and subtype confusion.",
        }


def workbook_reader_agent_bundle(
    mental_model: WorkbookMentalModelResult,
    evidence_pack: WorkbookEvidencePackResult,
) -> dict[str, Any]:
    workbook_reader = WorkbookReaderAgent()
    metric_interpreter = MetricInterpretationAgent()
    claim_discovery = ClaimDiscoveryAgent()
    ambiguity_review = AmbiguityReviewAgent()
    return {
        "instructions": "\n\n".join([
            workbook_reader.instructions(),
            metric_interpreter.instructions(),
            claim_discovery.instructions(),
            ambiguity_review.instructions(),
        ]),
        "roles": [
            workbook_reader.payload(mental_model, evidence_pack),
            metric_interpreter.payload(),
            claim_discovery.payload(),
            ambiguity_review.payload(),
        ],
    }
