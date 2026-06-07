#!/usr/bin/env python3
"""Validate company data files used by the static site."""

from __future__ import annotations

import json
import re
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

LISTING_STATUSES = {"listed", "listed-parent", "private", "delisted", "unknown"}


def has_cjk(value: str) -> bool:
    return bool(re.search(r"[\u3400-\u9fff]", value))


def has_localized_pair(item: dict, field: str) -> bool:
    base = item.get(field)
    if not isinstance(base, str):
        base = ""
    zh = item.get(f"{field}Zh") or (base if has_cjk(base) else "")
    en = item.get(f"{field}En") or (base if base and not has_cjk(base) else "")
    return isinstance(zh, str) and bool(zh.strip()) and isinstance(en, str) and bool(en.strip())


def has_localized_list_pair(item: dict, field: str) -> bool:
    base = item.get(field)
    if not isinstance(base, list) or not base:
        return False
    zh = item.get(f"{field}Zh")
    en = item.get(f"{field}En")
    return (
        isinstance(zh, list)
        and isinstance(en, list)
        and len(zh) == len(base)
        and len(en) == len(base)
        and all(isinstance(value, str) and value.strip() for value in zh)
        and all(isinstance(value, str) and value.strip() for value in en)
    )


def require_localized(errors: list[str], path: Path, item: dict, field: str, label: str) -> None:
    if not has_localized_pair(item, field):
        errors.append(f"{path.name}: {label} needs {field}Zh and {field}En")


def require_localized_list(errors: list[str], path: Path, item: dict, field: str, label: str) -> None:
    if not has_localized_list_pair(item, field):
        errors.append(f"{path.name}: {label} needs {field}Zh and {field}En lists")


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
    if isinstance(report.get("financials"), dict):
        require_localized(errors, path, report["financials"], "latestPeriod", "financial latestPeriod")

    if not report.get("supplyChain", {}).get("tiers"):
        errors.append(f"{path.name}: needs supply-chain tiers")

    for metric in report.get("financials", {}).get("highlights", []):
        label = metric.get("label", "unnamed metric")
        require_localized(errors, path, metric, "label", f"metric {label}")
        require_localized(errors, path, metric, "period", f"metric {label}")
        if metric.get("change"):
            require_localized(errors, path, metric, "change", f"metric {label}")

    for segment in report.get("financials", {}).get("revenueMix", []):
        label = segment.get("name", "unnamed revenue segment")
        require_localized(errors, path, segment, "name", f"revenue segment {label}")
        require_localized(errors, path, segment, "note", f"revenue segment {label}")

    for item in report.get("news", []):
        label = item.get("title", "untitled news")
        require_localized(errors, path, item, "title", f"news {label}")
        require_localized(errors, path, item, "category", f"news {label}")
        require_localized(errors, path, item, "summary", f"news {label}")
        require_localized(errors, path, item, "impact", f"news {label}")

    for tier in report.get("supplyChain", {}).get("tiers", []):
        tier_name = tier.get("title", "untitled tier")
        entities = tier.get("entities")
        if not isinstance(entities, list) or not entities:
            errors.append(f"{path.name}: supply-chain tier {tier_name} needs entities")
            continue

        for entity in entities:
            name = entity.get("name", "unnamed supplier")
            if not entity.get("relationship"):
                errors.append(f"{path.name}: supplier {name} needs relationship")
            require_localized(errors, path, entity, "relationship", f"supplier {name}")
            if not entity.get("productsServices"):
                errors.append(f"{path.name}: supplier {name} needs productsServices")
            require_localized_list(errors, path, entity, "productsServices", f"supplier {name}")
            if not entity.get("sourceIds"):
                errors.append(f"{path.name}: supplier {name} needs sourceIds")

            listing = entity.get("listing")
            if not isinstance(listing, dict):
                errors.append(f"{path.name}: supplier {name} needs listing")
                continue

            status = listing.get("status")
            if status not in LISTING_STATUSES:
                errors.append(f"{path.name}: supplier {name} has invalid listing status {status}")
            if status == "listed":
                if not listing.get("ticker") or not listing.get("exchange"):
                    errors.append(f"{path.name}: listed supplier {name} needs ticker and exchange")
                if not listing.get("stockUrl"):
                    errors.append(f"{path.name}: listed supplier {name} needs stockUrl")
            if status == "listed-parent":
                if not listing.get("parentTicker") or not listing.get("parentExchange"):
                    errors.append(f"{path.name}: listed-parent supplier {name} needs parentTicker and parentExchange")
                if not listing.get("parentStockUrl"):
                    errors.append(f"{path.name}: listed-parent supplier {name} needs parentStockUrl")

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
