#!/usr/bin/env python3
"""Rebuild the static company search index from company JSON files."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPANIES_DIR = ROOT / "public" / "data" / "companies"
INDEX_PATH = ROOT / "public" / "data" / "company-index.json"


def main() -> None:
    companies = []
    for path in sorted(COMPANIES_DIR.glob("*.json")):
      with path.open("r", encoding="utf-8") as handle:
          report = json.load(handle)
      companies.append(
          {
              "id": report["id"],
              "ticker": report["ticker"],
              "name": report["name"],
              "legalName": report["legalName"],
              "exchange": report["exchange"],
              "market": report["market"],
              "dataPath": f"data/companies/{path.name}",
              "aliases": report.get("aliases", []),
              "sector": report["sector"],
              "lastUpdated": report["lastUpdated"],
              "summary": report["summary"],
          }
      )

    payload = {
        "generatedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "companies": sorted(companies, key=lambda item: item["ticker"]),
    }

    INDEX_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {INDEX_PATH.relative_to(ROOT)} with {len(companies)} companies")


if __name__ == "__main__":
    main()
