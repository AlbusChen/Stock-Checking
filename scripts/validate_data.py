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
    "labels",
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
CONFIDENCE_LEVELS = {"high", "medium", "low"}
RELATIONSHIP_DIRECTIONS = {
    "target",
    "upstream-raw-material",
    "upstream-component",
    "upstream-equipment",
    "upstream-manufacturing",
    "direct-supplier",
    "system-integration",
    "downstream-customer",
    "indirect-demand",
    "peer-theme",
    "partner",
    "unknown",
}


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


def validate_listing(errors: list[str], path: Path, listing: object, label: str) -> None:
    if not isinstance(listing, dict):
        errors.append(f"{path.name}: {label} needs listing")
        return

    status = listing.get("status")
    if status not in LISTING_STATUSES:
        errors.append(f"{path.name}: {label} has invalid listing status {status}")
    if status == "listed":
        if not listing.get("ticker") or not listing.get("exchange"):
            errors.append(f"{path.name}: listed {label} needs ticker and exchange")
        if not listing.get("stockUrl"):
            errors.append(f"{path.name}: listed {label} needs stockUrl")
    if status == "listed-parent":
        if not listing.get("parentTicker") or not listing.get("parentExchange"):
            errors.append(f"{path.name}: listed-parent {label} needs parentTicker and parentExchange")
        if not listing.get("parentStockUrl"):
            errors.append(f"{path.name}: listed-parent {label} needs parentStockUrl")


def validate_score(errors: list[str], path: Path, score: object, label: str) -> None:
    if not isinstance(score, int) or score < 1 or score > 5:
        errors.append(f"{path.name}: {label} score must be an integer from 1 to 5")


def validate_relationship_strength(errors: list[str], path: Path, item: object, label: str) -> None:
    if not isinstance(item, dict):
        errors.append(f"{path.name}: {label} needs relationshipStrength")
        return

    validate_score(errors, path, item.get("score"), label)
    if item.get("direction") not in RELATIONSHIP_DIRECTIONS:
        errors.append(f"{path.name}: {label} has invalid relationship direction {item.get('direction')}")
    if item.get("confidence") not in CONFIDENCE_LEVELS:
        errors.append(f"{path.name}: {label} relationshipStrength needs confidence")
    require_localized(errors, path, item, "label", label)
    require_localized(errors, path, item, "rationale", label)


