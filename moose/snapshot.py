"""Deal Snapshot mapping and debug helpers."""

from __future__ import annotations

from typing import Any


SNAPSHOT_METRICS = [
    ("purchase_price", "Purchase Price"),
    ("total_project_cost", "Total Project Cost"),
    ("debt_amount", "Debt"),
    ("equity_required", "Equity"),
    ("loan_to_value", "LTV"),
    ("interest_rate", "Interest Rate"),
    ("stabilized_noi", "NOI"),
    ("levered_irr", "Levered IRR"),
    ("equity_multiple", "Equity Multiple"),
    ("exit_cap_rate", "Exit Cap"),
    ("sale_value", "Sale Value"),
]

METRIC_ALIASES = {
    "debt": "debt_amount",
    "ltv": "loan_to_value",
    "exit_cap": "exit_cap_rate",
    "sale_price": "sale_value",
    "noi": "stabilized_noi",
}

DISPLAY_STATUSES = {"verified", "verified_with_caveat"}


def normalize_metric(metric: Any) -> str:
    key = str(metric or "")
    return METRIC_ALIASES.get(key, key)


def facts_by_metric(facts: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    mapped: dict[str, dict[str, Any]] = {}
    for fact in facts:
        metric = normalize_metric(fact.get("metric_or_subject"))
        if not metric or fact.get("verification_status") not in DISPLAY_STATUSES:
            continue
        mapped.setdefault(metric, fact)
    return mapped


def build_snapshot_debug(
    snapshot_metrics: list[tuple[str, str]],
    claim_result: dict[str, Any],
    verification: dict[str, Any],
) -> list[dict[str, Any]]:
    claims = claim_result.get("claims", []) or []
    rejected_claims = claim_result.get("rejected_claims", []) or []
    facts = verification.get("verified_facts", []) or []
    fact_map = facts_by_metric(facts)
    raw_fact_map = {
        normalize_metric(fact.get("metric_or_subject")): fact
        for fact in facts
        if fact.get("metric_or_subject")
    }
    grounded_claim_map = {
        normalize_metric(claim.get("metric_or_subject")): claim
        for claim in claims
        if claim.get("metric_or_subject")
    }
    rejected_claim_map = {}
    for rejected in rejected_claims:
        claim = rejected.get("claim") if isinstance(rejected, dict) else None
        if isinstance(claim, dict) and claim.get("metric_or_subject"):
            rejected_claim_map[normalize_metric(claim.get("metric_or_subject"))] = rejected

    rows: list[dict[str, Any]] = []
    for metric, label in snapshot_metrics:
        expected_metric = normalize_metric(metric)
        grounded_claim = grounded_claim_map.get(expected_metric)
        rejected_claim = rejected_claim_map.get(expected_metric)
        raw_fact = raw_fact_map.get(expected_metric)
        displayed_fact = fact_map.get(expected_metric)
        source = _source_for(displayed_fact or raw_fact or (grounded_claim if isinstance(grounded_claim, dict) else None))
        rows.append({
            "label": label,
            "expected_metric_key": expected_metric,
            "claim_exists": bool(grounded_claim or rejected_claim),
            "grounded": bool(grounded_claim),
            "verified": bool(raw_fact and raw_fact.get("verification_status") in DISPLAY_STATUSES),
            "displayed": bool(displayed_fact),
            "source_sheet": source.get("sheet"),
            "source_cell": source.get("cell"),
            "source_row": source.get("row"),
            "missing_reason": _missing_reason(
                expected_metric=expected_metric,
                grounded_claim=grounded_claim,
                rejected_claim=rejected_claim,
                raw_fact=raw_fact,
                displayed_fact=displayed_fact,
            ),
        })
    return rows


def _missing_reason(
    expected_metric: str,
    grounded_claim: dict[str, Any] | None,
    rejected_claim: dict[str, Any] | None,
    raw_fact: dict[str, Any] | None,
    displayed_fact: dict[str, Any] | None,
) -> str:
    if displayed_fact:
        return ""
    if rejected_claim:
        return "failed grounding"
    if not grounded_claim and not raw_fact:
        return "not extracted"
    if raw_fact and raw_fact.get("verification_status") in {"rejected", "contradicted"}:
        return "rejected"
    if raw_fact and raw_fact.get("verification_status") in DISPLAY_STATUSES:
        return "verified but not mapped"
    if raw_fact:
        return str(raw_fact.get("verification_status") or "not displayed")
    if grounded_claim:
        return "not verified"
    return f"not extracted: {expected_metric}"


def _source_for(item: dict[str, Any] | None) -> dict[str, Any]:
    if not item:
        return {"sheet": None, "cell": None, "row": None}
    source_location = item.get("source_location")
    if isinstance(source_location, dict):
        return {
            "sheet": source_location.get("sheet"),
            "cell": source_location.get("cell"),
            "row": source_location.get("row"),
        }
    source = item.get("source")
    if isinstance(source, str) and "!" in source:
        sheet, ref = source.split("!", 1)
        if ref.lower().startswith("row"):
            row_text = "".join(ch for ch in ref if ch.isdigit())
            return {"sheet": sheet, "cell": None, "row": int(row_text) if row_text else None}
        return {"sheet": sheet, "cell": ref, "row": None}
    return {"sheet": None, "cell": None, "row": None}
