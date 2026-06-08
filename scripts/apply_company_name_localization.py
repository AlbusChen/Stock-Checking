#!/usr/bin/env python3
"""Add Chinese and English display names for supply-chain entities."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPANIES_DIR = ROOT / "public" / "data" / "companies"

NAME_ZH = {
    "Accenture": "埃森哲",
    "Air Liquide": "液化空气",
    "Alphabet / Google Cloud": "Alphabet / 谷歌云",
    "Amazon Web Services": "亚马逊云科技",
    "Amkor": "安靠科技",
    "Apple": "苹果",
    "Applied Materials": "应用材料",
    "ASE Technology": "日月光投控",
    "ASE Technology / SPIL": "日月光投控 / 矽品",
    "ASML": "阿斯麦",
    "Cellular carriers and resellers": "蜂窝网络运营商和经销商",
    "Compal": "仁宝电脑",
    "CoreWeave": "CoreWeave",
    "Dell": "戴尔",
    "Dell Technologies": "戴尔科技",
    "Direct retail, online store and direct sales force": "直营零售、在线商店与直销团队",
    "Entegris": "英特格",
    "Foxconn": "富士康",
    "Hewlett Packard Enterprise": "慧与科技",
    "Hon Hai Precision / Foxconn": "鸿海精密 / 富士康",
    "HP Inc.": "惠普",
    "HPE": "慧与科技",
    "IBM": "IBM",
    "Ibiden": "揖斐电",
    "Intel": "英特尔",
    "JSR": "JSR",
    "KLA": "KLA",
    "Lam Research": "泛林集团",
    "Lenovo": "联想",
    "LG Display": "乐金显示",
    "Linde": "林德",
    "Luxshare Precision": "立讯精密",
    "Micron": "美光科技",
    "Microsoft": "微软",
    "Microsoft Surface": "微软 Surface",
    "Murata": "村田制作所",
    "NVIDIA": "英伟达",
    "Oracle Cloud Infrastructure": "甲骨文云基础设施",
    "Pegatron": "和硕",
    "Quanta": "广达电脑",
    "Salesforce": "赛富时",
    "Samsung Display": "三星显示",
    "Samsung Electronics": "三星电子",
    "Shin-Etsu": "信越化学",
    "Shinko Electric Industries": "新光电气工业",
    "SK Hynix": "SK 海力士",
    "Sony Semiconductor Solutions": "索尼半导体解决方案",
    "SUMCO": "胜高",
    "Sunwoda": "欣旺达",
    "Super Micro Computer": "超微电脑",
    "Supermicro": "超微电脑",
    "TDK": "TDK",
    "Tokyo Electron": "东京电子",
    "TSMC": "台积电",
    "Unimicron": "欣兴电子",
    "Wistron": "纬创",
}


def localize_entity(entity: dict, path: Path) -> None:
    name = entity.get("name")
    if not isinstance(name, str):
        return
    name_zh = NAME_ZH.get(name)
    if not name_zh:
        raise KeyError(f"{path.name}: missing Chinese name mapping for {name}")
    entity["nameZh"] = name_zh
    entity["nameEn"] = name


def apply_names(path: Path) -> None:
    report = json.loads(path.read_text(encoding="utf-8"))
    for tier in report.get("supplyChain", {}).get("tiers", []):
        for entity in tier.get("entities", []):
            localize_entity(entity, path)
    for tier in report.get("supplyChain", {}).get("downstream", {}).get("tiers", []):
        for entity in tier.get("entities", []):
            localize_entity(entity, path)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    company_files = sorted(COMPANIES_DIR.glob("*.json"))
    for path in company_files:
        apply_names(path)
    print(f"Applied localized company names to {len(company_files)} company files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
