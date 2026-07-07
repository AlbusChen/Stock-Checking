import { ArrowRight, ExternalLink, Layers3, LineChart, Network, Target } from "lucide-react";
import { useMemo, useState } from "react";
import type { CompanyIndex, CompanyIndexItem } from "../types/company";

interface IndustryChainMapProps {
  index: CompanyIndex;
  onOpenCompany: (company: CompanyIndexItem) => void;
}

interface ChainLayerConfig {
  id: string;
  stage: string;
  stageEn: string;
  title: string;
  titleEn: string;
  role: string;
  roleEn: string;
  tags: string[];
  keywords: string[];
}

interface ChainCompany {
  company: CompanyIndexItem;
  matchedTerms: string[];
}

const chainLayers: ChainLayerConfig[] = [
  {
    id: "materials",
    stage: "上游 1",
    stageEn: "Upstream 1",
    title: "原材料与耗材",
    titleEn: "Raw materials & consumables",
    role: "特种气体、电子材料、硅晶圆、化学品和关键矿物。",
    roleEn: "Specialty gases, electronic materials, wafers, chemicals, and critical minerals.",
    tags: ["电子材料", "特种气体", "化工材料", "半导体材料"],
    keywords: ["special gas", "materials", "wafer", "chemical", "raw material"],
  },
  {
    id: "equipment",
    stage: "上游 2",
    stageEn: "Upstream 2",
    title: "设备、制造与封测",
    titleEn: "Equipment, fabrication & packaging",
    role: "光刻、刻蚀、沉积、量测、晶圆制造、先进封装和测试。",
    roleEn: "Lithography, etch, deposition, metrology, foundry, advanced packaging, and testing.",
    tags: ["半导体设备", "晶圆制造", "封装测试", "先进封装", "半导体制造"],
    keywords: ["foundry", "equipment", "lithography", "metrology", "packaging", "fab"],
  },
  {
    id: "chips",
    stage: "中游 1",
    stageEn: "Midstream 1",
    title: "核心芯片与存储",
    titleEn: "Core chips & memory",
    role: "GPU、ASIC、CPU、HBM、DRAM、NAND、网络芯片和定制半导体。",
    roleEn: "GPU, ASIC, CPU, HBM, DRAM, NAND, networking chips, and custom silicon.",
    tags: ["GPU", "HBM", "NAND", "存储", "网络芯片", "半导体", "AI芯片"],
    keywords: ["gpu", "hbm", "nand", "dram", "asic", "chip", "semiconductor", "memory"],
  },
  {
    id: "networking",
    stage: "中游 2",
    stageEn: "Midstream 2",
    title: "网络与光互连",
    titleEn: "Networking & optical interconnect",
    role: "交换机、数据中心网络、光模块、光通信、光互连和高速连接。",
    roleEn: "Switching, data-center networking, optical modules, optical links, and high-speed connectivity.",
    tags: ["网络设备", "数据中心网络", "算力网络", "光模块", "光通信", "光互连"],
    keywords: ["network", "optical", "switching", "interconnect", "ethernet", "photonics"],
  },
  {
    id: "power-cooling",
    stage: "中游 3",
    stageEn: "Midstream 3",
    title: "电力、散热与机柜",
    titleEn: "Power, cooling & enclosures",
    role: "数据中心电力、发电/电网、液冷、热管理、机柜和电气连接。",
    roleEn: "Data-center power, generation/grid, liquid cooling, thermal management, racks, and electrical connection.",
    tags: ["电力", "数据中心电力", "电网", "电网建设", "散热", "液冷", "热管理", "机柜", "电气连接"],
    keywords: ["power", "cooling", "thermal", "liquid", "grid", "enclosure", "rack"],
  },
  {
    id: "systems",
    stage: "下游 1",
    stageEn: "Downstream 1",
    title: "整机、终端与系统集成",
    titleEn: "Systems, devices & integration",
    role: "AI 服务器、企业服务器、消费电子终端、终端硬件和系统集成。",
    roleEn: "AI servers, enterprise servers, consumer devices, endpoint hardware, and system integration.",
    tags: ["服务器", "AI服务器", "终端硬件", "消费电子", "系统集成", "电信"],
    keywords: ["server", "device", "consumer electronics", "system integration", "terminal", "endpoint"],
  },
  {
    id: "cloud-compute",
    stage: "下游 2",
    stageEn: "Downstream 2",
    title: "云、算力与运营商",
    titleEn: "Cloud, compute & operators",
    role: "云平台、AI 算力运营、GPU 云、数据库/企业云和通信运营。",
    roleEn: "Cloud platforms, AI compute operators, GPU cloud, database/enterprise cloud, and communications operations.",
    tags: ["云计算", "算力", "GPU云", "电商", "物联网", "卫星通信"],
    keywords: ["cloud", "compute", "operator", "hyperscaler", "gpu cloud", "communications"],
  },
  {
    id: "applications",
    stage: "下游 3",
    stageEn: "Downstream 3",
    title: "应用、太空与场景落地",
    titleEn: "Applications, space & end markets",
    role: "AI 应用、企业软件、自动驾驶、太空、国防、卫星互联网和终端场景。",
    roleEn: "AI applications, enterprise software, autonomous driving, space, defense, satellite internet, and end-market use cases.",
    tags: ["AI应用", "软件服务", "自动驾驶", "太空", "国防", "卫星通信", "直连手机"],
    keywords: ["application", "software", "space", "satellite", "defense", "autonomous", "end market"],
  },
];

