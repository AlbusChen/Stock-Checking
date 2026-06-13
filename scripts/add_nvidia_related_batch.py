#!/usr/bin/env python3
"""Create reviewed company JSON files for the NVIDIA-related US-listed batch."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DRAFT_DIR = ROOT / "research" / "drafts"
COMPANIES_DIR = ROOT / "public" / "data" / "companies"

LAST_UPDATED = "2026-06-14T12:00:00+08:00"
ACCESSED_AT = "2026-06-14"
NVDA_10K_URL = "https://www.sec.gov/Archives/edgar/data/1045810/000104581026000021/nvda-20260125.htm"
NVDA_RTX_SYSTEMS_URL = "https://investor.nvidia.com/news/press-release-details/2025/NVIDIA-RTX-PRO-Servers-With-Blackwell-Coming-to-Worlds-Most-Popular-Enterprise-Systems/"

UPDATE_CADENCE = {
    "最新动态": "暂不启用定时；计划启用后每 12 小时",
    "财务与公告": "暂不启用定时；计划启用后每日",
    "主营业务": "暂不启用定时；计划启用后每周",
    "供应链溯源": "暂不启用定时；计划启用后每周",
}

MONEY_UNITS = {"USD", "EUR", "TWD", "CNY"}
METRIC_LABELS = {
    "revenue": ("收入", "revenue"),
    "net_income": ("净利润 / 净亏损", "net income / loss"),
    "assets": ("总资产", "total assets"),
    "cash_from_operations": ("经营现金流", "operating cash flow"),
}

COMPANY_META: dict[str, dict[str, Any]] = {
    "TSM": {
        "id": "tsm",
        "exchange": "NYSE",
        "name": "TSMC / 台积电",
        "homepage": "https://www.tsmc.com/english",
        "sector": "Semiconductors / 半导体",
        "industry": ["Foundry", "Advanced process nodes", "Advanced packaging", "晶圆代工", "先进制程", "先进封装"],
        "labels": ["半导体", "晶圆代工", "先进制程", "先进封装", "AI基础设施", "英伟达相关", "美股"],
        "summaryZh": "台积电是全球领先的纯晶圆代工厂，处于 NVIDIA AI GPU/加速器制造链的核心上游，关键变量包括先进制程、CoWoS/先进封装产能和高端客户资本开支。",
        "summaryEn": "TSMC is a leading pure-play foundry and a core upstream manufacturing node for NVIDIA AI GPUs and accelerators, with advanced nodes, CoWoS packaging capacity, and high-end customer capex as key variables.",
        "descriptionZh": "台积电为全球半导体客户提供晶圆制造、先进制程和先进封装相关服务，主要面向高性能计算、智能手机、汽车和物联网等终端需求。",
        "descriptionEn": "TSMC provides wafer manufacturing, advanced process technology, and advanced packaging services for global semiconductor customers across HPC, smartphones, automotive, and IoT demand.",
        "thesisZh": "与 NVIDIA 的关系主要在制造端：NVIDIA 的 AI 加速器需要先进制程和封装产能，台积电的产能、良率和资本开支直接影响 AI 芯片供给弹性。",
        "thesisEn": "The NVIDIA linkage sits mainly on manufacturing: NVIDIA AI accelerators require leading-edge process and packaging capacity, so TSMC capacity, yield, and capex shape AI chip supply elasticity.",
        "revenueModel": ["晶圆代工 / wafer foundry", "先进封装 / advanced packaging", "工程与光罩服务 / engineering and mask services"],
        "risks": [
            "客户集中与 AI 资本开支周期会影响高端制程利用率。 / Customer concentration and AI capex cycles affect leading-node utilization.",
            "先进封装、EUV 设备和关键材料供应可能成为扩产瓶颈。 / Advanced packaging, EUV tools, and critical materials can constrain expansion.",
        ],
        "kind": "fab",
    },
    "ASML": {
        "id": "asml",
        "exchange": "NASDAQ",
        "name": "ASML Holding / 阿斯麦",
        "homepage": "https://www.asml.com/en",
        "sector": "Semiconductor equipment / 半导体设备",
        "industry": ["Lithography systems", "EUV", "DUV", "光刻机", "EUV", "DUV"],
        "labels": ["半导体", "半导体设备", "光刻机", "EUV", "AI基础设施", "英伟达相关", "美股"],
        "summaryZh": "ASML 是先进光刻设备的关键供应商，虽通常不直接向 NVIDIA 销售芯片，但其 EUV/DUV 设备是台积电、三星等制造 NVIDIA AI 芯片所需先进制程的基础。",
        "summaryEn": "ASML is a critical lithography supplier. It usually does not sell chips to NVIDIA directly, but its EUV/DUV systems enable the advanced nodes used by foundries that manufacture NVIDIA AI chips.",
        "descriptionZh": "ASML 设计和销售光刻系统、计量与计算光刻解决方案，是先进逻辑和存储芯片制造的关键设备公司。",
        "descriptionEn": "ASML designs and sells lithography systems, metrology, and computational lithography solutions that are critical to advanced logic and memory manufacturing.",
        "thesisZh": "ASML 与 NVIDIA 的联系是间接上游：AI 加速器需求推动先进制程扩产，而先进制程高度依赖 EUV/DUV 光刻设备。",
        "thesisEn": "ASML's NVIDIA linkage is indirect upstream exposure: AI accelerator demand drives leading-node expansion, and leading nodes depend heavily on EUV/DUV lithography tools.",
        "revenueModel": ["EUV 系统 / EUV systems", "DUV 系统 / DUV systems", "服务和升级 / service and upgrades"],
        "risks": [
            "出口管制和客户资本开支波动会影响设备订单节奏。 / Export controls and customer capex cycles can affect tool orders.",
            "供应链依赖精密光学、激光、机电和特种材料。 / Supply depends on precision optics, lasers, mechatronics, and specialty materials.",
        ],
        "kind": "equipment",
    },
    "AMAT": {
        "id": "amat",
        "exchange": "NASDAQ",
        "name": "Applied Materials / 应用材料",
        "homepage": "https://www.appliedmaterials.com/",
        "sector": "Semiconductor equipment / 半导体设备",
        "industry": ["Deposition", "Etch", "Process control", "薄膜沉积", "刻蚀", "制程控制"],
        "labels": ["半导体", "半导体设备", "晶圆制造", "AI基础设施", "英伟达相关", "美股"],
        "summaryZh": "应用材料提供晶圆制造设备和服务，是先进逻辑、存储和封装产线的重要设备供应商，间接受益于 NVIDIA AI 芯片供应链扩产。",
        "summaryEn": "Applied Materials provides wafer-fabrication equipment and services for advanced logic, memory, and packaging lines, giving it indirect exposure to NVIDIA AI chip supply-chain expansion.",
        "descriptionZh": "公司提供材料工程设备、服务和软件，覆盖沉积、刻蚀、离子注入、热处理、量测和封装等环节。",
        "descriptionEn": "The company provides materials-engineering equipment, services, and software across deposition, etch, implant, thermal processing, metrology, and packaging.",
        "thesisZh": "NVIDIA 相关性来自先进制程和 HBM/封装扩产所需的制程设备，而非直接面向 NVIDIA 的终端销售。",
        "thesisEn": "The NVIDIA link comes from process-equipment demand for advanced nodes, HBM, and packaging capacity rather than direct end sales to NVIDIA.",
        "revenueModel": ["半导体系统 / semiconductor systems", "应用全球服务 / applied global services", "显示及相关市场 / display and adjacent markets"],
        "risks": [
            "晶圆厂资本开支周期会放大收入波动。 / Wafer-fab capex cycles can amplify revenue volatility.",
            "中国出口限制和客户扩产延后会影响订单可见度。 / China restrictions and customer fab delays can affect order visibility.",
        ],
        "kind": "equipment",
    },
    "LRCX": {
        "id": "lrcx",
        "exchange": "NASDAQ",
        "name": "Lam Research / 泛林集团",
        "homepage": "https://www.lamresearch.com/",
        "sector": "Semiconductor equipment / 半导体设备",
        "industry": ["Etch", "Deposition", "Wafer clean", "刻蚀", "沉积", "晶圆清洗"],
        "labels": ["半导体", "半导体设备", "刻蚀", "存储", "AI基础设施", "英伟达相关", "美股"],
        "summaryZh": "泛林集团专注刻蚀、沉积和清洗设备，是先进逻辑、HBM/DRAM 和 NAND 制造链的关键设备公司，NVIDIA AI 需求通过晶圆厂和存储厂扩产传导。",
        "summaryEn": "Lam Research focuses on etch, deposition, and clean tools for advanced logic, HBM/DRAM, and NAND manufacturing, with NVIDIA AI demand transmitted through foundry and memory capex.",
        "descriptionZh": "公司向半导体制造商销售晶圆制造设备、升级和服务，尤其在刻蚀和沉积环节具备强地位。",
        "descriptionEn": "The company sells wafer-fabrication equipment, upgrades, and services to semiconductor manufacturers, with strong positions in etch and deposition.",
        "thesisZh": "与 NVIDIA 的联系主要通过 HBM、先进逻辑和封装产能投资传导，属于间接上游设备敞口。",
        "thesisEn": "The NVIDIA linkage runs through HBM, advanced logic, and packaging capacity investment, making Lam an indirect upstream equipment exposure.",
        "revenueModel": ["晶圆制造设备 / wafer fabrication equipment", "客户支持业务 / customer support business"],
        "risks": [
            "存储和逻辑资本开支周期会影响订单。 / Memory and logic capex cycles affect orders.",
            "设备交付依赖高精度部件、真空系统和特种材料。 / Tool delivery depends on high-precision parts, vacuum systems, and specialty materials.",
        ],
        "kind": "equipment",
    },
    "KLAC": {
        "id": "klac",
        "exchange": "NASDAQ",
        "name": "KLA / 科磊",
        "homepage": "https://www.kla.com/",
        "sector": "Semiconductor equipment / 半导体设备",
        "industry": ["Process control", "Inspection", "Metrology", "制程控制", "检测", "量测"],
        "labels": ["半导体", "半导体设备", "检测量测", "先进制程", "英伟达相关", "美股"],
        "summaryZh": "KLA 提供检测、量测和制程控制设备，帮助先进晶圆厂提升良率；NVIDIA AI 芯片需求通过先进制程良率和扩产需求间接传导。",
        "summaryEn": "KLA provides inspection, metrology, and process-control tools that help advanced fabs improve yield, giving it indirect exposure to NVIDIA AI chip manufacturing demand.",
        "descriptionZh": "公司向晶圆制造、封装、PCB 和相关电子制造客户提供检测、量测、数据分析和服务。",
        "descriptionEn": "The company provides inspection, metrology, data analytics, and services for wafer manufacturing, packaging, PCB, and adjacent electronics manufacturing customers.",
        "thesisZh": "NVIDIA 相关性来自先进芯片良率和缺陷控制需求，特别是高价值 AI 加速器对制程控制的要求更高。",
        "thesisEn": "The NVIDIA linkage comes from yield and defect-control requirements for advanced chips, especially high-value AI accelerators.",
        "revenueModel": ["制程控制设备 / process-control systems", "服务 / services", "特种半导体制程 / specialty semiconductor processes"],
        "risks": [
            "客户资本开支周期和先进制程推进节奏会影响需求。 / Customer capex and leading-node timing affect demand.",
            "部分 SEC XBRL 经营利润和毛利旧概念已过时，本批次未采用这些陈旧字段。 / Some SEC XBRL operating-income and gross-profit concepts are stale, so this batch does not use those stale fields.",
        ],
        "kind": "equipment",
    },
    "AMKR": {
        "id": "amkr",
        "exchange": "NASDAQ",
        "name": "Amkor Technology / 安靠科技",
        "homepage": "https://amkor.com/",
        "sector": "Semiconductor packaging and test / 半导体封测",
        "industry": ["OSAT", "Advanced packaging", "Test", "外包封测", "先进封装", "测试"],
        "labels": ["半导体", "封装测试", "先进封装", "AI基础设施", "英伟达相关", "美股"],
        "summaryZh": "Amkor 是外包半导体封装与测试厂商，AI 芯片供应链扩张会提升先进封装和测试产能的重要性。",
        "summaryEn": "Amkor is an outsourced semiconductor assembly and test provider. AI chip supply-chain expansion increases the importance of advanced packaging and test capacity.",
        "descriptionZh": "公司为半导体客户提供封装设计、组装、先进封装和测试服务，覆盖通信、汽车、计算和消费电子。",
        "descriptionEn": "The company provides package design, assembly, advanced packaging, and test services for semiconductor customers across communications, automotive, computing, and consumer electronics.",
        "thesisZh": "与 NVIDIA 的联系是先进封装和测试产能的间接敞口；AI 加速器越复杂，封装、基板和测试环节越关键。",
        "thesisEn": "The NVIDIA linkage is indirect exposure to advanced packaging and test capacity; more complex AI accelerators make packaging, substrates, and test more critical.",
        "revenueModel": ["封装服务 / assembly services", "测试服务 / test services", "先进封装 / advanced packaging"],
        "risks": [
            "先进封装投资需要较长认证和爬坡周期。 / Advanced packaging investments require long qualification and ramp cycles.",
            "基板、载板和测试设备供应会影响交付。 / Substrate, carrier, and test-equipment supply can affect delivery.",
        ],
        "kind": "osat",
    },
    "SMCI": {
        "id": "smci",
        "exchange": "NASDAQ",
        "name": "Supermicro / 超微电脑",
        "homepage": "https://www.supermicro.com/",
        "sector": "AI servers / AI 服务器",
        "industry": ["AI servers", "Rack-scale systems", "Liquid cooling", "AI 服务器", "机柜级系统", "液冷"],
        "labels": ["服务器", "AI基础设施", "数据中心", "液冷", "英伟达相关", "美股"],
        "summaryZh": "Supermicro 提供 AI/GPU 服务器和机柜级系统，是 NVIDIA GPU 进入数据中心的关键整机与系统集成环节之一。",
        "summaryEn": "Supermicro provides AI/GPU servers and rack-scale systems, making it a key system-integration layer for NVIDIA GPUs entering data centers.",
        "descriptionZh": "公司设计和销售服务器、存储、网络、机柜级解决方案和液冷基础设施，面向企业、云和 AI 数据中心。",
        "descriptionEn": "The company designs and sells servers, storage, networking, rack-scale solutions, and liquid-cooling infrastructure for enterprise, cloud, and AI data centers.",
        "thesisZh": "NVIDIA 相关性偏直接：Supermicro 将 NVIDIA GPU、网络和软件平台集成到 AI 服务器和整机柜方案中。",
        "thesisEn": "The NVIDIA linkage is relatively direct: Supermicro integrates NVIDIA GPUs, networking, and software platforms into AI servers and rack-scale systems.",
        "revenueModel": ["服务器与存储系统 / server and storage systems", "子系统和配件 / subsystems and accessories", "服务 / services"],
        "risks": [
            "收入受 GPU 供应、客户项目节奏和库存管理影响。 / Revenue depends on GPU supply, customer project timing, and inventory management.",
            "快速扩张会带来营运资本、交付和质量控制压力。 / Rapid expansion creates working-capital, delivery, and quality-control pressure.",
        ],
        "kind": "server",
    },
    "DELL": {
        "id": "dell",
        "exchange": "NYSE",
        "name": "Dell Technologies / 戴尔科技",
        "homepage": "https://www.dell.com/",
        "sector": "Enterprise hardware and AI infrastructure / 企业硬件与 AI 基础设施",
        "industry": ["Servers", "Storage", "PCs", "AI infrastructure", "服务器", "存储", "PC", "AI 基础设施"],
        "labels": ["科技", "服务器", "AI基础设施", "企业硬件", "英伟达相关", "美股"],
        "summaryZh": "戴尔科技销售服务器、存储、PC 和服务，其 AI 服务器产品组合与 NVIDIA GPU/网络平台绑定度较高，是 NVIDIA 企业 AI 落地的重要 OEM 之一。",
        "summaryEn": "Dell sells servers, storage, PCs, and services. Its AI server portfolio is closely tied to NVIDIA GPU and networking platforms, making Dell an important enterprise AI OEM.",
        "descriptionZh": "公司提供基础设施解决方案、客户端设备、软件和服务，覆盖企业数据中心、边缘和终端设备。",
        "descriptionEn": "The company provides infrastructure solutions, client devices, software, and services across enterprise data centers, edge, and endpoints.",
        "thesisZh": "NVIDIA 相关性来自 AI 服务器出货和企业 AI 项目，GPU 供应、订单积压和毛利率是核心变量。",
        "thesisEn": "The NVIDIA linkage comes from AI server shipments and enterprise AI projects, with GPU supply, backlog, and margin as core variables.",
        "revenueModel": ["基础设施解决方案 / infrastructure solutions", "客户端解决方案 / client solutions", "服务与软件 / services and software"],
        "risks": [
            "AI 服务器收入可能伴随较低毛利率和营运资本压力。 / AI server revenue can carry lower margins and working-capital pressure.",
            "PC 周期、企业 IT 支出和 GPU 供应都会影响组合。 / PC cycles, enterprise IT spending, and GPU supply affect the mix.",
        ],
        "kind": "server",
    },
    "HPE": {
        "id": "hpe",
        "exchange": "NYSE",
        "name": "Hewlett Packard Enterprise / 慧与",
        "homepage": "https://www.hpe.com/",
        "sector": "Enterprise infrastructure / 企业基础设施",
        "industry": ["Servers", "Networking", "Hybrid cloud", "AI systems", "服务器", "网络", "混合云", "AI 系统"],
        "labels": ["科技", "服务器", "AI基础设施", "企业网络", "英伟达相关", "美股"],
        "summaryZh": "HPE 提供服务器、网络、存储和混合云基础设施，并与 NVIDIA 平台共同服务企业 AI/HPC 场景。",
        "summaryEn": "HPE provides servers, networking, storage, and hybrid-cloud infrastructure, and works with NVIDIA platforms in enterprise AI and HPC scenarios.",
        "descriptionZh": "公司向企业和公共部门客户提供计算、网络、存储、混合云和边缘基础设施。",
        "descriptionEn": "The company provides compute, networking, storage, hybrid-cloud, and edge infrastructure to enterprise and public-sector customers.",
        "thesisZh": "NVIDIA 相关性来自 AI/HPC 服务器、企业 AI 系统和加速计算集成，需求由企业与主权 AI 项目驱动。",
        "thesisEn": "The NVIDIA linkage comes from AI/HPC servers, enterprise AI systems, and accelerated-computing integration, driven by enterprise and sovereign AI projects.",
        "revenueModel": ["服务器 / servers", "混合云 / hybrid cloud", "智能边缘与网络 / intelligent edge and networking"],
        "risks": [
            "企业 IT 项目周期和大型 AI 集群交付节奏会影响收入确认。 / Enterprise IT cycles and large AI-cluster delivery timing affect revenue recognition.",
            "并购整合和产品组合变化可能影响利润率。 / Integration and mix changes can affect margins.",
        ],
        "kind": "server",
    },
    "MSFT": {
        "id": "msft",
        "exchange": "NASDAQ",
        "name": "Microsoft / 微软",
        "homepage": "https://www.microsoft.com/",
        "sector": "Cloud, software and AI / 云、软件与 AI",
        "industry": ["Cloud computing", "Productivity software", "AI platforms", "云计算", "办公软件", "AI 平台"],
        "labels": ["科技", "云计算", "AI", "软件服务", "英伟达相关", "美股"],
        "summaryZh": "微软通过 Azure 和 AI 服务消耗大规模 GPU 基础设施，是 NVIDIA 数据中心 GPU 需求的重要下游客户之一，同时也向企业客户转售 AI 算力和软件服务。",
        "summaryEn": "Microsoft consumes large-scale GPU infrastructure through Azure and AI services, making it an important downstream customer for NVIDIA data-center GPUs while reselling AI compute and software services.",
        "descriptionZh": "微软经营云服务、企业软件、生产力工具、游戏、搜索广告和 AI 平台，Azure 是其 AI 基础设施扩张核心。",
        "descriptionEn": "Microsoft operates cloud services, enterprise software, productivity tools, gaming, search ads, and AI platforms, with Azure central to AI infrastructure expansion.",
        "thesisZh": "NVIDIA 相关性来自 Azure GPU 集群和 AI 服务需求；微软既是 NVIDIA 的大型客户，也是 AI 算力需求的聚合者。",
        "thesisEn": "The NVIDIA linkage comes from Azure GPU clusters and AI service demand; Microsoft is both a large NVIDIA customer and an aggregator of AI compute demand.",
        "revenueModel": ["云服务 / cloud services", "生产力软件 / productivity software", "Windows 和设备 / Windows and devices", "游戏 / gaming"],
        "risks": [
            "AI 基础设施资本开支回报周期可能拉长。 / AI infrastructure capex payback periods may lengthen.",
            "云竞争、监管和模型成本会影响利润率。 / Cloud competition, regulation, and model costs can affect margins.",
        ],
        "kind": "cloud",
    },
    "AMZN": {
        "id": "amzn",
        "exchange": "NASDAQ",
        "name": "Amazon / 亚马逊",
        "homepage": "https://www.amazon.com/",
        "sector": "E-commerce, cloud and AI / 电商、云与 AI",
        "industry": ["E-commerce", "AWS", "AI infrastructure", "Advertising", "电商", "AWS", "AI 基础设施", "广告"],
        "labels": ["科技", "云计算", "AI", "电商", "英伟达相关", "美股"],
        "summaryZh": "亚马逊通过 AWS 为客户提供云计算、AI 和 GPU 实例，是 NVIDIA 数据中心 GPU 的重要下游需求方之一，同时也有自研加速器作为补充。",
        "summaryEn": "Amazon provides cloud, AI, and GPU instances through AWS, making it an important downstream source of NVIDIA data-center GPU demand while also using in-house accelerators.",
        "descriptionZh": "公司经营线上零售、第三方商家服务、订阅、广告、物流和 AWS 云服务。",
        "descriptionEn": "The company operates online retail, third-party seller services, subscriptions, advertising, logistics, and AWS cloud services.",
        "thesisZh": "NVIDIA 相关性主要来自 AWS AI/GPU 云服务，客户对训练和推理算力的需求会影响 GPU 采购和数据中心投资。",
        "thesisEn": "The NVIDIA linkage mainly comes from AWS AI/GPU cloud services, where customer demand for training and inference compute affects GPU purchases and data-center investment.",
        "revenueModel": ["线上商店 / online stores", "第三方卖家服务 / third-party seller services", "AWS / AWS", "广告 / advertising"],
        "risks": [
            "AWS 增速、资本开支和自研芯片替代路径会影响 NVIDIA 暴露。 / AWS growth, capex, and in-house chip substitution affect NVIDIA exposure.",
            "零售利润率、物流成本和监管仍会影响整体业绩。 / Retail margins, logistics costs, and regulation still affect overall results.",
        ],
        "kind": "cloud",
    },
    "GOOGL": {
        "id": "googl",
        "exchange": "NASDAQ",
        "name": "Alphabet / Google / 字母表",
        "homepage": "https://abc.xyz/",
        "sector": "Internet, cloud and AI / 互联网、云与 AI",
        "industry": ["Search", "Advertising", "Google Cloud", "AI", "搜索", "广告", "Google Cloud", "AI"],
        "labels": ["科技", "云计算", "AI", "广告", "英伟达相关", "美股"],
        "summaryZh": "Alphabet 通过 Google Cloud 和内部 AI 工作负载使用 GPU 与自研 TPU，既是 NVIDIA 数据中心生态客户，也是不完全依赖 NVIDIA 的 AI 平台公司。",
        "summaryEn": "Alphabet uses GPUs and in-house TPUs through Google Cloud and internal AI workloads, making it both an NVIDIA data-center ecosystem customer and an AI platform company with partial in-house alternatives.",
        "descriptionZh": "公司经营 Google 搜索、广告、YouTube、Google Cloud、硬件和其他业务，AI 是搜索、云和开发者平台的共同主线。",
        "descriptionEn": "The company operates Google Search, ads, YouTube, Google Cloud, hardware, and other bets, with AI spanning search, cloud, and developer platforms.",
        "thesisZh": "NVIDIA 相关性来自 Google Cloud GPU 实例和内部 AI 训练/推理需求，但 TPU 自研路径会降低单一供应商依赖。",
        "thesisEn": "The NVIDIA linkage comes from Google Cloud GPU instances and internal AI training/inference demand, while in-house TPU development reduces single-supplier dependence.",
        "revenueModel": ["Google 服务 / Google Services", "Google Cloud / Google Cloud", "其他业务 / Other Bets"],
        "risks": [
            "广告周期、监管和 AI 搜索产品迁移会影响利润池。 / Ad cycles, regulation, and AI search migration affect profit pools.",
            "自研 TPU 与外部 GPU 的组合变化会影响 NVIDIA 相关敞口。 / The mix of in-house TPUs and external GPUs affects NVIDIA-related exposure.",
        ],
        "kind": "cloud",
    },
    "ORCL": {
        "id": "orcl",
        "exchange": "NYSE",
        "name": "Oracle / 甲骨文",
        "homepage": "https://www.oracle.com/",
        "sector": "Enterprise software and cloud / 企业软件与云",
        "industry": ["Cloud infrastructure", "Database", "Enterprise software", "云基础设施", "数据库", "企业软件"],
        "labels": ["科技", "云计算", "数据库", "AI基础设施", "英伟达相关", "美股"],
        "summaryZh": "Oracle 通过 OCI 提供云基础设施、数据库和 AI 训练集群，GPU 云需求使其成为 NVIDIA 数据中心生态的重要下游客户之一。",
        "summaryEn": "Oracle provides cloud infrastructure, databases, and AI training clusters through OCI, making GPU cloud demand an important NVIDIA ecosystem linkage.",
        "descriptionZh": "公司提供数据库、中间件、应用软件、云基础设施和相关服务，OCI 是其 AI 基础设施增长核心。",
        "descriptionEn": "The company provides databases, middleware, applications, cloud infrastructure, and related services, with OCI central to AI infrastructure growth.",
        "thesisZh": "NVIDIA 相关性来自 OCI 的 GPU 集群和云服务扩张，订单、资本开支和数据中心电力供应是关键变量。",
        "thesisEn": "The NVIDIA linkage comes from OCI GPU clusters and cloud-services expansion, with backlog, capex, and data-center power availability as key variables.",
        "revenueModel": ["云和许可证 / cloud and license", "硬件 / hardware", "服务 / services"],
        "risks": [
            "大型 AI 云合同交付节奏和资本开支强度会影响现金流。 / Large AI cloud contract timing and capex intensity affect cash flow.",
            "数据库和应用软件业务仍受企业 IT 周期影响。 / Database and application software remain exposed to enterprise IT cycles.",
        ],
        "kind": "cloud",
    },
    "CRWV": {
        "id": "crwv",
        "exchange": "NASDAQ",
        "name": "CoreWeave / CoreWeave AI 云",
        "homepage": "https://www.coreweave.com/",
        "sector": "AI cloud infrastructure / AI 云基础设施",
        "industry": ["GPU cloud", "AI infrastructure", "Data centers", "GPU 云", "AI 基础设施", "数据中心"],
        "labels": ["云计算", "AI", "GPU云", "数据中心", "英伟达相关", "美股"],
        "summaryZh": "CoreWeave 是专注 GPU 云的上市公司，业务与 NVIDIA GPU 供给、数据中心融资和 AI 客户需求高度相关；公司仍处于高增长与高资本开支阶段。",
        "summaryEn": "CoreWeave is a public GPU-cloud company with high exposure to NVIDIA GPU supply, data-center financing, and AI customer demand, while still in a high-growth, high-capex phase.",
        "descriptionZh": "公司向 AI 实验室、企业和开发者提供 GPU 云、托管 Kubernetes、存储和网络基础设施。",
        "descriptionEn": "The company provides GPU cloud, managed Kubernetes, storage, and networking infrastructure to AI labs, enterprises, and developers.",
        "thesisZh": "NVIDIA 相关性最直接：CoreWeave 的云服务能力高度依赖 NVIDIA GPU 采购、部署和融资能力。",
        "thesisEn": "The NVIDIA linkage is direct: CoreWeave's cloud-service capacity depends heavily on NVIDIA GPU procurement, deployment, and financing capacity.",
        "revenueModel": ["GPU 云实例 / GPU cloud instances", "托管 AI 基础设施 / managed AI infrastructure", "存储和网络 / storage and networking"],
        "risks": [
            "公司仍有亏损和高杠杆/高资本开支特征。 / The company still has losses and high leverage/capex characteristics.",
            "客户集中、GPU 供应和数据中心电力制约会放大波动。 / Customer concentration, GPU supply, and data-center power constraints can amplify volatility.",
        ],
        "kind": "cloud",
    },
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def stock_url(ticker: str) -> str:
    return f"https://www.nasdaq.com/market-activity/stocks/{ticker.lower()}"


def listed(ticker: str, exchange: str, *, market: str = "US", url: str | None = None) -> dict[str, Any]:
    return {"status": "listed", "ticker": ticker, "exchange": exchange, "market": market, "stockUrl": url or stock_url(ticker)}


def unknown_listing(note_zh: str, note_en: str) -> dict[str, Any]:
    return {"status": "unknown", "note": note_zh, "noteZh": note_zh, "noteEn": note_en}


def source_ids(meta: dict[str, Any]) -> dict[str, str]:
    prefix = meta["id"]
    return {
        "homepage": f"{prefix}-homepage",
        "submissions": f"{prefix}-sec-submissions",
        "companyfacts": f"{prefix}-sec-companyfacts",
        "quote": f"{prefix}-nasdaq-quote",
        "nvidia10k": "nvidia-10k-2026",
        "nvidiaSystems": "nvidia-rtx-pro-systems-2025",
    }


def sources_for(meta: dict[str, Any], draft: dict[str, Any], ids: dict[str, str]) -> list[dict[str, Any]]:
    cik = draft["identity"]["cik"]
    return [
        {
            "id": ids["homepage"],
            "title": f"{meta['name']} company website",
            "titleZh": f"{meta['name']} 公司官网",
            "titleEn": f"{meta['name']} company website",
            "publisher": meta["name"],
            "url": meta["homepage"],
            "accessedAt": ACCESSED_AT,
            "type": "company",
        },
        {
            "id": ids["submissions"],
            "title": f"{draft['identity']['ticker']} SEC submissions",
            "titleZh": f"{draft['identity']['ticker']} SEC submissions 数据",
            "titleEn": f"{draft['identity']['ticker']} SEC submissions",
            "publisher": "SEC EDGAR",
            "url": f"https://data.sec.gov/submissions/CIK{cik}.json",
            "accessedAt": ACCESSED_AT,
            "type": "sec",
        },
        {
            "id": ids["companyfacts"],
            "title": f"{draft['identity']['ticker']} SEC companyfacts XBRL data",
            "titleZh": f"{draft['identity']['ticker']} SEC companyfacts XBRL 数据",
            "titleEn": f"{draft['identity']['ticker']} SEC companyfacts XBRL data",
            "publisher": "SEC EDGAR",
            "url": f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json",
            "accessedAt": ACCESSED_AT,
            "type": "sec",
        },
        {
            "id": ids["quote"],
            "title": f"{draft['identity']['ticker']} Nasdaq quote page",
            "titleZh": f"{draft['identity']['ticker']} Nasdaq 行情页面",
            "titleEn": f"{draft['identity']['ticker']} Nasdaq quote page",
            "publisher": "Nasdaq",
            "url": stock_url(draft["identity"]["ticker"]),
            "accessedAt": ACCESSED_AT,
            "type": "exchange",
        },
        {
            "id": ids["nvidia10k"],
            "title": "NVIDIA FY2026 Form 10-K",
            "titleZh": "NVIDIA 2026 财年 10-K 年报",
            "titleEn": "NVIDIA FY2026 Form 10-K",
            "publisher": "SEC EDGAR",
            "url": NVDA_10K_URL,
            "accessedAt": ACCESSED_AT,
            "type": "sec",
        },
        {
            "id": ids["nvidiaSystems"],
            "title": "NVIDIA RTX PRO Servers With Blackwell Coming to Enterprise Systems",
            "titleZh": "NVIDIA RTX PRO Blackwell 服务器进入企业系统生态",
            "titleEn": "NVIDIA RTX PRO Servers With Blackwell Coming to Enterprise Systems",
            "publisher": "NVIDIA Investor Relations",
            "url": NVDA_RTX_SYSTEMS_URL,
            "accessedAt": ACCESSED_AT,
            "type": "company",
        },
    ]


def fact_period(fact: dict[str, Any], cadence: str) -> tuple[str, str, str]:
    end = fact.get("end", "")
    if cadence == "quarterly":
        fp = str(fact.get("fp") or "Q").replace("Q", "")
        fy = str(fact.get("fy") or end[:4])
        base = f"Q{fp} FY{fy}"
        return base, f"{fy} 财年第 {fp} 财季", base
    year = end[:4] or str(fact.get("fy") or "")
    base = f"FY{year}"
    return base, f"{year} 财年", base


def highlight_period(fact: dict[str, Any], cadence: str) -> tuple[str, str, str]:
    end = fact.get("end", "")
    if cadence == "quarterly":
        return f"Quarter ended {end}", f"截至 {end} 的季度", f"Quarter ended {end}"
    return f"Year ended {end}", f"截至 {end} 的年度", f"Year ended {end}"


def scale_value(raw_value: float, raw_unit: str) -> tuple[float, str]:
    if raw_unit in MONEY_UNITS:
        return round(raw_value / 1_000_000_000, 3), f"{raw_unit} billions"
    return raw_value, raw_unit


def comparable_change(current: dict[str, Any], previous: dict[str, Any] | None, raw_unit: str) -> tuple[str, str, str] | None:
    if not previous or current.get("fp") != previous.get("fp"):
        return None
    current_value = current.get("value")
    previous_value = previous.get("value")
    if not isinstance(current_value, (int, float)) or not isinstance(previous_value, (int, float)) or previous_value <= 0:
        return None
    if raw_unit not in MONEY_UNITS:
        return None
    pct = (current_value / previous_value - 1) * 100
    change = f"{pct:+.1f}% vs prior comparable period"
    return change, f"较上一可比期间 {pct:+.1f}%", change


def facts_for(draft: dict[str, Any], metric: str, cadence: str) -> tuple[list[dict[str, Any]], str]:
    metric_data = draft["financials"].get(metric, {})
    if metric_data.get("status") != "ok":
        return [], ""
    facts = metric_data.get(cadence, [])
    fresh = []
    for fact in facts:
        end = str(fact.get("end", ""))
        if end[:4].isdigit() and int(end[:4]) < 2023:
            continue
        fresh.append(fact)
    return fresh, str(metric_data.get("unit", "USD"))


def make_highlight(draft: dict[str, Any], metric: str, source_id: str) -> dict[str, Any] | None:
    quarterly, unit = facts_for(draft, metric, "quarterly")
    annual, annual_unit = facts_for(draft, metric, "annual")
    cadence = "quarterly" if quarterly else "annual"
    facts = quarterly or annual
    unit = unit or annual_unit
    if not facts:
        return None
    fact = facts[0]
    value, scaled_unit = scale_value(fact["value"], unit)
    period, period_zh, period_en = highlight_period(fact, cadence)
    period_short, period_short_zh, period_short_en = fact_period(fact, cadence)
    label_zh, label_en = METRIC_LABELS[metric]
    highlight = {
        "label": f"{period_short} {label_en}",
        "labelZh": f"{period_short_zh} {label_zh}",
        "labelEn": f"{period_short_en} {label_en}",
        "value": value,
        "unit": scaled_unit,
        "period": period,
        "periodZh": period_zh,
        "periodEn": period_en,
        "sourceIds": [source_id],
    }
    if metric == "revenue":
        change = comparable_change(fact, facts[1] if len(facts) > 1 else None, unit)
        if change:
            highlight["change"], highlight["changeZh"], highlight["changeEn"] = change
    return highlight


def make_trend(draft: dict[str, Any], metric: str, source_id: str) -> dict[str, Any] | None:
    facts, unit = facts_for(draft, metric, "annual")
    if len(facts) < 2:
        return None
    points = []
    for fact in list(reversed(facts[:4])):
        value, scaled_unit = scale_value(fact["value"], unit)
        period, period_zh, period_en = fact_period(fact, "annual")
        points.append({"period": period, "periodZh": period_zh, "periodEn": period_en, "value": value, "sourceIds": [source_id]})
    label_zh, label_en = METRIC_LABELS[metric]
    _, scaled_unit = scale_value(facts[0]["value"], unit)
    return {
        "id": f"annual-{metric.replace('_', '-')}",
        "label": f"Annual {label_en}",
        "labelZh": f"年度{label_zh}",
        "labelEn": f"Annual {label_en}",
        "unit": scaled_unit,
        "cadence": "annual",
        "note": "SEC companyfacts annual series; segment-level mix is reviewed separately.",
        "noteZh": "使用 SEC companyfacts 年度序列；分部构成另行复核。",
        "noteEn": "SEC companyfacts annual series; segment-level mix is reviewed separately.",
        "sourceIds": [source_id],
        "points": points,
    }


def make_revenue_mix(draft: dict[str, Any], source_id: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    facts, unit = facts_for(draft, "revenue", "annual")
    if not facts:
        return [], []
    latest = facts[0]
    latest_value, scaled_unit = scale_value(latest["value"], unit)
    period, period_zh, period_en = fact_period(latest, "annual")
    note_zh = "批量自动稿仅使用可核对的总收入；分部收入拆分需要后续人工读取年报表格。"
    note_en = "The batch draft uses only verifiable total revenue; segment revenue split requires later manual annual-report table review."
    current_mix = [
        {
            "name": "Total revenue",
            "nameZh": "总收入",
            "nameEn": "Total revenue",
            "revenue": latest_value,
            "unit": scaled_unit,
            "period": period,
            "periodZh": period_zh,
            "periodEn": period_en,
            "share": 100,
            "note": note_zh,
            "noteZh": note_zh,
            "noteEn": note_en,
            "sourceIds": [source_id],
        }
    ]

    history = []
    for fact in list(reversed(facts[:4])):
        value, scaled_unit = scale_value(fact["value"], unit)
        period, period_zh, period_en = fact_period(fact, "annual")
        history.append(
            {
                "period": period,
                "periodZh": period_zh,
                "periodEn": period_en,
                "totalRevenue": value,
                "note": note_zh,
                "noteZh": note_zh,
                "noteEn": note_en,
                "sourceIds": [source_id],
                "segments": [
                    {
                        "name": "Total revenue",
                        "nameZh": "总收入",
                        "nameEn": "Total revenue",
                        "revenue": value,
                        "unit": scaled_unit,
                        "share": 100,
                        "sourceIds": [source_id],
                    }
                ],
            }
        )
    return current_mix, history


def entity(
    name: str,
    name_zh: str,
    name_en: str,
    relationship_zh: str,
    relationship_en: str,
    products_zh: list[str],
    products_en: list[str],
    listing: dict[str, Any],
    source_ids: list[str],
    *,
    confidence: str = "medium",
    company_url: str | None = None,
) -> dict[str, Any]:
    payload = {
        "name": name,
        "nameZh": name_zh,
        "nameEn": name_en,
        "relationship": relationship_zh,
        "relationshipZh": relationship_zh,
        "relationshipEn": relationship_en,
        "productsServices": products_zh,
        "productsServicesZh": products_zh,
        "productsServicesEn": products_en,
        "listing": listing,
        "confidence": confidence,
        "sourceIds": source_ids,
    }
    if company_url:
        payload["companyUrl"] = company_url
    return payload


def target_entity(meta: dict[str, Any], draft: dict[str, Any], ids: dict[str, str]) -> dict[str, Any]:
    ticker = draft["identity"]["ticker"]
    return entity(
        meta["name"],
        meta["name"],
        draft["identity"].get("legalName") or meta["name"],
        "目标公司；本页围绕其 NVIDIA 相关供应链位置进行整理。",
        "Target company; this page maps its NVIDIA-related supply-chain position.",
        meta["revenueModel"],
        meta["revenueModel"],
        listed(ticker, meta["exchange"]),
        [ids["homepage"], ids["quote"]],
        confidence="high",
        company_url=meta["homepage"],
    )


def nvidia_supplier(ids: dict[str, str], relationship_zh: str, relationship_en: str) -> dict[str, Any]:
    return entity(
        "NVIDIA Corporation / 英伟达",
        "NVIDIA Corporation / 英伟达",
        "NVIDIA Corporation",
        relationship_zh,
        relationship_en,
        ["GPU 加速器", "网络与系统平台", "AI 软件栈"],
        ["GPU accelerators", "networking and system platforms", "AI software stack"],
        listed("NVDA", "NASDAQ"),
        [ids["nvidia10k"], ids["nvidiaSystems"]],
        confidence="high",
        company_url="https://www.nvidia.com/",
    )


def downstream_entity(item: dict[str, Any], role_zh: str, role_en: str) -> dict[str, Any]:
    item["customerRole"] = role_zh
    item["customerRoleZh"] = role_zh
    item["customerRoleEn"] = role_en
    return item


def generic_input_entities(meta: dict[str, Any], ids: dict[str, str]) -> list[dict[str, Any]]:
    kind = meta["kind"]
    if kind == "fab":
        return [
            entity(
                "ASML Holding / 阿斯麦",
                "ASML Holding / 阿斯麦",
                "ASML Holding N.V.",
                "向先进晶圆厂供应 EUV/DUV 光刻设备，是先进制程产能的关键上游。",
                "Supplies EUV/DUV lithography tools to advanced fabs and is a critical upstream node for leading-node capacity.",
                ["EUV 光刻机", "DUV 光刻机", "光刻服务"],
                ["EUV lithography systems", "DUV lithography systems", "lithography services"],
                listed("ASML", "NASDAQ"),
                [ids["homepage"], ids["nvidia10k"]],
            ),
            entity(
                "Applied Materials / 应用材料",
                "Applied Materials / 应用材料",
                "Applied Materials, Inc.",
                "向晶圆厂供应沉积、刻蚀和材料工程设备。",
                "Supplies deposition, etch, and materials-engineering tools to fabs.",
                ["沉积设备", "刻蚀设备", "服务"],
                ["deposition tools", "etch tools", "services"],
                listed("AMAT", "NASDAQ"),
                [ids["homepage"]],
            ),
        ]
    if kind in {"server", "cloud"}:
        return [
            nvidia_supplier(
                ids,
                "供应 GPU、网络和软件平台，是该公司 AI 服务器或 GPU 云服务的重要上游。",
                "Supplies GPUs, networking, and software platforms that are important upstream inputs for the company's AI servers or GPU cloud services.",
            ),
            entity(
                "Data-center power and cooling suppliers / 数据中心电力与散热供应商",
                "数据中心电力与散热供应商",
                "Data-center power and cooling suppliers",
                "为 AI 集群提供电力设备、液冷、机柜和热管理系统。",
                "Provide power equipment, liquid cooling, racks, and thermal-management systems for AI clusters.",
                ["电力设备", "液冷系统", "机柜与配电"],
                ["power equipment", "liquid cooling", "racks and power distribution"],
                unknown_listing("多为项目供应商，上市状态需逐项确认。", "Project suppliers vary and listing status requires case-by-case review."),
                [ids["homepage"]],
                confidence="medium",
            ),
        ]
    if kind == "osat":
        return [
            entity(
                "Substrate and test-equipment suppliers / 基板与测试设备供应商",
                "基板与测试设备供应商",
                "Substrate and test-equipment suppliers",
                "为先进封装与测试提供封装基板、探针卡、测试机和材料。",
                "Provide package substrates, probe cards, testers, and materials for advanced packaging and test.",
                ["封装基板", "测试设备", "探针卡"],
                ["package substrates", "test equipment", "probe cards"],
                unknown_listing("需按具体供应商进一步映射。", "Requires further mapping by specific supplier."),
                [ids["homepage"]],
            )
        ]
    return [
        entity(
            "Precision components and specialty materials / 精密部件与特种材料",
            "精密部件与特种材料供应商",
            "Precision component and specialty material suppliers",
            "向半导体设备公司供应光学、真空、机电、气体和高纯材料。",
            "Supply optics, vacuum, mechatronics, gases, and high-purity materials to semiconductor equipment makers.",
            ["精密部件", "真空系统", "特种材料"],
            ["precision components", "vacuum systems", "specialty materials"],
            unknown_listing("多为私营或多层供应商，需进一步逐项追踪。", "Often private or multi-tier suppliers; further supplier-by-supplier tracing is required."),
            [ids["homepage"]],
        )
    ]


def downstream_entities(meta: dict[str, Any], ids: dict[str, str]) -> list[dict[str, Any]]:
    kind = meta["kind"]
    if kind == "fab":
        return [
            downstream_entity(
                entity(
                    "NVIDIA Corporation / 英伟达",
                    "NVIDIA Corporation / 英伟达",
                    "NVIDIA Corporation",
                    "作为 AI 加速器设计公司，其先进芯片制造需求通过晶圆代工和先进封装传导至台积电。",
                    "As an AI accelerator designer, its advanced-chip manufacturing demand flows to TSMC through foundry and advanced packaging capacity.",
                    ["AI GPU 晶圆制造", "先进封装产能"],
                    ["AI GPU wafer manufacturing", "advanced packaging capacity"],
                    listed("NVDA", "NASDAQ"),
                    [ids["nvidia10k"]],
                    confidence="medium",
                    company_url="https://www.nvidia.com/",
                ),
                "AI 芯片设计客户 / 需求来源",
                "AI chip design customer / demand source",
            )
        ]
    if kind == "equipment":
        return [
            downstream_entity(
                entity(
                    "TSMC / 台积电",
                    "TSMC / 台积电",
                    "Taiwan Semiconductor Manufacturing Company Limited",
                    "先进晶圆厂客户；其先进制程扩产是设备需求的重要来源。",
                    "Advanced foundry customer; its leading-node expansion is an important source of equipment demand.",
                    ["晶圆制造设备需求", "先进制程扩产"],
                    ["wafer-fab equipment demand", "leading-node expansion"],
                    listed("TSM", "NYSE"),
                    [ids["homepage"], ids["nvidia10k"]],
                    confidence="medium",
                    company_url="https://www.tsmc.com/english",
                ),
                "晶圆厂客户 / 设备需求方",
                "Foundry customer / equipment-demand source",
            ),
            downstream_entity(
                entity(
                    "NVIDIA Corporation / 英伟达",
                    "NVIDIA Corporation / 英伟达",
                    "NVIDIA Corporation",
                    "不是典型直接客户；NVIDIA AI 芯片需求通过台积电、存储厂和先进封装投资间接拉动设备需求。",
                    "Not typically a direct customer; NVIDIA AI-chip demand indirectly drives equipment demand through foundries, memory makers, and advanced-packaging investment.",
                    ["间接 AI 需求", "先进制程与 HBM 扩产"],
                    ["indirect AI demand", "advanced-node and HBM expansion"],
                    listed("NVDA", "NASDAQ"),
                    [ids["nvidia10k"]],
                    confidence="medium",
                    company_url="https://www.nvidia.com/",
                ),
                "间接需求驱动方",
                "Indirect demand driver",
            ),
        ]
    if kind == "osat":
        return [
            downstream_entity(
                entity(
                    "NVIDIA AI accelerator ecosystem / NVIDIA AI 加速器生态",
                    "NVIDIA AI 加速器生态",
                    "NVIDIA AI accelerator ecosystem",
                    "AI 加速器复杂度提升会增加先进封装、基板和测试需求；是否为直接客户需按具体项目确认。",
                    "Higher AI-accelerator complexity increases advanced packaging, substrate, and test demand; direct-customer status requires project-level confirmation.",
                    ["先进封装", "封装测试", "基板与可靠性测试"],
                    ["advanced packaging", "assembly and test", "substrates and reliability test"],
                    listed("NVDA", "NASDAQ"),
                    [ids["nvidia10k"]],
                    confidence="medium",
                ),
                "AI 封装测试需求来源",
                "AI packaging and test demand source",
            )
        ]
    return [
        downstream_entity(
            entity(
                "Enterprise and AI customers / 企业与 AI 客户",
                "企业与 AI 客户",
                "Enterprise and AI customers",
                "购买 AI 服务器、GPU 云或加速计算服务，将 NVIDIA GPU 能力转化为训练、推理和企业应用。",
                "Buy AI servers, GPU cloud, or accelerated-computing services, converting NVIDIA GPU capacity into training, inference, and enterprise applications.",
                ["AI 训练", "AI 推理", "企业应用"],
                ["AI training", "AI inference", "enterprise applications"],
                unknown_listing("客户群体分散，上市状态需按客户名单继续拆解。", "Customer base is broad; listing status requires customer-by-customer mapping."),
                [ids["homepage"], ids["nvidiaSystems"]],
                confidence="medium",
            ),
            "终端客户 / 算力使用方",
            "End customer / compute user",
        )
    ]


def raw_materials_for(kind: str) -> list[dict[str, Any]]:
    if kind in {"fab", "equipment", "osat"}:
        materials = [
            ("硅晶圆", "Silicon wafers", "用于晶圆制造、设备验证或封装测试。", "Used in wafer manufacturing, tool qualification, or packaging and test."),
            ("高纯特种气体与化学品", "High-purity specialty gases and chemicals", "用于光刻、沉积、刻蚀、清洗和封装流程。", "Used in lithography, deposition, etch, clean, and packaging processes."),
            ("铜、铝、钨、钴等金属材料", "Copper, aluminum, tungsten, cobalt and other metals", "用于互连、沉积、封装和设备部件。", "Used in interconnects, deposition, packaging, and tool components."),
        ]
    else:
        materials = [
            ("GPU、HBM 与高端 PCB/基板", "GPUs, HBM, and high-end PCBs/substrates", "用于 AI 服务器、GPU 云实例和高速互连。", "Used in AI servers, GPU cloud instances, and high-speed interconnects."),
            ("电力、铜和散热材料", "Power, copper, and thermal materials", "用于数据中心供电、配电、线缆、液冷和热管理。", "Used in data-center power, distribution, cabling, liquid cooling, and thermal management."),
            ("光模块和网络设备材料", "Optical-module and networking materials", "用于 GPU 集群互连、数据中心交换和跨机柜通信。", "Used in GPU-cluster interconnects, data-center switching, and rack-to-rack communication."),
        ]

    return [
        {
            "name": zh,
            "nameZh": zh,
            "nameEn": en,
            "usedIn": used_zh,
            "usedInZh": used_zh,
            "usedInEn": used_en,
            "upstream": ["矿产开采与冶炼", "高纯加工与认证", "设备/材料供应商交付"],
            "upstreamZh": ["矿产开采与冶炼", "高纯加工与认证", "设备/材料供应商交付"],
            "upstreamEn": ["mining and refining", "high-purity processing and qualification", "equipment/material supplier delivery"],
            "risk": "价格、地缘限制、认证周期和扩产节奏会影响可得性。",
            "riskZh": "价格、地缘限制、认证周期和扩产节奏会影响可得性。",
            "riskEn": "Availability can be affected by price, geopolitical restrictions, qualification cycles, and expansion timing.",
            "confidence": "medium",
        }
        for zh, en, used_zh, used_en in materials
    ]


def make_supply_chain(meta: dict[str, Any], draft: dict[str, Any], ids: dict[str, str]) -> dict[str, Any]:
    upstream_entities = generic_input_entities(meta, ids)
    downstream = downstream_entities(meta, ids)
    materials_zh = [material["nameZh"] for material in raw_materials_for(meta["kind"])]
    materials_en = [material["nameEn"] for material in raw_materials_for(meta["kind"])]
    return {
        "updatedAt": LAST_UPDATED,
        "thesis": f"{meta['thesisZh']} / {meta['thesisEn']}",
        "thesisZh": meta["thesisZh"],
        "thesisEn": meta["thesisEn"],
        "tiers": [
            {
                "level": 0,
                "title": "Target company",
                "titleZh": "目标公司",
                "titleEn": "Target company",
                "companies": [meta["name"]],
                "entities": [target_entity(meta, draft, ids)],
                "geography": ["US", "Global"],
                "materials": materials_zh,
                "materialsZh": materials_zh,
                "materialsEn": materials_en,
                "notes": "目标公司本身；上市公司代码和行情链接已核对。",
                "notesZh": "目标公司本身；上市公司代码和行情链接已核对。",
                "notesEn": "Target company itself; listed ticker and quote link reviewed.",
                "confidence": "high",
                "sourceIds": [ids["homepage"], ids["quote"]],
            },
            {
                "level": 1,
                "title": "Key upstream inputs",
                "titleZh": "关键上游投入",
                "titleEn": "Key upstream inputs",
                "companies": [item["name"] for item in upstream_entities],
                "entities": upstream_entities,
                "geography": ["US", "Europe", "Asia"],
                "materials": materials_zh,
                "materialsZh": materials_zh,
                "materialsEn": materials_en,
                "notes": "列出与 NVIDIA 相关业务最重要的上游投入；具体采购比例需继续人工拆解。",
                "notesZh": "列出与 NVIDIA 相关业务最重要的上游投入；具体采购比例需继续人工拆解。",
                "notesEn": "Lists the most important upstream inputs for NVIDIA-related business; exact purchase shares require further manual work.",
                "confidence": "medium",
                "sourceIds": [ids["homepage"], ids["nvidia10k"]],
            },
        ],
        "rawMaterials": raw_materials_for(meta["kind"]),
        "downstream": {
            "updatedAt": LAST_UPDATED,
            "thesis": f"{meta['thesisZh']} / {meta['thesisEn']}",
            "thesisZh": meta["thesisZh"],
            "thesisEn": meta["thesisEn"],
            "tiers": [
                {
                    "level": 1,
                    "title": "NVIDIA-related demand path",
                    "titleZh": "英伟达相关需求路径",
                    "titleEn": "NVIDIA-related demand path",
                    "entities": downstream,
                    "notes": "该层说明目标公司如何作为 NVIDIA 的上游、伙伴、客户或间接需求受益方。",
                    "notesZh": "该层说明目标公司如何作为 NVIDIA 的上游、伙伴、客户或间接需求受益方。",
                    "notesEn": "This layer explains how the target company functions as NVIDIA's upstream supplier, partner, customer, or indirect demand beneficiary.",
                    "confidence": "medium",
                    "sourceIds": [ids["homepage"], ids["nvidia10k"]],
                }
            ],
        },
    }


def make_financials(meta: dict[str, Any], draft: dict[str, Any], ids: dict[str, str]) -> dict[str, Any]:
    highlights = [
        item
        for metric in ["revenue", "net_income", "assets", "cash_from_operations"]
        if (item := make_highlight(draft, metric, ids["companyfacts"]))
    ]
    trends = [
        item
        for metric in ["revenue", "net_income", "assets"]
        if (item := make_trend(draft, metric, ids["companyfacts"]))
    ]
    revenue_mix, revenue_mix_history = make_revenue_mix(draft, ids["companyfacts"])
    latest_text = "Latest SEC companyfacts candidates; annual baseline from the latest audited filing."
    return {
        "latestPeriod": latest_text,
        "latestPeriodZh": "使用 SEC companyfacts 中的最新可核对候选；年度基准来自最近审计年报。",
        "latestPeriodEn": latest_text,
        "highlights": highlights,
        "revenueMix": revenue_mix,
        "trends": trends,
        "revenueMixHistory": revenue_mix_history,
    }


def make_news(draft: dict[str, Any], ids: dict[str, str]) -> list[dict[str, Any]]:
    latest = draft.get("filings", [{}])[0]
    form = latest.get("form", "filing")
    filed_at = latest.get("filedAt") or ACCESSED_AT
    report_date = latest.get("reportDate") or "n/a"
    return [
        {
            "date": filed_at,
            "title": f"Recent SEC filing: {form}",
            "titleZh": f"最新 SEC 文件：{form}",
            "titleEn": f"Recent SEC filing: {form}",
            "category": "SEC filing",
            "categoryZh": "SEC 文件",
            "categoryEn": "SEC filing",
            "summary": f"SEC submissions show a {form} filed on {filed_at}; report date {report_date}.",
            "summaryZh": f"SEC submissions 显示公司于 {filed_at} 提交 {form}；报告期为 {report_date}。",
            "summaryEn": f"SEC submissions show a {form} filed on {filed_at}; report date {report_date}.",
            "impact": "Used as the latest public filing checkpoint for this batch; scheduled daily refresh remains disabled.",
            "impactZh": "作为本批次最新公开文件检查点；每日定时刷新仍未启用。",
            "impactEn": "Used as the latest public filing checkpoint for this batch; scheduled daily refresh remains disabled.",
            "sourceIds": [ids["submissions"]],
        }
    ]


def make_filings(draft: dict[str, Any]) -> list[dict[str, Any]]:
    filings = []
    for filing in draft.get("filings", [])[:6]:
        form = filing.get("form", "")
        filed_at = filing.get("filedAt", "")
        if not form or not filed_at or not filing.get("url"):
            continue
        filings.append(
            {
                "form": form,
                "filedAt": filed_at,
                "reportDate": filing.get("reportDate") or "",
                "title": f"{form} filed {filed_at}",
                "url": filing["url"],
            }
        )
    return filings


def build_company(ticker: str) -> dict[str, Any]:
    meta = COMPANY_META[ticker]
    draft = read_json(DRAFT_DIR / f"us-{ticker.lower()}.draft.json")
    ids = source_ids(meta)
    currency = draft["financials"].get("revenue", {}).get("unit") or "USD"
    summary = f"{meta['summaryZh']} / {meta['summaryEn']}"
    description = f"{meta['descriptionZh']} / {meta['descriptionEn']}"
    thesis = f"{meta['thesisZh']} / {meta['thesisEn']}"
    return {
        "schemaVersion": 1,
        "id": meta["id"],
        "ticker": ticker,
        "exchange": meta["exchange"],
        "market": "US",
        "name": meta["name"],
        "legalName": draft["identity"].get("legalName") or draft["identity"].get("name") or meta["name"],
        "cik": draft["identity"]["cik"],
        "currency": currency,
        "sector": meta["sector"],
        "industry": meta["industry"],
        "homepage": meta["homepage"],
        "lastUpdated": LAST_UPDATED,
        "summary": summary,
        "summaryZh": meta["summaryZh"],
        "summaryEn": meta["summaryEn"],
        "aliases": [ticker, meta["name"], draft["identity"].get("legalName") or "", draft["identity"].get("name") or ""],
        "labels": meta["labels"],
        "updateCadence": UPDATE_CADENCE,
        "business": {
            "description": description,
            "descriptionZh": meta["descriptionZh"],
            "descriptionEn": meta["descriptionEn"],
            "revenueModel": meta["revenueModel"],
            "segments": make_revenue_mix(draft, ids["companyfacts"])[0],
            "thesis": thesis,
            "thesisZh": meta["thesisZh"],
            "thesisEn": meta["thesisEn"],
            "riskNotes": meta["risks"],
        },
        "supplyChain": make_supply_chain(meta, draft, ids),
        "financials": make_financials(meta, draft, ids),
        "news": make_news(draft, ids),
        "filings": make_filings(draft),
        "sources": sources_for(meta, draft, ids),
        "automation": {
            "sec": {
                "cik": draft["identity"]["cik"],
                "forms": ["10-K", "10-Q", "8-K", "20-F", "6-K"],
            },
            "newsFeeds": [
                {
                    "url": meta["homepage"],
                    "publisher": meta["name"],
                    "sourceType": "company",
                }
            ],
        },
    }


def add_label_to_existing(file_name: str, label: str) -> None:
    path = COMPANIES_DIR / file_name
    payload = read_json(path)
    labels = payload.setdefault("labels", [])
    if label not in labels:
        labels.insert(-1 if labels and labels[-1] == "美股" else len(labels), label)
    write_json(path, payload)


def main() -> None:
    COMPANIES_DIR.mkdir(parents=True, exist_ok=True)
    for ticker in COMPANY_META:
        report = build_company(ticker)
        write_json(COMPANIES_DIR / f"{report['id']}.json", report)
        print(f"Wrote public/data/companies/{report['id']}.json")

    add_label_to_existing("nvda.json", "英伟达相关")
    add_label_to_existing("mu.json", "英伟达相关")
    print("Updated NVDA and MU labels")


if __name__ == "__main__":
    main()
