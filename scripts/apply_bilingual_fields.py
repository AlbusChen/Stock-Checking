#!/usr/bin/env python3
"""Add curated Chinese/English display fields to company JSON reports."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPANIES_DIR = ROOT / "public" / "data" / "companies"


def has_cjk(value: str) -> bool:
    return bool(re.search(r"[\u3400-\u9fff]", value))


ZH_BY_EN = {
    "News": "新闻",
    "Earnings": "业绩",
    "Product / Developer": "产品 / 开发者",
    "Product / Ecosystem": "产品 / 生态",
    "SEC filing": "SEC 文件",
    "Q2 FY2026 revenue": "2026 财年第二财季收入",
    "Q2 FY2026 diluted EPS": "2026 财年第二财季摊薄 EPS",
    "FY2025 net sales": "2025 财年净销售额",
    "Q2 FY2026 operating cash flow": "2026 财年第二财季经营现金流",
    "Q1 FY2027 revenue": "2027 财年第一财季收入",
    "Q1 FY2027 Data Center": "2027 财年第一财季数据中心收入",
    "FY2026 revenue": "2026 财年收入",
    "Q1 FY2027 GAAP gross margin": "2027 财年第一财季 GAAP 毛利率",
    "Q1 2026 revenue": "2026 年第一季度收入",
    "Q1 2026 non-GAAP EPS": "2026 年第一季度 non-GAAP EPS",
    "FY2025 revenue": "2025 财年收入",
    "Q1 2026 GAAP gross margin": "2026 年第一季度 GAAP 毛利率",
    "Quarter ended 2026-03-28": "截至 2026-03-28 的季度",
    "Quarter ended 2026-04-26": "截至 2026-04-26 的季度",
    "FY2025": "2025 财年",
    "FY2026": "2026 财年",
    "Q1 FY2027": "2027 财年第一财季",
    "Q1 2026": "2026 年第一季度",
    "up 17% YoY": "同比增长 17%",
    "up 22% YoY": "同比增长 22%",
    "up 6% YoY": "同比增长 6%",
    "more than $28B": "超过 280 亿美元",
    "up 85% YoY": "同比增长 85%",
    "up 92% YoY": "同比增长 92%",
    "up 114% YoY": "同比增长 114%",
    "up 12.3 ppts YoY": "同比提升 12.3 个百分点",
    "up 7% YoY": "同比增长 7%",
    "up 123% YoY": "同比增长 123%",
    "flat YoY": "同比基本持平",
    "up 2.5 ppts YoY": "同比提升 2.5 个百分点",
    "FY2025 category net sales.": "2025 财年类别净销售额。",
    "Operating segment revenue; includes rounded figures.": "经营分部收入；数字经四舍五入。",
    "Includes intersegment transactions and is not additive to net revenue.": "包含分部间交易，不能直接加总为净收入。",
}

TERM_ZH_BY_EN = {
    "iPhone": "iPhone",
    "Services": "服务",
    "Mac": "Mac",
    "Wearables, Home and Accessories": "可穿戴、家居与配件",
    "iPad": "iPad",
    "Data Center": "数据中心",
    "Edge Computing": "边缘计算",
    "Client Computing Group": "客户端计算事业部",
    "Data Center and AI": "数据中心与 AI",
    "Intel Foundry": "英特尔代工",
    "Product design": "产品设计",
    "Operating systems": "操作系统",
    "Apple silicon designs": "Apple silicon 设计",
    "Finished device assembly": "整机组装",
    "EMS manufacturing": "电子制造服务",
    "Mechanical integration": "机电整合",
    "Connectors": "连接器",
    "Acoustic modules": "声学模组",
    "Device assembly": "设备组装",
    "System assembly": "系统装配",
    "Mainboard integration": "主板整合",
    "ODM manufacturing": "ODM 制造",
    "Notebook/tablet assembly": "笔电/平板组装",
    "Wearable device manufacturing": "可穿戴设备制造",
    "Regional production capacity": "区域产能",
    "Advanced logic wafers": "先进逻辑晶圆",
    "Apple silicon manufacturing": "Apple silicon 制造",
    "Foundry services": "晶圆代工服务",
    "OLED panels": "OLED 面板",
    "Display modules": "显示模组",
    "Panel technology": "面板技术",
    "LCD panels": "LCD 面板",
    "Display components": "显示组件",
    "CMOS image sensors": "CMOS 图像传感器",
    "Camera sensor technology": "摄像头传感器技术",
    "Imaging components": "成像组件",
    "MLCC": "多层陶瓷电容",
    "RF components": "射频组件",
    "Passive components": "被动元件",
    "Battery cells/components": "电池电芯/组件",
    "Battery cells": "电池电芯",
    "Battery packs": "电池包",
    "Power modules": "电源模组",
    "EUV lithography systems": "EUV 光刻系统",
    "DUV lithography systems": "DUV 光刻系统",
    "Lithography services": "光刻服务",
    "Deposition tools": "沉积设备",
    "Materials engineering": "材料工程",
    "Process equipment": "工艺设备",
    "Etch tools": "刻蚀设备",
    "Wafer cleaning equipment": "晶圆清洗设备",
    "Coater/developer tools": "涂布/显影设备",
    "Deposition equipment": "沉积设备",
    "Etch systems": "刻蚀系统",
    "Inspection tools": "检测设备",
    "Metrology systems": "量测系统",
    "Process control": "过程控制",
    "Silicon wafers": "硅晶圆",
    "Photoresists": "光刻胶",
    "Semiconductor materials": "半导体材料",
    "300mm silicon wafers": "300mm 硅晶圆",
    "Prime wafers": "抛光晶圆",
    "Epitaxial wafers": "外延晶圆",
    "GPU/CPU/DPU designs": "GPU/CPU/DPU 设计",
    "CUDA ecosystem": "CUDA 生态",
    "Reference systems": "参考系统",
    "Advanced packaging capacity": "先进封装产能",
    "HBM": "高带宽内存",
    "DRAM": "DRAM 内存",
    "HBM/DRAM": "HBM/DRAM 内存",
    "Memory components": "存储器组件",
    "Memory stacks": "内存堆叠",
    "GDDR memory": "GDDR 显存",
    "OSAT services": "封装测试服务",
    "Advanced packaging": "先进封装",
    "Semiconductor test": "半导体测试",
    "Advanced packages": "先进封装件",
    "Semiconductor packaging": "半导体封装",
    "Test services": "测试服务",
    "AI server manufacturing": "AI 服务器制造",
    "Rack integration": "机柜整合",
    "EMS capacity": "电子制造产能",
    "AI servers": "AI 服务器",
    "Rack systems": "机柜系统",
    "Server manufacturing": "服务器制造",
    "Board integration": "板卡整合",
    "GPU servers": "GPU 服务器",
    "Liquid-cooled AI systems": "液冷 AI 系统",
    "Enterprise infrastructure": "企业基础设施",
    "GPU systems": "GPU 系统",
    "AI infrastructure": "AI 基础设施",
    "HPC servers": "高性能计算服务器",
    "Workstations": "工作站",
    "Enterprise systems": "企业系统",
    "ABF substrates": "ABF 基板",
    "Package substrates": "封装基板",
    "Organic substrates": "有机基板",
    "IC substrates": "IC 载板",
    "PCBs": "印刷电路板",
    "HDI boards": "高密度互连板",
    "Semiconductor packages": "半导体封装件",
    "Lead frames": "引线框架",
    "External foundry wafers": "外部代工晶圆",
    "Advanced process capacity": "先进制程产能",
    "Chiplet manufacturing": "Chiplet 制造",
    "CPU designs": "CPU 设计",
    "Electronic gases": "电子特气",
    "Industrial gases": "工业气体",
    "On-site gas supply": "现场供气",
    "On-site gas systems": "现场供气系统",
    "Specialty materials": "特种材料",
    "Materials handling": "材料处理",
    "Filtration": "过滤",
    "CMP consumables": "CMP 消耗材料",
    "Lithography materials": "光刻材料",
    "Semiconductor chemicals": "半导体化学品",
    "Sensors": "传感器",
    "Accelerator boards": "加速卡",
    "Racks": "机柜",
    "Cooling and power": "散热与供电",
    "Finished devices": "成品设备",
    "Camera modules": "摄像头模组",
    "Enclosures": "外壳",
    "Application processors": "应用处理器",
    "Image sensors": "图像传感器",
    "Batteries": "电池",
    "Lithography tools": "光刻设备",
    "Specialty gases": "特种气体",
    "Photomasks": "光掩模",
    "DRAM stacks": "DRAM 堆叠",
    "EUV tools": "EUV 设备",
    "Wet chemicals": "湿电子化学品",
    "CMP slurry": "CMP 抛光液",
    "Assembly and test": "封装测试",
    "Assembly services": "组装服务",
    "Process nodes": "制程节点",
    "Industrial design": "工业设计",
    "Networking stack": "网络协议栈",
    "iOS/macOS ecosystem": "iOS/macOS 生态",
    "CUDA": "CUDA",
    "GPU/CPU/DPU designs": "GPU/CPU/DPU 设计",
    "Metrology": "量测",
    "Inspection": "检测",
    "Deposition": "沉积",
    "Etch": "刻蚀",
    "EUV lithography": "EUV 光刻",
    "300mm wafers": "300mm 晶圆",
    "Quartz": "石英",
    "Polysilicon": "多晶硅",
    "Lithium brine/hard rock": "锂盐湖/硬岩锂",
    "Cobalt": "钴",
    "Nickel": "镍",
    "Graphite": "石墨",
    "Rare earth oxides": "稀土氧化物",
    "Copper concentrate": "铜精矿",
    "Bauxite": "铝土矿",
    "Conflict minerals": "冲突矿产",
    "DRAM wafers": "DRAM 晶圆",
    "TSV materials": "TSV 材料",
    "Copper": "铜",
    "Packaging films": "封装薄膜",
    "Copper foil": "铜箔",
    "Resins": "树脂",
    "Fluorochemicals": "含氟化学品",
    "Noble gases": "稀有气体",
    "Solvents": "溶剂",
    "Specialty polymers": "特种聚合物",
    "Epoxy resins": "环氧树脂",
    "Glass cloth": "玻纤布",
    "Ceramics": "陶瓷",
}

EN_BY_ZH = {
    "品牌、设计、系统集成": "Brand, design, and system integration",
    "最终组装与关键模组": "Final assembly and key modules",
    "半导体、显示与电池": "Semiconductors, displays, and batteries",
    "晶圆、设备、化学品与封装": "Wafers, equipment, chemicals, and packaging",
    "芯片、系统和软件平台定义": "Chip, system, and software platform definition",
    "晶圆代工、HBM 与封装": "Foundry, HBM, and packaging",
    "板卡、服务器和整机集成": "Boards, servers, and system integration",
    "设备、基板、材料和化学品": "Equipment, substrates, materials, and chemicals",
    "产品设计、制造和 foundry 服务": "Product design, manufacturing, and foundry services",
    "晶圆厂设备与工艺工具": "Fab equipment and process tools",
    "外部 foundry、封装与基板": "External foundry, packaging, and substrates",
    "晶圆、化学品、气体和消耗材料": "Wafers, chemicals, gases, and consumables",
    "自动抓取条目，需要人工复核业务影响。": "Automatically fetched item; business impact requires manual review.",
    "短期观察点在 AI 功能是否能提升设备换机与服务使用频次。": "The near-term focus is whether AI features can lift device upgrades and service usage frequency.",
    "业绩显示 iPhone 与服务仍是主线，回购授权和股息提升强化资本回报。": "The results show iPhone and Services remain the main drivers, while buybacks and dividend increases reinforce capital returns.",
    "年报提供业务结构、供应链风险和采购义务基线。": "The annual report provides the baseline for business structure, supply-chain risk, and purchase obligations.",
    "出口限制会直接影响中国市场可达收入，但数据中心需求仍处于强周期。": "Export restrictions directly affect addressable China revenue, while data center demand remains in a strong cycle.",
    "强化 AI PC 与本地 agent 生态，可能扩大 RTX installed base 的软件价值。": "This strengthens the AI PC and local-agent ecosystem and may increase software value across the RTX installed base.",
    "供给改善和 CPU 需求支撑业绩，但 GAAP 亏损、重组费用和 foundry 投入仍需跟踪。": "Supply improvement and CPU demand supported results, but GAAP losses, restructuring charges, and foundry spending still need tracking.",
    "强化 CPU 在 AI 推理和边缘场景中的定位，但商业转化取决于生态伙伴和客户部署速度。": "This reinforces CPUs in AI inference and edge workloads, while monetization depends on ecosystem partners and customer deployment pace.",
    "公司处于修复与重构阶段，分部重组、Altera 出表和制造资产效率是分析重点。": "The company is in a repair-and-rebuild phase; segment restructuring, Altera deconsolidation, and manufacturing asset efficiency are key.",
}

NEWS_OVERRIDES = {
    "Apple and Major League Baseball announce July “Friday Night Baseball” schedule": {
        "titleZh": "Apple 与美国职业棒球大联盟公布 7 月“Friday Night Baseball”赛程",
        "titleEn": "Apple and Major League Baseball announce July Friday Night Baseball schedule",
        "summaryZh": "Apple 与 MLB 公布 7 月 Friday Night Baseball 赛程，属于 Apple TV+ 体育内容与订阅服务生态更新。",
        "summaryEn": "Apple and MLB announced the July Friday Night Baseball schedule, an update to Apple TV+ sports content and the subscription-services ecosystem.",
        "impactZh": "该消息偏服务内容更新，财务影响通常小于硬件周期，但有助于观察 Apple TV+ 内容投入与用户留存。",
        "impactEn": "This is mainly a services-content update; its financial impact is usually smaller than a hardware cycle but helps track Apple TV+ content investment and retention.",
    },
    "Mini Football Legends, Family Feud Pocket, and seven more hits join Apple Arcade": {
        "titleZh": "Mini Football Legends、Family Feud Pocket 等九款游戏加入 Apple Arcade",
        "titleEn": "Mini Football Legends, Family Feud Pocket, and seven more games join Apple Arcade",
        "summaryZh": "Apple Arcade 新增多款游戏，继续扩充订阅内容库并服务于设备生态粘性。",
        "summaryEn": "Apple Arcade added several games, continuing to expand its subscription content library and support ecosystem stickiness.",
        "impactZh": "该消息主要影响服务内容丰富度，对短期业绩影响有限，但与服务收入和用户留存相关。",
        "impactEn": "The item mainly affects services content breadth; near-term earnings impact is limited but it relates to Services revenue and retention.",
    },
    "App Store ecosystem reaches $1.4 trillion as developers thrive globally": {
        "titleZh": "App Store 生态规模达到 1.4 万亿美元，全球开发者持续增长",
        "titleEn": "App Store ecosystem reaches $1.4 trillion as developers thrive globally",
        "summaryZh": "Apple 强调 App Store 生态交易规模和开发者全球增长，突出服务平台的经济规模。",
        "summaryEn": "Apple highlighted App Store ecosystem transaction scale and global developer growth, underscoring the economic scale of its services platform.",
        "impactZh": "该消息支撑服务平台价值叙事，但也需要继续跟踪 App Store 监管和佣金压力。",
        "impactEn": "The item supports the services-platform value narrative, while App Store regulation and commission pressure still need monitoring.",
    },
    "WWDC26 将于 6 月 8 日开幕": {
        "titleZh": "WWDC26 将于 6 月 8 日开幕",
        "titleEn": "WWDC26 opens on June 8",
        "summaryEn": "Apple announced the WWDC26 schedule; the keynote and Platforms State of the Union will show platform updates, AI progress, and developer tools.",
    },
    "Apple 发布 FY2026 第二财季业绩": {
        "titleZh": "Apple 发布 2026 财年第二财季业绩",
        "titleEn": "Apple reports second-quarter FY2026 results",
        "summaryEn": "Quarterly revenue was $111.2 billion, up 17% year over year; diluted EPS was $2.01, up 22%; Services revenue reached a new record.",
    },
    "Apple 提交 FY2025 Form 10-K": {
        "titleZh": "Apple 提交 2025 财年 Form 10-K",
        "titleEn": "Apple files FY2025 Form 10-K",
        "summaryEn": "FY2025 net sales were $416.161 billion, with iPhone and Services as the largest revenue sources.",
    },
    "NVIDIA 与 Microsoft 推动个人 AI Windows PC": {
        "titleZh": "NVIDIA 与 Microsoft 推动个人 AI Windows PC",
        "titleEn": "NVIDIA and Microsoft push personal AI Windows PCs",
        "summaryEn": "NVIDIA and Microsoft announced RTX AI PC and local-agent initiatives, including Windows AI Foundry support and RTX Pro systems.",
    },
    "NVIDIA 发布 Q1 FY2027 业绩": {
        "titleZh": "NVIDIA 发布 2027 财年第一财季业绩",
        "titleEn": "NVIDIA reports first-quarter FY2027 results",
        "summaryEn": "Revenue was $81.615 billion, up 85% year over year; Data Center revenue reached $75.2 billion, up 92%; the company recorded a charge related to H20 export restrictions.",
    },
    "NVIDIA FY2026 年收入达到 2159.38 亿美元": {
        "titleZh": "NVIDIA 2026 财年收入达到 2159.38 亿美元",
        "titleEn": "NVIDIA FY2026 revenue reaches $215.938 billion",
        "summaryEn": "FY2026 revenue was $215.938 billion, up 114% year over year, led by Data Center demand.",
    },
    "Postcard from Computex 2026: New Intel® Core™ Series 3 laptops for Everyday Creation and All-day Productivity": {
        "titleZh": "Computex 2026 现场：Intel Core Series 3 笔记本面向日常创作与全天生产力",
        "titleEn": "Postcard from Computex 2026: Intel Core Series 3 laptops for everyday creation and all-day productivity",
        "summaryZh": "Intel 展示搭载新款 Core Series 3 的轻薄笔记本设计，强调续航、日常创作和生产力体验。",
        "summaryEn": "Intel showcased thin-and-light laptop designs powered by Core Series 3, emphasizing battery life, everyday creation, and productivity.",
        "impactZh": "该消息偏客户端产品线更新，影响取决于 OEM 设计落地、AI PC 需求和渠道销售。",
        "impactEn": "This is a client-product update; impact depends on OEM design wins, AI PC demand, and channel sell-through.",
    },
    "Intel Introduces Ethernet E835 Controllers and Network Adapters for Cloud, Edge and Enterprise Data Center Infrastructure": {
        "titleZh": "Intel 推出面向云、边缘和企业数据中心的 Ethernet E835 控制器与网卡",
        "titleEn": "Intel introduces Ethernet E835 controllers and network adapters for cloud, edge, and enterprise data centers",
        "summaryZh": "Intel 发布 Ethernet E835 控制器和网卡，面向高密度数据中心、企业、边缘和 AI 网络需求。",
        "summaryEn": "Intel launched Ethernet E835 controllers and network adapters for high-density data center, enterprise, edge, and AI networking needs.",
        "impactZh": "该消息强化网络和数据中心平台组合，但收入转化取决于客户认证、服务器平台导入和采购周期。",
        "impactEn": "The item strengthens Intel's networking and data center platform portfolio, while revenue conversion depends on customer qualification, platform adoption, and procurement cycles.",
    },
    "Intel 在 Computex 2026 发布 AI 创新": {
        "titleZh": "Intel 在 Computex 2026 发布 AI 创新",
        "titleEn": "Intel announces AI innovations at Computex 2026",
        "summaryEn": "Intel announced rack-scale AI infrastructure for inference and agentic workloads, Xeon 6+, ecosystem partnerships, and Series 3 processor updates.",
    },
    "Computex 2026: An Intelligent World Built on Silicon": {
        "titleZh": "Computex 2026：建立在硅之上的智能世界",
        "titleEn": "Computex 2026: An intelligent world built on silicon",
        "summaryZh": "Intel 在 Computex 主题演讲中强调 x86、AI、客户端和数据中心平台在智能计算中的作用。",
        "summaryEn": "Intel's Computex keynote emphasized the role of x86, AI, client, and data center platforms in intelligent computing.",
        "impactZh": "该消息偏生态叙事，需结合具体产品发布、客户采用和 foundry 进展评估。",
        "impactEn": "The item is mostly ecosystem narrative and should be assessed alongside specific product launches, customer adoption, and foundry progress.",
    },
    "Intel 发布 2026 第一季度业绩": {
        "titleZh": "Intel 发布 2026 年第一季度业绩",
        "titleEn": "Intel reports first-quarter 2026 results",
        "summaryEn": "Q1 revenue was $13.6 billion, up 7% year over year; non-GAAP EPS was $0.29; Q2 revenue guidance was $13.8 billion to $14.8 billion.",
    },
    "Intel 发布 2025 全年业绩": {
        "titleZh": "Intel 发布 2025 年全年业绩",
        "titleEn": "Intel reports full-year 2025 results",
        "summaryEn": "FY2025 revenue was $52.9 billion, roughly flat with 2024; Intel Products revenue was $49.1 billion and Intel Foundry revenue was $17.8 billion.",
    },
}

RAW_OVERRIDES = {
    "硅晶圆": {
        "nameEn": "Silicon wafers",
        "usedInEn": "Apple silicon, RF, memory, and sensor chips",
        "riskEn": "Advanced nodes are constrained by wafers, EUV equipment, and foundry capacity.",
    },
    "锂、钴、镍、石墨": {
        "nameEn": "Lithium, cobalt, nickel, and graphite",
        "usedInEn": "Batteries",
        "riskEn": "Battery materials are affected by mineral sourcing, recycling ratios, compliance audits, and price volatility.",
    },
    "稀土、铜、铝、金、锡、钨": {
        "nameEn": "Rare earths, copper, aluminum, gold, tin, and tungsten",
        "usedInEn": "Magnets, enclosures, connectors, circuit boards, and solder",
        "riskEn": "Compliance tracking is complex, while geopolitics and smelting capacity can affect delivery.",
    },
    "高纯硅与先进晶圆": {
        "nameEn": "High-purity silicon and advanced wafers",
        "usedInEn": "GPU, CPU, DPU, and switch chips",
        "riskEn": "Supply is constrained by advanced-node capacity, yield, EUV tools, and packaging schedules.",
    },
    "HBM 相关材料": {
        "nameEn": "HBM-related materials",
        "usedInEn": "AI accelerator memory stacks",
        "riskEn": "HBM suppliers are concentrated; stacking yield and customer qualification cycles can affect delivery.",
    },
    "ABF 基板、铜、化学品、特种气体": {
        "nameEn": "ABF substrates, copper, chemicals, and specialty gases",
        "usedInEn": "Advanced packaging, PCBs, server power, and cooling",
        "riskEn": "AI server demand can push constraints from chips into substrates, power, cooling, and rack systems.",
    },
    "高纯硅晶圆": {
        "nameEn": "High-purity silicon wafers",
        "usedInEn": "CPUs, chiplets, and foundry wafers",
        "riskEn": "Advanced nodes require high-spec wafers and strict defect control; supply quality directly affects yield.",
    },
    "光刻胶、特种气体和湿化学品": {
        "nameEn": "Photoresists, specialty gases, and wet chemicals",
        "usedInEn": "Lithography, etch, clean, and deposition",
        "riskEn": "Supplier concentration and long qualification cycles mean disruptions can affect continuous fab operations.",
    },
    "铜、ABF 树脂、陶瓷和封装材料": {
        "nameEn": "Copper, ABF resin, ceramics, and packaging materials",
        "usedInEn": "Advanced packaging, substrates, interconnects, and thermal management",
        "riskEn": "Advanced packaging expansion raises demand for high-layer-count substrates and thermal materials.",
    },
}


def set_pair(item: dict, field: str, zh: str | None = None, en: str | None = None) -> None:
    base = item.get(field, "")
    if not isinstance(base, str):
        base = ""
    if zh is None:
        zh = ZH_BY_EN.get(base) or TERM_ZH_BY_EN.get(base) or base
    if en is None:
        en = base if not has_cjk(base) else EN_BY_ZH.get(base, base)
    item[f"{field}Zh"] = zh
    item[f"{field}En"] = en


def set_list_pair(item: dict, field: str) -> None:
    values = item.get(field, [])
    if not isinstance(values, list):
        return
    zh_values = []
    en_values = []
    for value in values:
        if not isinstance(value, str):
            continue
        zh_values.append(TERM_ZH_BY_EN.get(value, value))
        en_values.append(value if not has_cjk(value) else EN_BY_ZH.get(value, value))
    item[f"{field}Zh"] = zh_values
    item[f"{field}En"] = en_values


def apply_business(report: dict) -> None:
    for segment in report.get("business", {}).get("segments", []):
        set_pair(segment, "name")
        set_pair(segment, "period")
        set_pair(segment, "note")
    for segment in report.get("financials", {}).get("revenueMix", []):
        set_pair(segment, "name")
        set_pair(segment, "period")
        set_pair(segment, "note")


def apply_financials(report: dict) -> None:
    for metric in report.get("financials", {}).get("highlights", []):
        set_pair(metric, "label")
        set_pair(metric, "period")
        if metric.get("change"):
            set_pair(metric, "change")


def apply_supply_chain(report: dict) -> None:
    for tier in report.get("supplyChain", {}).get("tiers", []):
        set_pair(tier, "title")
        set_pair(tier, "notes")
        set_list_pair(tier, "materials")
        tier_title = tier.get("titleEn") or tier.get("title", "supply-chain tier")
        for entity in tier.get("entities", []):
            set_pair(entity, "relationship")
            services_en = [value for value in entity.get("productsServices", []) if isinstance(value, str)]
            services_zh = [TERM_ZH_BY_EN.get(value, value) for value in services_en]
            entity["productsServicesZh"] = services_zh
            entity["productsServicesEn"] = services_en
            relationship_en = entity.get("relationshipEn", "")
            if not relationship_en or relationship_en == entity.get("relationship") or has_cjk(relationship_en):
                entity["relationshipEn"] = (
                    f"{entity.get('name', 'This entity')} is tracked in the {tier_title} layer for "
                    f"{', '.join(services_en)}. Read the relationship together with the confidence level and cited sources."
                )
            listing = entity.get("listing", {})
            if isinstance(listing, dict) and listing.get("note"):
                set_pair(listing, "note")

    for material in report.get("supplyChain", {}).get("rawMaterials", []):
        overrides = RAW_OVERRIDES.get(material.get("name", ""), {})
        set_pair(material, "name", en=overrides.get("nameEn"))
        set_pair(material, "usedIn", en=overrides.get("usedInEn"))
        set_pair(material, "risk", en=overrides.get("riskEn"))
        set_list_pair(material, "upstream")


def apply_news(report: dict) -> None:
    for item in report.get("news", []):
        override = NEWS_OVERRIDES.get(item.get("title", ""), {})
        set_pair(item, "title", zh=override.get("titleZh"), en=override.get("titleEn"))
        set_pair(item, "category")
        set_pair(item, "summary", zh=override.get("summaryZh"), en=override.get("summaryEn"))
        set_pair(item, "impact", zh=override.get("impactZh"), en=override.get("impactEn"))


def apply_sources(report: dict) -> None:
    for source in report.get("sources", []):
        override = NEWS_OVERRIDES.get(source.get("title", ""), {})
        set_pair(source, "title", zh=override.get("titleZh"), en=override.get("titleEn"))


def main() -> int:
    for path in sorted(COMPANIES_DIR.glob("*.json")):
        report = json.loads(path.read_text(encoding="utf-8"))
        apply_business(report)
        apply_financials(report)
        apply_supply_chain(report)
        apply_news(report)
        apply_sources(report)
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Applied bilingual fields: {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
