#!/usr/bin/env python3
"""Refresh latest RSS news items for tracked companies.

The script is intentionally dependency-free so it can run on GitHub Actions.
Feeds that fail are skipped, leaving the last curated data in place.
"""

from __future__ import annotations

import json
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPANIES_DIR = ROOT / "public" / "data" / "companies"
MAX_ITEMS = 8


def clean_text(value: str | None) -> str:
    if not value:
        return ""
    value = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def parse_date(value: str | None) -> str:
    if not value:
        return datetime.now(timezone.utc).date().isoformat()
    try:
        return parsedate_to_datetime(value).date().isoformat()
    except (TypeError, ValueError):
        return value[:10]


def bilingual_auto_news(title: str, summary: str) -> dict:
    summary = summary[:260]
    return {
        "titleZh": f"自动抓取新闻：{title}",
        "titleEn": title,
        "categoryZh": "新闻",
        "categoryEn": "News",
        "summaryZh": "自动抓取摘要，需人工翻译与复核。" if summary else "自动抓取条目，需人工补充摘要。",
        "summaryEn": summary,
        "impactZh": "自动抓取条目，需要人工复核业务影响。",
        "impactEn": "Automatically fetched item; business impact requires manual review.",
    }


def load_feed(url: str) -> list[dict]:
    request = urllib.request.Request(url, headers={"User-Agent": "Stock-Checking research bot"})
    with urllib.request.urlopen(request, timeout=30) as response:
        raw = response.read()

    root = ET.fromstring(raw)
    channel_items = root.findall(".//item")
    atom_items = root.findall("{http://www.w3.org/2005/Atom}entry")
    items = channel_items or atom_items
    parsed: list[dict] = []

    for item in items[:MAX_ITEMS]:
        title = clean_text(item.findtext("title") or item.findtext("{http://www.w3.org/2005/Atom}title"))
        link = clean_text(item.findtext("link"))
        if not link:
            atom_link = item.find("{http://www.w3.org/2005/Atom}link")
            link = atom_link.attrib.get("href", "") if atom_link is not None else ""
        summary = clean_text(
            item.findtext("description")
            or item.findtext("summary")
            or item.findtext("{http://www.w3.org/2005/Atom}summary")
        )
        date = parse_date(
            item.findtext("pubDate")
            or item.findtext("updated")
            or item.findtext("{http://www.w3.org/2005/Atom}updated")
        )
        if title and link:
            parsed.append({"title": title, "url": link, "summary": summary, "date": date})

    return parsed


def update_report(path: Path) -> bool:
    report = json.loads(path.read_text(encoding="utf-8"))
    feeds = report.get("automation", {}).get("newsFeeds", [])
    if not feeds:
        return False

    existing_titles = {item["title"] for item in report.get("news", [])}
    news = list(report.get("news", []))
    sources = list(report.get("sources", []))
    source_ids = {source["id"] for source in sources}
    changed = False

    for feed in feeds:
        try:
            items = load_feed(feed["url"])
        except Exception as exc:  # noqa: BLE001
            print(f"Warning: feed failed for {path.name}: {feed['url']} ({exc})", file=sys.stderr)
            continue

        for item in items[:3]:
            if item["title"] in existing_titles:
                continue
            source_id = f"rss-{report['id']}-{re.sub(r'[^a-z0-9]+', '-', item['title'].lower()).strip('-')[:50]}"
            if source_id not in source_ids:
                sources.append(
                    {
                        "id": source_id,
                        "title": item["title"],
                        "titleZh": f"自动抓取新闻：{item['title']}",
                        "titleEn": item["title"],
                        "publisher": feed["publisher"],
                        "url": item["url"],
                        "publishedAt": item["date"],
                        "accessedAt": datetime.now(timezone.utc).date().isoformat(),
                        "type": feed.get("sourceType", "news"),
                        "evidenceLevel": "strong" if feed.get("sourceType") in {"company", "exchange"} else "weak",
                        "evidenceLevelZh": "强证据" if feed.get("sourceType") in {"company", "exchange"} else "弱证据",
                        "evidenceLevelEn": "Strong" if feed.get("sourceType") in {"company", "exchange"} else "Weak",
                    }
                )
                source_ids.add(source_id)
            localized = bilingual_auto_news(item["title"], item["summary"])
            news.append(
                {
                    "date": item["date"],
                    "title": item["title"],
                    "category": "News",
                    "summary": item["summary"][:260],
                    "impact": "自动抓取条目，需要人工复核业务影响。",
                    **localized,
                    "sourceIds": [source_id],
                }
            )
            existing_titles.add(item["title"])
            changed = True

    if not changed:
        return False

    news.sort(key=lambda entry: entry["date"], reverse=True)
    report["news"] = news[:18]
    report["sources"] = sources
    report["lastUpdated"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return True


def main() -> int:
    changed = 0
    for path in sorted(COMPANIES_DIR.glob("*.json")):
        if update_report(path):
            changed += 1
            print(f"Updated news: {path.name}")

    print(f"News refresh complete; changed={changed}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