function cnQuoteSymbol(ticker: string, exchange: string) {
  const code = ticker.replace(/\D/g, "");
  const normalizedExchange = exchange.toUpperCase();

  if (normalizedExchange.includes("SSE") || code.startsWith("6")) return `sh${code}`;
  if (normalizedExchange.includes("SZSE") || code.startsWith("0") || code.startsWith("3")) return `sz${code}`;
  if (
    normalizedExchange.includes("BSE") ||
    code.startsWith("4") ||
    code.startsWith("8") ||
    code.startsWith("9")
  ) {
    return `bj${code}`;
  }
  return code ? `sh${code}` : ticker.toLowerCase();
}

function quoteHref(company: CompanyIndexItem) {
  if (company.market === "US") {
    return `https://www.nasdaq.com/market-activity/stocks/${encodeURIComponent(company.ticker.toLowerCase())}`;
  }

  return `https://quote.eastmoney.com/${cnQuoteSymbol(company.ticker, company.exchange)}.html`;
}

function companyHaystack(company: CompanyIndexItem) {
  return [
    company.ticker,
    company.name,
    company.legalName,
    company.exchange,
    company.market,
    company.sector,
    company.summary,
    ...company.labels,
    ...company.aliases,
  ]
    .join(" ")
    .toLowerCase();
}

function collectMatchedTerms(company: CompanyIndexItem, layer: ChainLayerConfig) {
  const haystack = companyHaystack(company);
  const tagMatches = layer.tags.filter((tag) => company.labels.includes(tag));
  const keywordMatches = layer.keywords.filter((keyword) => haystack.includes(keyword.toLowerCase()));
  return [...new Set([...tagMatches, ...keywordMatches])];
}

function layerCompanies(index: CompanyIndex, layer: ChainLayerConfig): ChainCompany[] {
  return index.companies
    .map((company) => ({ company, matchedTerms: collectMatchedTerms(company, layer) }))
    .filter(({ matchedTerms }) => matchedTerms.length > 0)
    .sort((a, b) => {
      if (b.matchedTerms.length !== a.matchedTerms.length) return b.matchedTerms.length - a.matchedTerms.length;
      return a.company.ticker.localeCompare(b.company.ticker);
    });
}

