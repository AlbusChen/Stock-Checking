import {
  Activity,
  Building2,
  ExternalLink,
  Factory,
  FileText,
  LineChart,
  Network,
  Newspaper,
  ShieldCheck,
} from "lucide-react";
import { useMemo, useState } from "react";
import type { BusinessSegment, CompanyReport, Source } from "../types/company";
import { MetricStrip } from "./MetricStrip";

interface CompanyDetailProps {
  report: CompanyReport;
}

const tabs = [
  { id: "overview", label: "总览", icon: Building2 },
  { id: "business", label: "业务", icon: Activity },
  { id: "supply", label: "供应链", icon: Network },
  { id: "financials", label: "业绩", icon: LineChart },
  { id: "news", label: "动态", icon: Newspaper },
  { id: "sources", label: "来源", icon: FileText },
] as const;

type TabId = (typeof tabs)[number]["id"];

function sourceLookup(sources: Source[]) {
  return sources.reduce<Record<string, Source>>((acc, source) => {
    acc[source.id] = source;
    return acc;
  }, {});
}

function Evidence({ ids, sources }: { ids: string[]; sources: Record<string, Source> }) {
  const linked = ids.map((id) => sources[id]).filter(Boolean);
  if (linked.length === 0) return null;

  return (
    <div className="evidence">
      {linked.map((source) => (
        <a href={source.url} target="_blank" rel="noreferrer" key={source.id}>
          {source.publisher}
          <ExternalLink size={13} aria-hidden="true" />
        </a>
      ))}
    </div>
  );
}

function SegmentBars({ segments, sources }: { segments: BusinessSegment[]; sources: Record<string, Source> }) {
  const maxRevenue = Math.max(...segments.map((segment) => segment.revenue ?? 0), 1);

  return (
    <div className="bars">
      {segments.map((segment) => (
        <div className="bar-row" key={segment.name}>
          <div className="bar-label">
            <span>{segment.name}</span>
            <strong>
              {segment.revenue ? `$${segment.revenue.toLocaleString("en-US")}B` : "n/a"}
            </strong>
          </div>
          <div className="bar-track">
            <div className="bar-fill" style={{ width: `${((segment.revenue ?? 0) / maxRevenue) * 100}%` }} />
          </div>
          <p>{segment.note}</p>
          <Evidence ids={segment.sourceIds} sources={sources} />
        </div>
      ))}
    </div>
  );
}

