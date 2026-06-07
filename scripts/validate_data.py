#!/usr/bin/env python3
"""Validate company data files used by the static site."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPANIES_DIR = ROOT / "public" / "data" / "companies"
INDEX_PATH = ROOT / "public" / "data" / "company-index.json"

REQUIRED_TOP_LEVEL = {
    "schemaVersion",
    "id",
    "ticker",
    "exchange",
    "market",
    "name",
    "legalName",
    "currency",
    "sector",
    "industry",
    "homepage",
    "lastUpdated",
    "summary",
    "updateCadence",
    "business",
    "supplyChain",
    "financials",
    "news",
    "filings",
    "sources",
}


def collect_source_refs(report: dict) -> set[str]:
    refs: set[str] = set()

    def visit(value: object) -> None:
        if isinstance(value, dict):
            source_ids = value.get("sourceIds")
            if isinstance(source_ids, list):
                refs.update(str(source_id) for source_id in source_ids)
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(report)
    return refs


def validate_report(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        report = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"{path}: invalid JSON: {exc}"]

    missing = REQUIRED_TOP_LEVEL - set(report)
    if missing:
        errors.append(f"{path.name}: missing keys {sorted(missing)}")

    if report.get("market") not in {"US", "CN"}:
        errors.append(f"{path.name}: market must be US or CN")

    source_ids = {source.get("id") for source in report.get("sources", [])}
    if None in source_ids:
        errors.append(f"{path.name}: every source needs an id")

    for ref in collect_source_refs(report):
        if ref not in source_ids:
            errors.append(f"{path.name}: missing source for reference {ref}")

    if not report.get("financials", {}).get("highlights"):
        errors.append(f"{path.name}: needs financial highlights")

    if not report.get("supplyChain", {}).get("tiers"):
        errors.append(f"{path.name}: needs supply-chain tiers")

    return errors


def main() -> int:
    errors: list[str] = []

    if not INDEX_PATH.exists():
        errors.append("company-index.json is missing")

    company_files = sorted(COMPANIES_DIR.glob("*.json"))
    if not company_files:
        errors.append("no company data files found")

    for path in company_files:
        errors.extend(validate_report(path))

    if errors:
        print("Data validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"Validated {len(company_files)} company data files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
