"""
Regression checks for Moose Deal Snapshot population.

Run: python3 test_moose_snapshot.py
"""

from __future__ import annotations

import sys
from pathlib import Path

from moose.pipeline import run_financial_model_reasoning
from moose.snapshot import SNAPSHOT_METRICS, build_snapshot_debug


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


def main() -> int:
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

    print("ALL PASS")
    for metric in sorted(EXPECTED_BASELINE):
        row = by_metric[metric]
        print(f"  [PASS] {metric} -> {row['source_sheet']}!{row['source_cell'] or 'row' + str(row['source_row'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