export function CompanyDetail({ report }: CompanyDetailProps) {
  const [activeTab, setActiveTab] = useState<TabId>("overview");
  const sources = useMemo(() => sourceLookup(report.sources), [report.sources]);

  return (
    <section className="company-panel">
      <header className="company-header">
        <div>
          <div className="ticker-line">
            <span className="ticker">{report.ticker}</span>
            <span>{report.exchange}</span>
            <span>{report.market}</span>
          </div>
          <h1>{report.name}</h1>
          <p>{report.summary}</p>
        </div>
        <div className="freshness">
          <ShieldCheck size={18} aria-hidden="true" />
          <span>更新 {new Date(report.lastUpdated).toLocaleDateString("zh-CN")}</span>
        </div>
      </header>

      <MetricStrip metrics={report.financials.highlights} />

      <nav className="tabs" aria-label="company sections">
        {tabs.map(({ id, label, icon: Icon }) => (
          <button
            className={activeTab === id ? "tab active" : "tab"}
            key={id}
            onClick={() => setActiveTab(id)}
            title={label}
            type="button"
          >
            <Icon size={16} aria-hidden="true" />
            <span>{label}</span>
          </button>
        ))}
      </nav>

      {activeTab === "overview" && (
        <div className="section-grid">
          <article className="info-card wide">
            <h2>判断摘要</h2>
            <p>{report.business.thesis}</p>
          </article>
          <article className="info-card">
            <h2>更新频率</h2>
            <dl className="cadence">
              {Object.entries(report.updateCadence).map(([key, value]) => (
                <div key={key}>
                  <dt>{key}</dt>
                  <dd>{value}</dd>
                </div>
              ))}
            </dl>
          </article>
          <article className="info-card">
            <h2>风险提醒</h2>
            <ul className="clean-list">
              {report.business.riskNotes.map((risk) => (
                <li key={risk}>{risk}</li>
              ))}
            </ul>
          </article>
        </div>
      )}

      {activeTab === "business" && (
        <div className="content-stack">
          <article className="info-card wide">
            <h2>主营业务</h2>
            <p>{report.business.description}</p>
            <div className="pill-row">
              {report.business.revenueModel.map((item) => (
                <span className="pill" key={item}>
                  {item}
                </span>
              ))}
            </div>
          </article>
          <article className="info-card wide">
            <h2>收入结构</h2>
            <SegmentBars segments={report.financials.revenueMix} sources={sources} />
          </article>
        </div>
      )}

      {activeTab === "supply" && (
        <div className="content-stack">
          <article className="info-card wide">
            <h2>溯源结论</h2>
            <p>{report.supplyChain.thesis}</p>
          </article>
          <div className="tier-list">
            {report.supplyChain.tiers.map((tier) => (
              <article className="tier-card" key={`${tier.level}-${tier.title}`}>
                <div className="tier-top">
                  <span>Tier {tier.level}</span>
                  <strong>{tier.title}</strong>
                  <em>{tier.confidence}</em>
                </div>
                <p>{tier.notes}</p>
                <div className="pill-row compact">
                  {tier.companies.map((company) => (
                    <span className="pill" key={company}>
                      <Factory size={13} aria-hidden="true" />
                      {company}
                    </span>
                  ))}
                </div>
                <div className="subline">{tier.materials.join(" / ")}</div>
                <Evidence ids={tier.sourceIds} sources={sources} />
              </article>
            ))}
          </div>
          <article className="info-card wide">
            <h2>原材料层</h2>
            <div className="raw-grid">
              {report.supplyChain.rawMaterials.map((material) => (
                <div className="raw-item" key={material.name}>
                  <strong>{material.name}</strong>
                  <span>{material.usedIn}</span>
                  <p>{material.risk}</p>
                </div>
              ))}
            </div>
          </article>
        </div>
      )}

      {activeTab === "financials" && (
        <div className="content-stack">
          <article className="info-card wide">
            <h2>{report.financials.latestPeriod}</h2>
            <div className="metric-list">
              {report.financials.highlights.map((metric) => (
                <div className="metric-row" key={`${metric.label}-${metric.period}`}>
                  <span>{metric.label}</span>
                  <strong>
                    {metric.unit === "USD billions" ? "$" : ""}
                    {metric.value.toLocaleString("en-US")}
                    {metric.unit === "USD billions" ? "B" : metric.unit === "percent" ? "%" : ""}
                  </strong>
                  <small>{metric.change}</small>
                  <Evidence ids={metric.sourceIds} sources={sources} />
                </div>
              ))}
            </div>
          </article>
          <article className="info-card wide">
            <h2>收入构成</h2>
            <SegmentBars segments={report.financials.revenueMix} sources={sources} />
          </article>
        </div>
      )}

      {activeTab === "news" && (
        <div className="timeline">
          {report.news.map((item) => (
            <article className="news-item" key={`${item.date}-${item.title}`}>
              <time>{item.date}</time>
              <div>
                <span className="category">{item.category}</span>
                <h2>{item.title}</h2>
                <p>{item.summary}</p>
                <strong>{item.impact}</strong>
                <Evidence ids={item.sourceIds} sources={sources} />
              </div>
            </article>
          ))}
        </div>
      )}

      {activeTab === "sources" && (
        <div className="source-list">
          {report.sources.map((source) => (
            <a className="source-card" href={source.url} target="_blank" rel="noreferrer" key={source.id}>
              <span>{source.type}</span>
              <strong>{source.title}</strong>
              <small>
                {source.publisher}
                {source.publishedAt ? ` · ${source.publishedAt}` : ""}
              </small>
              <ExternalLink size={16} aria-hidden="true" />
            </a>
          ))}
        </div>
      )}
    </section>
  );
}
