#!/usr/bin/env python3
"""Add curated downstream customer and go-to-market data to company reports."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPANIES_DIR = ROOT / "public" / "data" / "companies"
ACCESSED_AT = "2026-06-08"


def listed(ticker: str, exchange: str, stock_url: str, market: str = "US") -> dict:
    return {
        "status": "listed",
        "ticker": ticker,
        "exchange": exchange,
        "market": market,
        "stockUrl": stock_url,
    }


def unknown(note_zh: str, note_en: str) -> dict:
    return {
        "status": "unknown",
        "note": note_zh,
        "noteZh": note_zh,
        "noteEn": note_en,
    }


def entity(
    name: str,
    role: str,
    role_zh: str,
    relationship: str,
    relationship_zh: str,
    products: list[str],
    products_zh: list[str],
    listing: dict,
    source_ids: list[str],
    company_url: str | None = None,
    confidence: str = "medium",
) -> dict:
    item = {
        "name": name,
        "customerRole": role,
        "customerRoleZh": role_zh,
        "customerRoleEn": role,
        "relationship": relationship,
        "relationshipZh": relationship_zh,
        "relationshipEn": relationship,
        "productsServices": products,
        "productsServicesZh": products_zh,
        "productsServicesEn": products,
        "listing": listing,
        "confidence": confidence,
        "sourceIds": source_ids,
    }
    if company_url:
        item["companyUrl"] = company_url
    return item


def tier(
    level: int,
    title: str,
    title_zh: str,
    notes: str,
    notes_zh: str,
    entities: list[dict],
    source_ids: list[str],
    confidence: str = "medium",
) -> dict:
    return {
        "level": level,
        "title": title,
        "titleZh": title_zh,
        "titleEn": title,
        "entities": entities,
        "notes": notes,
        "notesZh": notes_zh,
        "notesEn": notes,
        "confidence": confidence,
        "sourceIds": source_ids,
    }


def source(source_id: str, title: str, title_zh: str, publisher: str, url: str, published_at: str | None = None) -> dict:
    item = {
        "id": source_id,
        "title": title,
        "titleZh": title_zh,
        "titleEn": title,
        "publisher": publisher,
        "url": url,
        "accessedAt": ACCESSED_AT,
        "type": "company",
    }
    if published_at:
        item["publishedAt"] = published_at
    return item


DOWNSTREAM = {
    "aapl": {
        "sources": [
            source(
                "aapl-enterprise",
                "Apple Enterprise - hardware, software, and services",
                "Apple 企业市场：硬件、软件与服务",
                "Apple",
                "https://www.apple.com/business/enterprise/",
            )
        ],
        "downstream": {
            "updatedAt": "2026-06-08",
            "thesis": "Apple is mostly the downstream demand owner rather than a midstream component supplier: its demand chain runs through direct sales, carriers/resellers, enterprise deployment partners, and the App Store/services ecosystem.",
            "thesisZh": "Apple 更接近供应链终端需求方，而不是典型中游零部件供应商：其下游去向主要是直营、运营商/经销商、企业部署伙伴以及 App Store/服务生态。",
            "thesisEn": "Apple is mostly the downstream demand owner rather than a midstream component supplier: its demand chain runs through direct sales, carriers/resellers, enterprise deployment partners, and the App Store/services ecosystem.",
            "tiers": [
                tier(
                    1,
                    "Distribution channels and end markets",
                    "销售渠道与终端市场",
                    "Apple discloses direct and indirect distribution channels; indirect channels include cellular carriers and resellers.",
                    "Apple 披露直营和间接渠道；间接渠道包括蜂窝网络运营商和经销商。",
                    [
                        entity(
                            "Direct retail, online store and direct sales force",
                            "Direct channel",
                            "直营渠道",
                            "Apple sells products and some services directly to end customers through its stores, online store and direct sales force.",
                            "Apple 通过 Apple Store、在线商店和直销团队直接向终端客户销售产品及部分服务。",
                            ["iPhone, Mac, iPad, wearables and services"],
                            ["iPhone、Mac、iPad、可穿戴设备与服务"],
                            listed("AAPL", "NASDAQ", "https://www.nasdaq.com/market-activity/stocks/aapl"),
                            ["aapl-10k-2025"],
                            "https://www.apple.com/store",
                            "high",
                        ),
                        entity(
                            "Cellular carriers and resellers",
                            "Indirect channel",
                            "间接渠道",
                            "Apple's 10-K identifies third-party cellular network carriers and other resellers as indirect distribution channels for products and certain services.",
                            "Apple 10-K 将第三方蜂窝网络运营商和其他经销商列为产品及部分服务的间接分销渠道。",
                            ["device distribution", "service distribution"],
                            ["设备分销", "服务分销"],
                            unknown("该条是渠道类别，不对应单一上市公司。", "This row is a channel category rather than one listed company."),
                            ["aapl-10k-2025"],
                            confidence="high",
                        ),
                    ],
                    ["aapl-10k-2025"],
                    "high",
                ),
                tier(
                    2,
                    "Enterprise platform partners",
                    "企业平台伙伴",
                    "These are ecosystem and route-to-market partners rather than simple purchase customers; they help take Apple devices, OS frameworks and services into enterprise workflows.",
                    "这些更接近生态与商业落地伙伴，而不是简单采购客户；它们帮助 Apple 设备、系统框架和服务进入企业工作流。",
                    [
                        entity(
                            "IBM",
                            "Enterprise solution partner",
                            "企业解决方案伙伴",
                            "Apple and IBM teams work together on enterprise clients and workflows; Apple supplies the device, OS and service layer while IBM contributes industry solutions and deployment services.",
                            "Apple 与 IBM 团队共同服务企业客户和工作流；Apple 提供设备、操作系统和服务层，IBM 提供行业解决方案与部署服务。",
                            ["iPhone and iPad enterprise platform", "Apple services support"],
                            ["iPhone 与 iPad 企业平台", "Apple 服务支持"],
                            listed("IBM", "NYSE", "https://www.nyse.com/quote/XNYS:IBM"),
                            ["aapl-enterprise"],
                            "https://www.ibm.com/",
                        ),
                        entity(
                            "Accenture",
                            "Enterprise transformation partner",
                            "企业转型伙伴",
                            "Accenture combines digital transformation services with Apple products to help enterprise clients improve customer experience and productivity.",
                            "Accenture 将数字化转型服务与 Apple 产品结合，帮助企业客户改善客户体验和生产力。",
                            ["Apple hardware in enterprise workflows", "mobility and app transformation"],
                            ["企业工作流中的 Apple 硬件", "移动化与应用转型"],
                            listed("ACN", "NYSE", "https://www.nyse.com/quote/XNYS:ACN"),
                            ["aapl-enterprise"],
                            "https://www.accenture.com/",
                        ),
                        entity(
                            "Salesforce",
                            "Enterprise app ecosystem partner",
                            "企业应用生态伙伴",
                            "Salesforce and Apple position iOS and Apple devices as part of CRM and customer-engagement workflows for business users.",
                            "Salesforce 与 Apple 将 iOS 和 Apple 设备嵌入 CRM 与客户互动工作流，面向企业用户落地。",
                            ["iOS enterprise app workflows", "Apple device integration"],
                            ["iOS 企业应用工作流", "Apple 设备集成"],
                            listed("CRM", "NYSE", "https://www.nyse.com/quote/XNYS:CRM"),
                            ["aapl-enterprise"],
                            "https://www.salesforce.com/",
                        ),
                    ],
                    ["aapl-enterprise"],
                ),
            ],
        },
    },
    "nvda": {
        "sources": [
            source(
                "nvda-blackwell-ultra-2025",
                "NVIDIA Blackwell Ultra AI Factory Platform Paves Way for Age of AI Reasoning",
                "NVIDIA Blackwell Ultra AI 工厂平台发布",
                "NVIDIA Investor Relations",
                "https://investor.nvidia.com/news/press-release-details/2025/NVIDIA-Blackwell-Ultra-AI-Factory-Platform-Paves-Way-for-Age-of-AI-Reasoning/default.aspx",
                "2025-03-18",
            ),
            source(
                "nvda-rtx-pro-systems-2025",
                "NVIDIA RTX PRO Servers With Blackwell Coming to World's Most Popular Enterprise Systems",
                "NVIDIA RTX PRO Blackwell 服务器进入主流企业系统",
                "NVIDIA Investor Relations",
                "https://investor.nvidia.com/news/press-release-details/2025/NVIDIA-RTX-PRO-Servers-With-Blackwell-Coming-to-Worlds-Most-Popular-Enterprise-Systems/",
                "2025-08-11",
            ),
        ],
        "downstream": {
            "updatedAt": "2026-06-08",
            "thesis": "NVIDIA sits in the middle of the AI infrastructure chain: upstream fabs, HBM and packaging constrain supply, while downstream cloud providers, GPU clouds and system OEMs convert NVIDIA platforms into rentable compute or deployable AI factories.",
            "thesisZh": "NVIDIA 处在 AI 基础设施供应链中游：上游受代工、HBM 与先进封装约束；下游由云厂商、GPU 云和系统 OEM 将 NVIDIA 平台转化为可租用算力或可部署 AI 工厂。",
            "thesisEn": "NVIDIA sits in the middle of the AI infrastructure chain: upstream fabs, HBM and packaging constrain supply, while downstream cloud providers, GPU clouds and system OEMs convert NVIDIA platforms into rentable compute or deployable AI factories.",
            "tiers": [
                tier(
                    1,
                    "Cloud and GPU-cloud customers",
                    "云与 GPU 云客户",
                    "Cloud providers buy or deploy NVIDIA GPUs, networking and software stacks, then expose them as AI infrastructure services to model developers and enterprises.",
                    "云厂商采购或部署 NVIDIA GPU、网络和软件栈，再将其作为 AI 基础设施服务提供给模型开发者和企业。",
                    [
                        entity(
                            "Microsoft",
                            "Cloud infrastructure customer",
                            "云基础设施客户",
                            "Microsoft Azure is cited among cloud providers offering NVIDIA Blackwell Ultra-powered infrastructure and using NVIDIA platforms for large-scale AI clusters.",
                            "Microsoft Azure 被 NVIDIA 列为提供 Blackwell Ultra 算力基础设施的云厂商之一，并使用 NVIDIA 平台建设大规模 AI 集群。",
                            ["Blackwell GPUs", "GB200/GB300 NVL systems", "NVIDIA networking and AI software"],
                            ["Blackwell GPU", "GB200/GB300 NVL 系统", "NVIDIA 网络与 AI 软件"],
                            listed("MSFT", "NASDAQ", "https://www.nasdaq.com/market-activity/stocks/msft"),
                            ["nvda-blackwell-ultra-2025"],
                            "https://azure.microsoft.com/",
                            "high",
                        ),
                        entity(
                            "Amazon Web Services",
                            "Cloud infrastructure customer",
                            "云基础设施客户",
                            "AWS is listed by NVIDIA among cloud service providers expected to offer Blackwell Ultra-powered instances.",
                            "AWS 被 NVIDIA 列为预计提供 Blackwell Ultra 实例的云服务商之一。",
                            ["Blackwell Ultra instances", "GPU cloud infrastructure"],
                            ["Blackwell Ultra 实例", "GPU 云基础设施"],
                            listed("AMZN", "NASDAQ", "https://www.nasdaq.com/market-activity/stocks/amzn"),
                            ["nvda-blackwell-ultra-2025"],
                            "https://aws.amazon.com/",
                            "high",
                        ),
                        entity(
                            "Alphabet / Google Cloud",
                            "Cloud infrastructure customer",
                            "云基础设施客户",
                            "Google Cloud is listed by NVIDIA among cloud service providers expected to offer Blackwell Ultra-powered instances.",
                            "Google Cloud 被 NVIDIA 列为预计提供 Blackwell Ultra 实例的云服务商之一。",
                            ["Blackwell Ultra instances", "GPU cloud infrastructure"],
                            ["Blackwell Ultra 实例", "GPU 云基础设施"],
                            listed("GOOGL", "NASDAQ", "https://www.nasdaq.com/market-activity/stocks/googl"),
                            ["nvda-blackwell-ultra-2025"],
                            "https://cloud.google.com/",
                            "high",
                        ),
                        entity(
                            "Oracle Cloud Infrastructure",
                            "Cloud infrastructure customer",
                            "云基础设施客户",
                            "Oracle Cloud Infrastructure is listed by NVIDIA among cloud service providers expected to offer Blackwell Ultra-powered instances.",
                            "Oracle Cloud Infrastructure 被 NVIDIA 列为预计提供 Blackwell Ultra 实例的云服务商之一。",
                            ["Blackwell Ultra instances", "GPU cloud infrastructure"],
                            ["Blackwell Ultra 实例", "GPU 云基础设施"],
                            listed("ORCL", "NYSE", "https://www.nyse.com/quote/XNYS:ORCL"),
                            ["nvda-blackwell-ultra-2025"],
                            "https://www.oracle.com/cloud/",
                            "high",
                        ),
                        entity(
                            "CoreWeave",
                            "GPU cloud customer",
                            "GPU 云客户",
                            "CoreWeave is listed by NVIDIA among GPU cloud providers expected to offer Blackwell Ultra-powered instances.",
                            "CoreWeave 被 NVIDIA 列为预计提供 Blackwell Ultra 实例的 GPU 云服务商之一。",
                            ["GB200/GB300 systems", "GPU cloud infrastructure"],
                            ["GB200/GB300 系统", "GPU 云基础设施"],
                            listed("CRWV", "NASDAQ", "https://www.nasdaq.com/market-activity/stocks/crwv"),
                            ["nvda-blackwell-ultra-2025"],
                            "https://www.coreweave.com/",
                            "high",
                        ),
                    ],
                    ["nvda-blackwell-ultra-2025"],
                    "high",
                ),
                tier(
                    2,
                    "Enterprise system OEMs",
                    "企业系统 OEM",
                    "System OEMs integrate NVIDIA GPUs, networking and software into servers, workstations and AI-factory systems for enterprise and cloud buyers.",
                    "系统 OEM 将 NVIDIA GPU、网络和软件集成进服务器、工作站和 AI 工厂系统，再销售给企业和云客户。",
                    [
                        entity(
                            "Dell Technologies",
                            "System OEM / route-to-market partner",
                            "系统 OEM / 商业落地伙伴",
                            "Dell is one of the system partners NVIDIA lists for RTX PRO and Blackwell server platforms.",
                            "Dell 是 NVIDIA 列出的 RTX PRO 与 Blackwell 服务器平台系统伙伴之一。",
                            ["RTX PRO 6000 Blackwell servers", "AI factory systems"],
                            ["RTX PRO 6000 Blackwell 服务器", "AI 工厂系统"],
                            listed("DELL", "NYSE", "https://www.nyse.com/quote/XNYS:DELL"),
                            ["nvda-rtx-pro-systems-2025"],
                            "https://www.dell.com/",
                            "high",
                        ),
                        entity(
                            "Hewlett Packard Enterprise",
                            "System OEM / route-to-market partner",
                            "系统 OEM / 商业落地伙伴",
                            "HPE is one of the system partners NVIDIA lists for RTX PRO and Blackwell server platforms.",
                            "HPE 是 NVIDIA 列出的 RTX PRO 与 Blackwell 服务器平台系统伙伴之一。",
                            ["RTX PRO 6000 Blackwell servers", "AI factory systems"],
                            ["RTX PRO 6000 Blackwell 服务器", "AI 工厂系统"],
                            listed("HPE", "NYSE", "https://www.nyse.com/quote/XNYS:HPE"),
                            ["nvda-rtx-pro-systems-2025"],
                            "https://www.hpe.com/",
                            "high",
                        ),
                        entity(
                            "Lenovo",
                            "System OEM / route-to-market partner",
                            "系统 OEM / 商业落地伙伴",
                            "Lenovo is one of the system partners NVIDIA lists for RTX PRO and Blackwell server platforms.",
                            "Lenovo 是 NVIDIA 列出的 RTX PRO 与 Blackwell 服务器平台系统伙伴之一。",
                            ["RTX PRO 6000 Blackwell servers", "AI factory systems"],
                            ["RTX PRO 6000 Blackwell 服务器", "AI 工厂系统"],
                            listed("0992", "HKEX", "https://www.hkex.com.hk/Market-Data/Securities-Prices/Equities/Equities-Quote?sym=992&sc_lang=en", "HK"),
                            ["nvda-rtx-pro-systems-2025"],
                            "https://www.lenovo.com/",
                            "high",
                        ),
                        entity(
                            "Super Micro Computer",
                            "System OEM / route-to-market partner",
                            "系统 OEM / 商业落地伙伴",
                            "Supermicro is one of the system partners NVIDIA lists for RTX PRO and Blackwell server platforms.",
                            "Supermicro 是 NVIDIA 列出的 RTX PRO 与 Blackwell 服务器平台系统伙伴之一。",
                            ["RTX PRO 6000 Blackwell servers", "AI factory systems"],
                            ["RTX PRO 6000 Blackwell 服务器", "AI 工厂系统"],
                            listed("SMCI", "NASDAQ", "https://www.nasdaq.com/market-activity/stocks/smci"),
                            ["nvda-rtx-pro-systems-2025"],
                            "https://www.supermicro.com/",
                            "high",
                        ),
                    ],
                    ["nvda-rtx-pro-systems-2025"],
                    "high",
                ),
            ],
        },
    },
    "intc": {
        "sources": [
            source(
                "intc-vpro-oem-2024",
                "Intel Core Ultra Extends AI PCs to the Enterprise with New Intel vPro Platform",
                "Intel Core Ultra 与 vPro 平台进入企业 AI PC",
                "Intel Newsroom",
                "https://newsroom.intel.com/client-computing/mwc-2024-core-ultra-ai-pc-enterprise-vpro",
                "2024-02-27",
            ),
            source(
                "intc-xeon6-partner-2025",
                "Customers and Ecosystem Partners Showcase Support for Intel Xeon 6 with Performance-cores",
                "客户与生态伙伴支持 Intel Xeon 6 P-core",
                "Intel Newsroom",
                "https://download.intel.com/newsroom/2025/3jdc8gkA5/xeon-6-customer-partner-quote-sheet.pdf",
                "2025-04-08",
            ),
            source(
                "intc-foundry-microsoft-2024",
                "Intel Launches World's First Systems Foundry Designed for the AI Era",
                "Intel 推出面向 AI 时代的系统级晶圆代工",
                "Intel Newsroom",
                "https://newsroom.intel.com/intel-foundry/foundry-news-roadmaps-updates",
                "2024-02-21",
            ),
        ],
        "downstream": {
            "updatedAt": "2026-06-08",
            "thesis": "Intel is a classic midstream semiconductor company: it supplies client CPUs to OEMs, Xeon platforms to server makers and cloud/enterprise infrastructure, and is trying to turn Intel Foundry into a downstream customer-facing manufacturing service.",
            "thesisZh": "Intel 是典型中游半导体公司：向 OEM 提供客户端 CPU，向服务器厂商和云/企业基础设施提供 Xeon 平台，同时试图把 Intel Foundry 打造成面向下游客户的制造服务。",
            "thesisEn": "Intel is a classic midstream semiconductor company: it supplies client CPUs to OEMs, Xeon platforms to server makers and cloud/enterprise infrastructure, and is trying to turn Intel Foundry into a downstream customer-facing manufacturing service.",
            "tiers": [
                tier(
                    1,
                    "PC OEM customers and platform partners",
                    "PC OEM 客户与平台伙伴",
                    "Intel discloses OEM design momentum for AI PCs and vPro; these partners convert Intel CPUs into commercial notebooks, desktops and workstations.",
                    "Intel 披露 AI PC 与 vPro 的 OEM 设计动能；这些伙伴把 Intel CPU 转化为商用笔记本、台式机和工作站。",
                    [
                        entity(
                            "Dell Technologies",
                            "PC OEM customer",
                            "PC OEM 客户",
                            "Dell commercial PCs are part of Intel's cited vPro and Core Ultra partner ecosystem.",
                            "Dell 商用 PC 属于 Intel 披露的 vPro 与 Core Ultra 伙伴生态。",
                            ["Core Ultra processors", "vPro commercial PC platform"],
                            ["Core Ultra 处理器", "vPro 商用 PC 平台"],
                            listed("DELL", "NYSE", "https://www.nyse.com/quote/XNYS:DELL"),
                            ["intc-vpro-oem-2024"],
                            "https://www.dell.com/",
                            "high",
                        ),
                        entity(
                            "HP Inc.",
                            "PC OEM customer",
                            "PC OEM 客户",
                            "HP commercial PCs are part of Intel's cited vPro and Core Ultra partner ecosystem.",
                            "HP 商用 PC 属于 Intel 披露的 vPro 与 Core Ultra 伙伴生态。",
                            ["Core Ultra processors", "vPro commercial PC platform"],
                            ["Core Ultra 处理器", "vPro 商用 PC 平台"],
                            listed("HPQ", "NYSE", "https://www.nyse.com/quote/XNYS:HPQ"),
                            ["intc-vpro-oem-2024"],
                            "https://www.hp.com/",
                            "high",
                        ),
                        entity(
                            "Lenovo",
                            "PC OEM customer",
                            "PC OEM 客户",
                            "Lenovo commercial PCs are part of Intel's cited vPro and Core Ultra partner ecosystem.",
                            "Lenovo 商用 PC 属于 Intel 披露的 vPro 与 Core Ultra 伙伴生态。",
                            ["Core Ultra processors", "vPro commercial PC platform"],
                            ["Core Ultra 处理器", "vPro 商用 PC 平台"],
                            listed("0992", "HKEX", "https://www.hkex.com.hk/Market-Data/Securities-Prices/Equities/Equities-Quote?sym=992&sc_lang=en", "HK"),
                            ["intc-vpro-oem-2024"],
                            "https://www.lenovo.com/",
                            "high",
                        ),
                        entity(
                            "Microsoft Surface",
                            "PC OEM / device partner",
                            "PC OEM / 设备伙伴",
                            "Microsoft Surface is listed in Intel's commercial Core Ultra/vPro design ecosystem.",
                            "Microsoft Surface 被列入 Intel 商用 Core Ultra/vPro 设计生态。",
                            ["Core Ultra processors", "Surface commercial devices"],
                            ["Core Ultra 处理器", "Surface 商用设备"],
                            listed("MSFT", "NASDAQ", "https://www.nasdaq.com/market-activity/stocks/msft"),
                            ["intc-vpro-oem-2024"],
                            "https://www.microsoft.com/surface",
                            "high",
                        ),
                    ],
                    ["intc-vpro-oem-2024"],
                    "high",
                ),
                tier(
                    2,
                    "Server OEMs and data-center platform customers",
                    "服务器 OEM 与数据中心平台客户",
                    "Server OEMs turn Intel Xeon platforms into enterprise, cloud and telecom infrastructure systems.",
                    "服务器 OEM 将 Intel Xeon 平台转化为企业、云和电信基础设施系统。",
                    [
                        entity(
                            "Dell Technologies",
                            "Server OEM customer",
                            "服务器 OEM 客户",
                            "Dell PowerEdge systems use Intel Xeon platforms across enterprise and cloud infrastructure.",
                            "Dell PowerEdge 系统在企业和云基础设施中使用 Intel Xeon 平台。",
                            ["Xeon 6 processors", "server platform enablement"],
                            ["Xeon 6 处理器", "服务器平台导入"],
                            listed("DELL", "NYSE", "https://www.nyse.com/quote/XNYS:DELL"),
                            ["intc-xeon6-partner-2025"],
                            "https://www.dell.com/",
                            "high",
                        ),
                        entity(
                            "Hewlett Packard Enterprise",
                            "Server OEM customer",
                            "服务器 OEM 客户",
                            "HPE server platforms are part of Intel's Xeon 6 partner ecosystem.",
                            "HPE 服务器平台属于 Intel Xeon 6 伙伴生态。",
                            ["Xeon 6 processors", "server platform enablement"],
                            ["Xeon 6 处理器", "服务器平台导入"],
                            listed("HPE", "NYSE", "https://www.nyse.com/quote/XNYS:HPE"),
                            ["intc-xeon6-partner-2025"],
                            "https://www.hpe.com/",
                            "high",
                        ),
                        entity(
                            "Super Micro Computer",
                            "Server OEM customer",
                            "服务器 OEM 客户",
                            "Supermicro systems use Intel Xeon 6 platforms for enterprise and cloud data-center workloads.",
                            "Supermicro 系统使用 Intel Xeon 6 平台面向企业和云数据中心负载。",
                            ["Xeon 6 processors", "server platform enablement"],
                            ["Xeon 6 处理器", "服务器平台导入"],
                            listed("SMCI", "NASDAQ", "https://www.nasdaq.com/market-activity/stocks/smci"),
                            ["intc-xeon6-partner-2025"],
                            "https://www.supermicro.com/",
                            "high",
                        ),
                    ],
                    ["intc-xeon6-partner-2025"],
                    "high",
                ),
                tier(
                    3,
                    "Foundry customers",
                    "晶圆代工客户",
                    "Intel Foundry is the clearest example of Intel moving from an internal-product company into a supplier for other chip designers.",
                    "Intel Foundry 是 Intel 从内部产品公司转向其他芯片设计公司供应商的最直接例子。",
                    [
                        entity(
                            "Microsoft",
                            "Foundry customer",
                            "晶圆代工客户",
                            "Intel states Microsoft chose a chip design it plans to produce on Intel 18A.",
                            "Intel 披露 Microsoft 选择了一款计划采用 Intel 18A 制程生产的芯片设计。",
                            ["Intel 18A process technology", "foundry manufacturing services"],
                            ["Intel 18A 制程技术", "晶圆代工制造服务"],
                            listed("MSFT", "NASDAQ", "https://www.nasdaq.com/market-activity/stocks/msft"),
                            ["intc-foundry-microsoft-2024"],
                            "https://www.microsoft.com/",
                            "high",
                        )
                    ],
                    ["intc-foundry-microsoft-2024"],
                    "high",
                ),
            ],
        },
    },
}


def upsert_sources(existing: list[dict], additions: list[dict]) -> list[dict]:
    by_id = {item.get("id"): item for item in existing}
    for item in additions:
        by_id[item["id"]] = item
    return list(by_id.values())


def apply_downstream(company_id: str, payload: dict) -> None:
    path = COMPANIES_DIR / f"{company_id}.json"
    report = json.loads(path.read_text(encoding="utf-8"))
    report["sources"] = upsert_sources(report.get("sources", []), payload.get("sources", []))
    report.setdefault("supplyChain", {})
    report["supplyChain"]["downstream"] = payload["downstream"]
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    for company_id, payload in DOWNSTREAM.items():
        apply_downstream(company_id, payload)
    print(f"Applied downstream data to {len(DOWNSTREAM)} companies")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
