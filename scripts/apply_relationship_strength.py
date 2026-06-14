#!/usr/bin/env python3
"""Apply relationship-strength scoring to company reports."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
COMPANIES_DIR = ROOT / "public" / "data" / "companies"

SCORE_LABELS = {
    5: ("核心瓶颈", "Core bottleneck"),
    4: ("强相关", "Strong relevance"),
    3: ("中相关", "Moderate relevance"),
    2: ("弱相关", "Weak relevance"),
    1: ("主题相关", "Thematic relevance"),
}

THEME_EXPOSURE_BY_TICKER: dict[str, dict[str, Any]] = {
    "NVDA": {
        "theme": ("英伟达相关", "NVIDIA-related"),
        "score": 5,
        "role": ("AI 加速计算核心平台", "Core AI accelerated-computing platform"),
        "rationale": (
            "目标公司本身是该主题的需求与供给锚点，供应链、客户和生态变化都会围绕它传导。",
            "The company itself is the anchor of this theme, with supply-chain, customer, and ecosystem changes transmitting around it.",
        ),
        "confidence": "high",
    },
    "TSM": {
        "theme": ("英伟达相关", "NVIDIA-related"),
        "score": 5,
        "role": ("核心制造瓶颈", "Core manufacturing bottleneck"),
        "rationale": (
            "先进制程和先进封装直接影响 AI 加速器供给弹性，处于比普通下游客户更靠近供给约束的位置。",
            "Advanced nodes and packaging directly shape AI accelerator supply elasticity, placing it closer to the supply bottleneck than ordinary downstream customers.",
        ),
        "confidence": "high",
    },
    "MU": {
        "theme": ("英伟达相关", "NVIDIA-related"),
        "score": 5,
        "role": ("HBM 与存储关键供给", "Critical HBM and memory supply"),
        "rationale": (
            "HBM/DRAM 直接进入 AI 加速器和数据中心平台，扩产、良率和认证会影响 GPU 系统交付。",
            "HBM/DRAM directly enters AI accelerators and data-center platforms, so capacity, yield, and qualification affect GPU-system delivery.",
        ),
        "confidence": "high",
    },
    "ASML": {
        "theme": ("英伟达相关", "NVIDIA-related"),
        "score": 4,
        "role": ("间接上游核心设备", "Indirect upstream core equipment"),
        "rationale": (
            "光刻设备不直接供应 NVIDIA，但它决定先进制程扩产节奏，是 AI 芯片制造链的高稀缺设备环节。",
            "Lithography tools do not supply NVIDIA directly, but they determine leading-node expansion cadence and are a scarce equipment layer in AI chip manufacturing.",
        ),
        "confidence": "high",
    },
    "AMAT": {
        "theme": ("英伟达相关", "NVIDIA-related"),
        "score": 4,
        "role": ("上游制程设备", "Upstream process equipment"),
        "rationale": (
            "沉积、刻蚀和材料工程设备通过先进逻辑、存储和封装扩产间接传导 AI 需求。",
            "Deposition, etch, and materials-engineering tools transmit AI demand indirectly through advanced logic, memory, and packaging expansion.",
        ),
        "confidence": "medium",
    },
    "LRCX": {
        "theme": ("英伟达相关", "NVIDIA-related"),
        "score": 4,
        "role": ("上游刻蚀与沉积设备", "Upstream etch and deposition equipment"),
        "rationale": (
            "刻蚀、沉积和清洗设备支撑先进逻辑与 HBM 产能，处于 AI 芯片供给链的上游扩产环节。",
            "Etch, deposition, and clean tools support advanced logic and HBM capacity, placing it in the upstream expansion layer of AI chip supply.",
        ),
        "confidence": "medium",
    },
    "KLAC": {
        "theme": ("英伟达相关", "NVIDIA-related"),
        "score": 4,
        "role": ("先进制程良率控制", "Advanced-node yield control"),
        "rationale": (
            "检测量测和制程控制影响先进芯片良率，属于 AI 加速器制造链中的间接但关键设备环节。",
            "Inspection, metrology, and process control affect advanced-chip yield, making it an indirect but important equipment layer for AI accelerators.",
        ),
        "confidence": "medium",
    },
    "AMKR": {
        "theme": ("英伟达相关", "NVIDIA-related"),
        "score": 4,
        "role": ("先进封装测试能力", "Advanced packaging and test capacity"),
        "rationale": (
            "AI 加速器复杂度提升会放大封装、基板和测试产能的重要性，但具体项目敞口仍需继续拆解。",
            "Rising AI accelerator complexity increases the importance of packaging, substrates, and test capacity, though project-level exposure needs further review.",
        ),
        "confidence": "medium",
    },
    "SMCI": {
        "theme": ("英伟达相关", "NVIDIA-related"),
        "score": 4,
        "role": ("直接 AI 服务器系统集成", "Direct AI server system integration"),
        "rationale": (
            "把 NVIDIA GPU、网络和软件平台集成进 AI 服务器与机柜级系统，相关性比普通终端客户更直接。",
            "It integrates NVIDIA GPUs, networking, and software into AI servers and rack-scale systems, making the linkage more direct than ordinary end customers.",
        ),
        "confidence": "high",
    },
    "DELL": {
        "theme": ("英伟达相关", "NVIDIA-related"),
        "score": 4,
        "role": ("企业 AI 服务器 OEM", "Enterprise AI server OEM"),
        "rationale": (
            "AI 服务器产品组合直接承接 NVIDIA GPU 平台需求，但仍受企业项目节奏和整机毛利约束。",
            "Its AI server portfolio directly carries NVIDIA GPU platform demand, while still depending on enterprise project timing and system margins.",
        ),
        "confidence": "medium",
    },
    "HPE": {
        "theme": ("英伟达相关", "NVIDIA-related"),
        "score": 4,
        "role": ("企业 AI/HPC 系统集成", "Enterprise AI/HPC system integration"),
        "rationale": (
            "通过 AI/HPC 服务器和企业系统承接 NVIDIA 平台需求，传导路径直接但项目化特征较强。",
            "It carries NVIDIA platform demand through AI/HPC servers and enterprise systems, with a direct but project-driven transmission path.",
        ),
        "confidence": "medium",
    },
    "CRWV": {
        "theme": ("英伟达相关", "NVIDIA-related"),
        "score": 4,
        "role": ("GPU 云直接依赖方", "Direct GPU-cloud dependency"),
        "rationale": (
            "业务能力高度依赖 NVIDIA GPU 采购、部署和融资，虽属于下游云客户，但关系密切度高于普通采购方。",
            "Its service capacity depends heavily on NVIDIA GPU procurement, deployment, and financing, so it is tighter than a normal downstream buyer.",
        ),
        "confidence": "high",
    },
    "MSFT": {
        "theme": ("英伟达相关", "NVIDIA-related"),
        "score": 3,
        "role": ("大型下游云客户", "Large downstream cloud customer"),
        "rationale": (
            "Azure 采购和消耗 GPU 算力，但传导链条位于需求端，关系密切度低于制造和关键供给瓶颈。",
            "Azure purchases and consumes GPU compute, but the transmission is on the demand side and less tight than manufacturing or critical supply bottlenecks.",
        ),
        "confidence": "medium",
    },
    "AMZN": {
        "theme": ("英伟达相关", "NVIDIA-related"),
        "score": 3,
        "role": ("大型下游云客户", "Large downstream cloud customer"),
        "rationale": (
            "AWS GPU 云需求会影响 NVIDIA 出货，但自研加速器和云业务组合会稀释单一供应商相关性。",
            "AWS GPU-cloud demand affects NVIDIA shipments, while in-house accelerators and cloud mix dilute single-supplier linkage.",
        ),
        "confidence": "medium",
    },
    "GOOGL": {
        "theme": ("英伟达相关", "NVIDIA-related"),
        "score": 3,
        "role": ("云与 AI 平台客户", "Cloud and AI platform customer"),
        "rationale": (
            "Google Cloud 和内部 AI 使用 GPU，但 TPU 自研路径使其与 NVIDIA 的关系低于纯 GPU 依赖型公司。",
            "Google Cloud and internal AI use GPUs, but the in-house TPU path makes the NVIDIA linkage lower than pure GPU-dependent companies.",
        ),
        "confidence": "medium",
    },
    "ORCL": {
        "theme": ("英伟达相关", "NVIDIA-related"),
        "score": 3,
        "role": ("GPU 云基础设施客户", "GPU cloud infrastructure customer"),
        "rationale": (
            "OCI GPU 集群扩张与 NVIDIA 平台相关，但仍属于下游云需求和数据中心资本开支传导。",
            "OCI GPU cluster expansion is linked to NVIDIA platforms, but it remains downstream cloud demand and data-center capex transmission.",
        ),
        "confidence": "medium",
    },
    "SPCX": {
        "theme": ("太空产业链", "Space supply chain"),
        "score": 5,
        "role": ("发射、卫星与商业航天核心平台", "Launch, satellite, and commercial-space core platform"),
        "rationale": (
            "公司直接处于发射服务、卫星互联网和政府航天任务核心位置，是太空主题的锚点。",
            "The company sits directly at the center of launch services, satellite internet, and government space missions, anchoring the space theme.",
        ),
        "confidence": "high",
    },
    "RKLB": {
        "theme": ("太空产业链", "Space supply chain"),
        "score": 4,
        "role": ("发射与航天系统供应", "Launch and space-systems supplier"),
        "rationale": (
            "发射服务和航天系统直接承接商业航天扩张，但规模和平台覆盖弱于主题核心公司。",
            "Launch services and space systems directly carry commercial-space expansion, though scale and platform breadth are below the theme anchor.",
        ),
        "confidence": "medium",
    },
    "ASTS": {
        "theme": ("太空产业链", "Space supply chain"),
        "score": 4,
        "role": ("卫星直连手机网络", "Direct-to-device satellite network"),
        "rationale": (
            "直接处于卫星通信应用层，技术和商业化路径与低轨通信热潮高度相关。",
            "It sits directly in the satellite-communications application layer, with technology and commercialization closely tied to the LEO connectivity theme.",
        ),
        "confidence": "medium",
    },
    "GSAT": {
        "theme": ("太空产业链", "Space supply chain"),
        "score": 3,
        "role": ("卫星通信运营商", "Satellite communications operator"),
        "rationale": (
            "卫星通信资产与终端连接主题相关，但产业链控制力和扩产瓶颈属性低于发射或核心网络平台。",
            "Satellite communications assets link to device connectivity, but supply-chain control and bottleneck attributes are lower than launch or core network platforms.",
        ),
        "confidence": "medium",
    },
    "IRDM": {
        "theme": ("太空产业链", "Space supply chain"),
        "score": 3,
        "role": ("卫星通信运营商", "Satellite communications operator"),
        "rationale": (
            "低轨卫星通信服务与太空应用相关，但更多是运营服务端暴露，不是关键制造瓶颈。",
            "LEO satellite communications services link to space applications, but exposure is more on the operating-services side than a key manufacturing bottleneck.",
        ),
        "confidence": "medium",
    },
    "VSAT": {
        "theme": ("太空产业链", "Space supply chain"),
        "score": 3,
        "role": ("卫星宽带与国防通信", "Satellite broadband and defense communications"),
        "rationale": (
            "业务与卫星宽带和国防通信相关，属于应用和网络运营端的中等相关性。",
            "The business is tied to satellite broadband and defense communications, giving it moderate application and network-operations relevance.",
        ),
        "confidence": "medium",
    },
    "688146": {
        "theme": ("半导体材料", "Semiconductor materials"),
        "score": 4,
        "role": ("电子特气关键材料供应商", "Critical electronic-specialty-gas supplier"),
        "rationale": (
            "电子特气和含氟材料直接进入半导体制造流程，产业扩产时通常比普通下游应用更靠近供给约束。",
            "Electronic specialty gases and fluorine-containing materials enter semiconductor manufacturing directly, so they sit closer to supply constraints than ordinary downstream applications during expansion cycles.",
        ),
        "confidence": "medium",
    },
    "INTC": {
        "theme": ("半导体制造与算力", "Semiconductor manufacturing and compute"),
        "score": 4,
        "role": ("CPU 与晶圆代工平台", "CPU and foundry platform"),
        "rationale": (
            "公司同时处于计算芯片和制造产能端，相关性强于单纯下游采购方，但其 AI GPU 生态不是当前最核心瓶颈。",
            "The company spans compute chips and manufacturing capacity, stronger than a pure downstream buyer, though its AI GPU ecosystem is not the current central bottleneck.",
        ),
        "confidence": "medium",
    },
    "AAPL": {
        "theme": ("消费电子与 AI 终端", "Consumer electronics and AI endpoints"),
        "score": 3,
        "role": ("终端生态锚点", "Endpoint ecosystem anchor"),
        "rationale": (
            "公司通过终端硬件、芯片设计和服务生态影响上游需求，但在半导体热潮中通常不如关键制造和材料环节紧密。",
            "The company affects upstream demand through devices, chip design, and services, but in a semiconductor boom it is usually less tightly linked than critical manufacturing and materials layers.",
        ),
        "confidence": "medium",
    },
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def contains_any(text: str, needles: list[str]) -> bool:
    lowered = text.lower()
    return any(needle.lower() in lowered for needle in needles)


def score_label(score: int) -> tuple[str, str]:
    return SCORE_LABELS.get(score, SCORE_LABELS[1])


def make_strength(
    score: int,
    direction: str,
    rationale_zh: str,
    rationale_en: str,
    *,
    confidence: str = "medium",
    label: tuple[str, str] | None = None,
) -> dict[str, Any]:
    label_zh, label_en = label or score_label(score)
    return {
        "score": score,
        "label": label_zh,
        "labelZh": label_zh,
        "labelEn": label_en,
        "direction": direction,
        "rationale": rationale_zh,
        "rationaleZh": rationale_zh,
        "rationaleEn": rationale_en,
        "confidence": confidence,
    }


def make_theme_exposure(report: dict[str, Any]) -> list[dict[str, Any]]:
    ticker = str(report.get("ticker", "")).upper()
    payload = THEME_EXPOSURE_BY_TICKER.get(ticker)
    if payload is None:
        labels = report.get("labels", [])
        if "半导体" in labels:
            payload = {
                "theme": ("半导体产业链", "Semiconductor supply chain"),
                "score": 3,
                "role": ("产业链相关公司", "Supply-chain related company"),
                "rationale": (
                    "公司处于半导体产业链相关环节，但尚未单独标记为核心瓶颈或直接供应方。",
                    "The company sits in a semiconductor-related layer but is not yet separately marked as a core bottleneck or direct supplier.",
                ),
                "confidence": "medium",
            }
        elif "太空" in labels:
            payload = {
                "theme": ("太空产业链", "Space supply chain"),
                "score": 3,
                "role": ("主题相关公司", "Theme-related company"),
                "rationale": (
                    "公司与太空产业链相关，但具体瓶颈属性和客户暴露仍需继续拆解。",
                    "The company is related to the space supply chain, while bottleneck attributes and customer exposure need further review.",
                ),
                "confidence": "medium",
            }
        else:
            payload = {
                "theme": ("公开公司主题", "Public-company theme"),
                "score": 2,
                "role": ("主题观察对象", "Theme watch item"),
                "rationale": (
                    "公司已收录为公开公司研究对象，关系强度需要随供应链资料继续细化。",
                    "The company is included as a public-company research target; relationship strength should be refined as supply-chain evidence improves.",
                ),
                "confidence": "low",
            }

    theme_zh, theme_en = payload["theme"]
    role_zh, role_en = payload["role"]
    rationale_zh, rationale_en = payload["rationale"]
    return [
        {
            "theme": theme_zh,
            "themeZh": theme_zh,
            "themeEn": theme_en,
            "score": payload["score"],
            "role": role_zh,
            "roleZh": role_zh,
            "roleEn": role_en,
            "rationale": rationale_zh,
            "rationaleZh": rationale_zh,
            "rationaleEn": rationale_en,
            "confidence": payload.get("confidence", "medium"),
        }
    ]


def entity_text(entity: dict[str, Any], tier: dict[str, Any] | None = None, report: dict[str, Any] | None = None) -> str:
    fields: list[Any] = [
        entity.get("name", ""),
        entity.get("nameZh", ""),
        entity.get("nameEn", ""),
        entity.get("relationship", ""),
        entity.get("relationshipZh", ""),
        entity.get("relationshipEn", ""),
        entity.get("customerRole", ""),
        entity.get("customerRoleZh", ""),
        entity.get("customerRoleEn", ""),
        " ".join(entity.get("productsServices", []) or []),
        " ".join(entity.get("productsServicesZh", []) or []),
        " ".join(entity.get("productsServicesEn", []) or []),
    ]
    if tier:
        fields.extend(
            [
                tier.get("title", ""),
                tier.get("titleZh", ""),
                tier.get("titleEn", ""),
                tier.get("notes", ""),
                " ".join(tier.get("materials", []) or []),
                " ".join(tier.get("materialsZh", []) or []),
                " ".join(tier.get("materialsEn", []) or []),
            ]
        )
    if report:
        fields.extend([report.get("ticker", ""), report.get("sector", "")])
    return " ".join(str(value) for value in fields if value)


def listing_ticker(entity: dict[str, Any]) -> str:
    listing = entity.get("listing", {})
    return str(listing.get("ticker") or listing.get("parentTicker") or "").upper()


def supplier_strength(report: dict[str, Any], tier: dict[str, Any], entity: dict[str, Any]) -> dict[str, Any]:
    text = entity_text(entity, tier, report)
    report_ticker = str(report.get("ticker", "")).upper()
    ticker = listing_ticker(entity)
    level = tier.get("level")

    if level == 0 or ticker == report_ticker:
        return make_strength(
            5,
            "target",
            "目标公司本身，是本页产业链分析的参照对象。",
            "The target company itself, used as the reference point for this supply-chain analysis.",
            confidence="high",
            label=("目标公司", "Target company"),
        )

    if contains_any(text, ["原材料", "raw material", "硅晶圆", "specialty gas", "特种气体", "高纯", "矿", "化学品"]):
        return make_strength(
            5,
            "upstream-raw-material",
            "处于原材料或高纯材料层，产业扩产时通常最先形成供给、认证或价格约束。",
            "Sits in the raw-material or high-purity material layer, where expansion cycles often first create supply, qualification, or pricing constraints.",
        )

    if contains_any(text, ["hbm", "dram", "nand", "memory", "存储", "cowos", "advanced packaging", "先进封装", "晶圆代工", "foundry", "wafer manufacturing"]):
        return make_strength(
            5,
            "upstream-manufacturing",
            "直接进入关键制造、存储或封装环节，对产能、良率和交付节奏有较强约束。",
            "Directly enters critical manufacturing, memory, or packaging layers, strongly affecting capacity, yield, and delivery cadence.",
            confidence="high" if contains_any(text, ["hbm", "cowos", "晶圆代工", "foundry"]) else "medium",
        )

    if contains_any(text, ["euv", "duv", "lithography", "光刻"]):
        return make_strength(
            5,
            "upstream-equipment",
            "光刻设备是先进制程扩产的稀缺设备层，虽间接但瓶颈属性强。",
            "Lithography tools are a scarce equipment layer for leading-node expansion; the link is indirect but has strong bottleneck attributes.",
            confidence="high",
        )

    if contains_any(text, ["equipment", "设备", "etch", "刻蚀", "deposition", "沉积", "metrology", "量测", "inspection", "检测", "process control"]):
        return make_strength(
            4,
            "upstream-equipment",
            "处于制程设备或检测量测层，需求通过晶圆厂、存储厂和封装产线扩产传导。",
            "Sits in process equipment or metrology/inspection, with demand transmitted through foundry, memory, and packaging line expansion.",
        )

    if "NVIDIA" in text or "英伟达" in text:
        score = 5 if report_ticker == "CRWV" else 4
        return make_strength(
            score,
            "direct-supplier",
            "NVIDIA 平台是该公司 AI 服务器或 GPU 云能力的关键投入，供给变化会直接影响交付。",
            "NVIDIA platforms are a key input for this company's AI server or GPU-cloud capacity, so supply changes directly affect delivery.",
            confidence="high" if score == 5 else "medium",
        )

    if contains_any(text, ["server", "服务器", "rack", "整机", "oem", "system", "系统集成", "液冷"]):
        return make_strength(
            4,
            "system-integration",
            "把关键芯片、网络、散热和整机方案转化为可交付系统，相关性强但通常低于制造瓶颈。",
            "Converts chips, networking, cooling, and system design into deliverable systems; strong relevance but usually below manufacturing bottlenecks.",
        )

    return make_strength(
        3,
        "upstream-component",
        "处于供应链上游或配套服务层，对交付和成本有影响，但短期瓶颈属性需继续核实。",
        "Sits in an upstream or supporting-service layer and can affect delivery and cost, but near-term bottleneck attributes need further verification.",
    )


def downstream_strength(report: dict[str, Any], tier: dict[str, Any], entity: dict[str, Any]) -> dict[str, Any]:
    text = entity_text(entity, tier, report)
    report_ticker = str(report.get("ticker", "")).upper()
    ticker = listing_ticker(entity)

    if contains_any(text, ["enterprise and ai customers", "企业与 ai 客户", "终端客户", "end customer", "compute user"]):
        return make_strength(
            2,
            "downstream-customer",
            "终端客户代表需求去向，但通常不直接决定上游产能瓶颈。",
            "End customers indicate demand direction but usually do not directly determine upstream capacity bottlenecks.",
        )

    if ticker == "CRWV":
        return make_strength(
            4,
            "downstream-customer",
            "该 GPU 云客户对 NVIDIA GPU 供给依赖度高，虽在下游但关系紧密。",
            "This GPU-cloud customer is highly dependent on NVIDIA GPU supply, making the downstream link unusually tight.",
            confidence="high",
        )

    if ticker in {"MSFT", "AMZN", "GOOGL", "ORCL", "META", "TSLA"} or contains_any(text, ["cloud", "hyperscaler", "云客户", "azure", "aws", "google cloud", "oci"]):
        return make_strength(
            3,
            "downstream-customer",
            "大型云或平台客户会影响需求预期，但传导链条位于采购和应用端，弱于供给瓶颈。",
            "Large cloud or platform customers affect demand expectations, but the transmission sits on the purchasing and application side and is weaker than supply bottlenecks.",
        )

    if "NVIDIA" in text or "英伟达" in text or ticker == "NVDA":
        if report_ticker in {"TSM", "MU"}:
            return make_strength(
                5,
                "downstream-customer",
                "NVIDIA 需求直接拉动关键制造或存储产能，是比普通终端客户更紧密的需求来源。",
                "NVIDIA demand directly pulls critical manufacturing or memory capacity, making it a tighter demand source than an ordinary end customer.",
                confidence="high",
            )
        if report_ticker in {"AMKR"}:
            return make_strength(
                4,
                "indirect-demand",
                "AI 加速器复杂度提升会推高封装和测试需求，但直接项目敞口仍需继续确认。",
                "Rising AI-accelerator complexity increases packaging and test demand, though direct project exposure still needs confirmation.",
            )
        return make_strength(
            3,
            "indirect-demand",
            "NVIDIA 需求通过晶圆厂、存储厂或封装投资间接传导，不等同于直接采购关系。",
            "NVIDIA demand transmits indirectly through foundry, memory, or packaging investment and is not the same as a direct purchasing relationship.",
        )

    if contains_any(text, ["政府", "government", "电信", "telecom", "operator", "运营商", "carrier", "国防"]):
        return make_strength(
            3,
            "downstream-customer",
            "应用或运营客户能影响订单和收入可见度，但与核心供给瓶颈相比传导更长。",
            "Application or operator customers can affect orders and revenue visibility, but the transmission is longer than core supply bottlenecks.",
        )

    return make_strength(
        2,
        "downstream-customer",
        "下游需求关系有助于判断应用去向，但相关性通常弱于上游关键供给和制造瓶颈。",
        "The downstream demand relationship helps identify application direction, but it is usually weaker than upstream critical supply and manufacturing bottlenecks.",
    )


def apply_strength(report: dict[str, Any]) -> None:
    report["themeExposure"] = make_theme_exposure(report)

    for tier in report.get("supplyChain", {}).get("tiers", []):
        for entity in tier.get("entities", []) or []:
            entity["relationshipStrength"] = supplier_strength(report, tier, entity)

    downstream = report.get("supplyChain", {}).get("downstream")
    if isinstance(downstream, dict):
        for tier in downstream.get("tiers", []) or []:
            for entity in tier.get("entities", []) or []:
                entity["relationshipStrength"] = downstream_strength(report, tier, entity)


def main() -> None:
    paths = sorted(COMPANIES_DIR.glob("*.json"))
    for path in paths:
        report = read_json(path)
        apply_strength(report)
        write_json(path, report)
        print(f"Updated {path.relative_to(ROOT)}")
    print(f"Applied relationship strength to {len(paths)} company reports")


if __name__ == "__main__":
    main()
