#!/usr/bin/env python3
"""Refresh recent SEC filing links for tracked US companies."""

from __future__ import annotations

import json
import os
import sys
import urllib.request
import gzip
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPANIES_DIR = ROOT / "public" / "data" / "companies"
USER_AGENT = os.getenv(
    "SEC_USER_AGENT",
    "Stock-Checking research bot contact@example.com",
)


def sec_json(cik: str) -> dict:
    padded = cik.zfill(10)
    request = urllib.request.Request(
        f"https://data.sec.gov/submissions/CIK{padded}.json",
        headers={"User-Agent": USER_AGENT, "Accept-Encoding": "gzip, deflate"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        raw = response.read()
        if response.headers.get("Content-Encoding", "").lower() == "gzip" or raw.startswith(b"\x1f\x8b"):
            raw = gzip.decompress(raw)
        return json.loads(raw.decode("utf-8"))


def archive_url(cik: str, accession: str, primary_doc: str) -> str:
    cik_int = str(int(cik))
    accession_no_dash = accession.replace("-", "")
    return f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{accession_no_dash}/{primary_doc}"


def update_report(path: Path) -> bool:
    report = json.loads(path.read_text(encoding="utf-8"))
    sec = report.get("automation", {}).get("sec")
    if not sec:
        return False

    forms = set(sec.get("forms", []))
    cik = sec["cik"]
    data = sec_json(cik)
    recent = data.get("filings", {}).get("recent", {})

    filings = []
    for index, form in enumerate(recent.get("form", [])):
        if form not in forms:
            continue
        accession = recent["accessionNumber"][index]
        primary_doc = recent["primaryDocument"][index]
        filings.append(
            {
                "form": form,
                "filedAt": recent["filingDate"][index],
                "reportDate": recent.get("reportDate", [""])[index],
                "title": f"{form} filed {recent['filingDate'][index]}",
                "url": archive_url(cik, accession, primary_doc),
            }
        )
        if len(filings) >= 12:
            break

    if not filings:
        return False

    old = report.get("filings", [])
    if old == filings:
        return False

    report["filings"] = filings
    report["lastUpdated"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return True


def main() -> int:
    changed = 0
    for path in sorted(COMPANIES_DIR.glob("*.json")):
        try:
            if update_report(path):
                changed += 1
                print(f"Updated filings: {path.name}")
        except Exception as exc:  # noqa: BLE001
            print(f"Warning: failed to update {path.name}: {exc}", file=sys.stderr)

    print(f"SEC filing refresh complete; changed={changed}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