export function IndustryChainMap({ index, onOpenCompany }: IndustryChainMapProps) {
  const layers = useMemo(
    () =>
      chainLayers.map((layer) => ({
        ...layer,
        companies: layerCompanies(index, layer),
      })),
    [index],
  );
  const [activeLayerId, setActiveLayerId] = useState(chainLayers[0].id);
  const activeLayer = layers.find((layer) => layer.id === activeLayerId) ?? layers[0];
  const totalLinks = layers.reduce((sum, layer) => sum + layer.companies.length, 0);

  return (
    <section className="chain-panel">
      <header className="chain-header">
        <div>
          <div className="chain-kicker">
            <Network size={16} aria-hidden="true" />
            <span>Industry chain</span>
          </div>
          <h1>产业链图谱</h1>
          <p>从上游材料、设备，到中游芯片、网络、电力，再到下游云、终端和应用，按当前收录公司自动归类。</p>
        </div>
        <div className="chain-stat">
          <Layers3 size={18} aria-hidden="true" />
          <strong>{layers.length}</strong>
          <span>链条层级</span>
          <small>{totalLinks} 个公司映射</small>
        </div>
      </header>

      <div className="chain-flow" aria-label="industry chain from upstream to downstream">
        {layers.map((layer, indexInChain) => (
          <button
            aria-label={`${layer.title} ${layer.companies.length} 家`}
            aria-pressed={activeLayer.id === layer.id}
            className={activeLayer.id === layer.id ? "chain-node active" : "chain-node"}
            data-chain-layer={layer.id}
            key={layer.id}
            onClick={() => setActiveLayerId(layer.id)}
            type="button"
          >
            <span className="chain-stage">
              {layer.stage}
              <small>{layer.stageEn}</small>
            </span>
            <strong>
              {layer.title}
              <small>{layer.titleEn}</small>
            </strong>
            <p>{layer.role}</p>
            <em>{layer.companies.length} 家</em>
            {indexInChain < layers.length - 1 ? <ArrowRight className="chain-arrow" size={17} aria-hidden="true" /> : null}
          </button>
        ))}
      </div>

      <section className="chain-detail">
        <div className="chain-detail-heading">
          <div>
            <span>{activeLayer.stage}</span>
            <h2>{activeLayer.title}</h2>
            <p>{activeLayer.role}</p>
          </div>
          <div className="chain-detail-count">
            <Target size={17} aria-hidden="true" />
            <strong>{activeLayer.companies.length}</strong>
            <span>相关上市企业</span>
          </div>
        </div>

        <div className="chain-company-grid">
          {activeLayer.companies.map(({ company, matchedTerms }) => (
            <article className={`chain-company-card market-${company.market.toLowerCase()}`} key={`${activeLayer.id}-${company.id}`}>
              <button
                aria-label={`${company.ticker} ${company.name}`}
                data-chain-company={company.id}
                onClick={() => onOpenCompany(company)}
                type="button"
              >
                <span>{company.ticker}</span>
                <strong>{company.name}</strong>
                <small>{company.sector}</small>
              </button>
              <div className="chain-company-tags">
                {matchedTerms.slice(0, 4).map((term) => (
                  <em key={`${company.id}-${activeLayer.id}-${term}`}>{term}</em>
                ))}
              </div>
              <div className="chain-company-actions">
                <button aria-label={`打开 ${company.ticker} 详情`} onClick={() => onOpenCompany(company)} type="button">
                  打开详情
                </button>
                <a href={quoteHref(company)} target="_blank" rel="noreferrer">
                  <LineChart size={13} aria-hidden="true" />
                  行情
                  <ExternalLink size={13} aria-hidden="true" />
                </a>
              </div>
            </article>
          ))}
          {activeLayer.companies.length === 0 ? (
            <div className="chain-empty">
              <span>当前层级暂无已收录上市公司</span>
            </div>
          ) : null}
        </div>
      </section>
    </section>
  );
}