def validate_theme_exposure(errors: list[str], path: Path, exposure: object, label: str) -> None:
    if not isinstance(exposure, dict):
        errors.append(f"{path.name}: {label} must be an object")
        return

    validate_score(errors, path, exposure.get("score"), label)
    if exposure.get("confidence") not in CONFIDENCE_LEVELS:
        errors.append(f"{path.name}: {label} needs confidence")
    require_localized(errors, path, exposure, "theme", label)
    require_localized(errors, path, exposure, "role", label)
    require_localized(errors, path, exposure, "rationale", label)


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

    labels = report.get("labels")
    if (
        not isinstance(labels, list)
        or not labels
        or not all(isinstance(label, str) and label.strip() for label in labels)
    ):
        errors.append(f"{path.name}: labels must be a non-empty string list")

    theme_exposure = report.get("themeExposure")
    if not isinstance(theme_exposure, list) or not theme_exposure:
        errors.append(f"{path.name}: needs themeExposure list")
    else:
        for index, exposure in enumerate(theme_exposure):
            validate_theme_exposure(errors, path, exposure, f"themeExposure[{index}]")

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

    business = report.get("business", {})
    if not isinstance(business.get("description"), str) or not business.get("description", "").strip():
        errors.append(f"{path.name}: business needs description")
    if not isinstance(business.get("thesis"), str) or not business.get("thesis", "").strip():
        errors.append(f"{path.name}: business needs thesis")
    if not isinstance(business.get("revenueModel"), list) or not business.get("revenueModel"):
        errors.append(f"{path.name}: business needs revenueModel list")
    if not isinstance(business.get("riskNotes"), list) or not business.get("riskNotes"):
        errors.append(f"{path.name}: business needs riskNotes list")

    if not report.get("supplyChain", {}).get("tiers"):
        errors.append(f"{path.name}: needs supply-chain tiers")

    for metric in report.get("financials", {}).get("highlights", []):
        label = metric.get("label", "unnamed metric")
        require_localized(errors, path, metric, "label", f"metric {label}")
        require_localized(errors, path, metric, "period", f"metric {label}")
        if metric.get("change"):
            require_localized(errors, path, metric, "change", f"metric {label}")

    for trend in report.get("financials", {}).get("trends", []):
        label = trend.get("label", "unnamed trend")
        if not trend.get("id"):
            errors.append(f"{path.name}: trend {label} needs id")
        if trend.get("cadence") not in {"annual", "quarterly"}:
            errors.append(f"{path.name}: trend {label} needs cadence annual or quarterly")
        if not trend.get("sourceIds"):
            errors.append(f"{path.name}: trend {label} needs sourceIds")
        require_localized(errors, path, trend, "label", f"trend {label}")
        if trend.get("note"):
            require_localized(errors, path, trend, "note", f"trend {label}")
        points = trend.get("points")
        if not isinstance(points, list) or len(points) < 2:
            errors.append(f"{path.name}: trend {label} needs at least two points")
            continue
        for point in points:
            period = point.get("period", "unnamed period")
            require_localized(errors, path, point, "period", f"trend {label} point {period}")
            if not isinstance(point.get("value"), (int, float)):
                errors.append(f"{path.name}: trend {label} point {period} needs numeric value")

    for segment in report.get("financials", {}).get("revenueMix", []):
        label = segment.get("name", "unnamed revenue segment")
        require_localized(errors, path, segment, "name", f"revenue segment {label}")
        require_localized(errors, path, segment, "note", f"revenue segment {label}")

    for period in report.get("financials", {}).get("revenueMixHistory", []):
        label = period.get("period", "unnamed revenue mix period")
        require_localized(errors, path, period, "period", f"revenue mix history {label}")
        if period.get("note"):
            require_localized(errors, path, period, "note", f"revenue mix history {label}")
        segments = period.get("segments")
        if not isinstance(segments, list) or not segments:
            errors.append(f"{path.name}: revenue mix history {label} needs segments")
            continue
        for segment in segments:
            segment_name = segment.get("name", "unnamed history segment")
            require_localized(errors, path, segment, "name", f"revenue mix history segment {segment_name}")
            if not isinstance(segment.get("revenue"), (int, float)):
                errors.append(f"{path.name}: revenue mix history segment {segment_name} needs numeric revenue")

    for item in report.get("news", []):
        label = item.get("title", "untitled news")
        require_localized(errors, path, item, "title", f"news {label}")
        require_localized(errors, path, item, "category", f"news {label}")
        require_localized(errors, path, item, "summary", f"news {label}")
        require_localized(errors, path, item, "impact", f"news {label}")

    for tier in report.get("supplyChain", {}).get("tiers", []):
        tier_name = tier.get("title", "untitled tier")
        if not isinstance(tier.get("level"), int):
            errors.append(f"{path.name}: supply-chain tier {tier_name} needs numeric level")
        if tier.get("confidence") not in CONFIDENCE_LEVELS:
            errors.append(f"{path.name}: supply-chain tier {tier_name} needs confidence")
        require_localized(errors, path, tier, "notes", f"supply-chain tier {tier_name}")
        require_localized_list(errors, path, tier, "materials", f"supply-chain tier {tier_name}")
        if not tier.get("sourceIds"):
            errors.append(f"{path.name}: supply-chain tier {tier_name} needs sourceIds")
        entities = tier.get("entities")
        if not isinstance(entities, list) or not entities:
            errors.append(f"{path.name}: supply-chain tier {tier_name} needs entities")
            continue

        for entity in entities:
            name = entity.get("name", "unnamed supplier")
            require_localized(errors, path, entity, "name", f"supplier {name}")
            if not entity.get("relationship"):
                errors.append(f"{path.name}: supplier {name} needs relationship")
            require_localized(errors, path, entity, "relationship", f"supplier {name}")
            if not entity.get("productsServices"):
                errors.append(f"{path.name}: supplier {name} needs productsServices")
            require_localized_list(errors, path, entity, "productsServices", f"supplier {name}")
            if not entity.get("sourceIds"):
                errors.append(f"{path.name}: supplier {name} needs sourceIds")

            validate_listing(errors, path, entity.get("listing"), f"supplier {name}")
            validate_relationship_strength(
                errors,
                path,
                entity.get("relationshipStrength"),
                f"supplier {name} relationshipStrength",
            )

    raw_materials = report.get("supplyChain", {}).get("rawMaterials")
    if not isinstance(raw_materials, list) or not raw_materials:
        errors.append(f"{path.name}: needs rawMaterials list")
    else:
        for material in raw_materials:
            if not isinstance(material, dict):
                errors.append(f"{path.name}: rawMaterial must be an object")
                continue
            label = material.get("name", "unnamed raw material")
            require_localized(errors, path, material, "name", f"raw material {label}")
            require_localized(errors, path, material, "usedIn", f"raw material {label}")
            require_localized(errors, path, material, "risk", f"raw material {label}")
            require_localized_list(errors, path, material, "upstream", f"raw material {label}")
            if material.get("confidence") not in CONFIDENCE_LEVELS:
                errors.append(f"{path.name}: raw material {label} needs confidence")

    downstream = report.get("supplyChain", {}).get("downstream")
    if isinstance(downstream, dict):
        require_localized(errors, path, downstream, "thesis", "downstream thesis")
        tiers = downstream.get("tiers")
        if not isinstance(tiers, list) or not tiers:
            errors.append(f"{path.name}: downstream needs tiers")
        else:
            for tier in tiers:
                tier_name = tier.get("title", "untitled downstream tier")
                if not isinstance(tier.get("level"), int):
                    errors.append(f"{path.name}: downstream tier {tier_name} needs numeric level")
                if tier.get("confidence") not in CONFIDENCE_LEVELS:
                    errors.append(f"{path.name}: downstream tier {tier_name} needs confidence")
                if not tier.get("sourceIds"):
                    errors.append(f"{path.name}: downstream tier {tier_name} needs sourceIds")
                require_localized(errors, path, tier, "title", f"downstream tier {tier_name}")
                require_localized(errors, path, tier, "notes", f"downstream tier {tier_name}")
                entities = tier.get("entities")
                if not isinstance(entities, list) or not entities:
                    errors.append(f"{path.name}: downstream tier {tier_name} needs entities")
                    continue
                for entity in entities:
                    name = entity.get("name", "unnamed downstream entity")
                    require_localized(errors, path, entity, "name", f"downstream customer {name}")
                    require_localized(errors, path, entity, "customerRole", f"downstream customer {name}")
                    require_localized(errors, path, entity, "relationship", f"downstream customer {name}")
                    if not entity.get("productsServices"):
                        errors.append(f"{path.name}: downstream customer {name} needs productsServices")
                    require_localized_list(errors, path, entity, "productsServices", f"downstream customer {name}")
                    if not entity.get("sourceIds"):
                        errors.append(f"{path.name}: downstream customer {name} needs sourceIds")
                    validate_listing(errors, path, entity.get("listing"), f"downstream customer {name}")
                    validate_relationship_strength(
                        errors,
                        path,
                        entity.get("relationshipStrength"),
                        f"downstream customer {name} relationshipStrength",
                    )

    for filing in report.get("filings", []):
        form = filing.get("form", "unnamed filing")
        if not filing.get("title"):
            errors.append(f"{path.name}: filing {form} needs title")
        if not filing.get("filedAt"):
            errors.append(f"{path.name}: filing {form} needs filedAt")
        if not filing.get("url"):
            errors.append(f"{path.name}: filing {form} needs url")

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
