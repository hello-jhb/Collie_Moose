"""
Regression checks for Moose Deal Snapshot population.

Run: python3 test_moose_snapshot.py
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

from openpyxl import Workbook

from moose.pipeline import run_financial_model_reasoning
from moose.snapshot import SNAPSHOT_METRICS, build_snapshot_debug
from moose.trust.verifier import TrustVerifier
from moose.workbook.claim_extractor import FallbackWorkbookClaimExtractor


SAMPLE = Path("sample/BAC_vClosing.xlsx")
EXPECTED_BASELINE = {
    "purchase_price",
    "total_project_cost",
    "debt_amount",
    "equity_required",
    "loan_to_value",
    "interest_rate",
    "levered_irr",
    "equity_multiple",
    "exit_cap_rate",
    "sale_value",
}
DIRECT_METRICS = {
    "debt_amount",
    "loan_to_value",
    "interest_rate",
    "exit_cap_rate",
}


def main() -> int:
    scale_failure = _check_scaled_currency_claim()
    if scale_failure:
        print("Moose currency scale regression failed:")
        print(f"  [FAIL] {scale_failure}")
        return 1

    if not SAMPLE.exists():
        print(f"Missing sample workbook: {SAMPLE}")
        return 1

    result = run_financial_model_reasoning(SAMPLE)
    verification_run = result["verification_run"]
    debug_rows = build_snapshot_debug(
        SNAPSHOT_METRICS,
        verification_run["claim_result"],
        verification_run["verification"],
    )
    by_metric = {
        row["expected_metric_key"]: row
        for row in debug_rows
    }

    failures = []
    for metric in sorted(EXPECTED_BASELINE):
        row = by_metric.get(metric)
        if not row:
            failures.append(f"{metric}: no debug row")
            continue
        if not row["displayed"]:
            failures.append(f"{metric}: {row['missing_reason']}")

    if failures:
        print("Moose snapshot regression failed:")
        for failure in failures:
            print(f"  [FAIL] {failure}")
        return 1

    facts = verification_run["verification"]["verified_facts"]
    facts_by_subject = {
        fact["metric_or_subject"]: fact
        for fact in facts
        if fact.get("metric_or_subject") in DIRECT_METRICS
    }
    unlabeled_fallback = [
        metric
        for metric in sorted(DIRECT_METRICS)
        if facts_by_subject.get(metric, {}).get("fact_origin") == "fallback"
        and facts_by_subject.get(metric, {}).get("extraction_method") != "deterministic_fallback"
    ]
    if unlabeled_fallback:
        print("Moose deterministic fallback labeling regression failed:")
        for metric in unlabeled_fallback:
            print(f"  [FAIL] {metric}: fallback fact is not labeled deterministic_fallback")
        return 1

    missing_rationale = [
        metric
        for metric in sorted(DIRECT_METRICS)
        if not facts_by_subject.get(metric, {}).get("why_selected")
    ]
    if missing_rationale:
        print("Moose claim rationale regression failed:")
        for metric in missing_rationale:
            print(f"  [FAIL] {metric}: no why_selected rationale")
        return 1

    reasoning = result["reasoning"]
    readout_text = " ".join([
        str(reasoning.get("answer_summary", "")),
        " ".join(str(value) for value in reasoning.get("sections", {}).values()),
    ])
    bad_fragments = [" percent from", " currency from", " multiple from"]
    bad_units = [fragment for fragment in bad_fragments if fragment in readout_text]
    if bad_units:
        print("Moose readout unit-format regression failed:")
        for fragment in bad_units:
            print(f"  [FAIL] raw unit phrase still present: {fragment!r}")
        return 1
    expected_display_fragments = ["$", "%", "x"]
    missing_display = [
        fragment for fragment in expected_display_fragments
        if fragment not in readout_text
    ]
    if missing_display:
        print("Moose readout display-format regression failed:")
        for fragment in missing_display:
            print(f"  [FAIL] formatted fragment missing: {fragment!r}")
        return 1

    print("ALL PASS")
    for metric in sorted(EXPECTED_BASELINE):
        row = by_metric[metric]
        print(f"  [PASS] {metric} -> {row['source_sheet']}!{row['source_cell'] or 'row' + str(row['source_row'])}")
    return 0


def _check_scaled_currency_claim() -> str | None:
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Assumptions"
    worksheet["A1"] = "Sources and Uses ($000s)"
    worksheet["E48"] = "Loan Amount"
    worksheet["F48"] = 37_700

    extractor = FallbackWorkbookClaimExtractor()
    mental_model = SimpleNamespace(
        expected_sections=["debt", "capital_structure"],
        expected_metric_families=["debt", "capital_structure"],
        likely_authoritative_sources={"debt_amount": ["Debt", "Sources & Uses", "Summary", "Assumptions"]},
        important_sheets=["Assumptions"],
        confidence=0.8,
    )
    claims = extractor._claims_from_sheet(
        "scaled.xlsx",
        worksheet,
        {"debt", "capital_structure"},
        mental_model,
    )
    debt_claim = next((claim for claim in claims if claim["metric_or_subject"] == "debt_amount"), None)
    if not debt_claim:
        return "Debt claim was not extracted from scaled assumption sheet."
    if debt_claim["value"] != 37_700_000:
        return f"Debt claim value was {debt_claim['value']}, expected 37700000."

    with tempfile.NamedTemporaryFile(suffix=".xlsx") as handle:
        workbook.save(handle.name)
        verification = TrustVerifier().verify_claims(handle.name, [debt_claim])
    fact = verification.verified_facts[0]
    if fact["verification_status"] not in {"verified", "verified_with_caveat"}:
        return f"Scaled debt claim verification status was {fact['verification_status']}."
    if fact["verified_value"] != 37_700_000:
        return f"Scaled debt fact value was {fact['verified_value']}, expected 37700000."
    return None


if __name__ == "__main__":
    sys.exit(main())
