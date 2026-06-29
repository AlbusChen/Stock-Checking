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
import { formatFinancialValue } from "../lib/format";
import { combineLocalized, localizedField, localizedList } from "../lib/localization";
import type {
  BusinessSegment,
  CompanyReport,
  DownstreamChain,
  FailureCondition,
  RelationshipStrength,
  ScarceLayer,
  Source,
  SupplierListing,
  ThemeExposure,
} from "../types/company";
import { FinancialTrendCharts } from "./FinancialTrendCharts";
import { MetricStrip } from "./MetricStrip";
import { TextPair } from "./TextPair";

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

function evidenceLevelLabel(source: Source) {
  const level = source.evidenceLevel;
  if (source.evidenceLevelZh && source.evidenceLevelEn) {
    return { zh: source.evidenceLevelZh, en: source.evidenceLevelEn };
  }
  if (level === "strong") return { zh: "强证据", en: "Strong" };
  if (level === "medium") return { zh: "中证据", en: "Medium" };
  if (level === "weak") return { zh: "弱证据", en: "Weak" };
  return { zh: "待核验", en: "Needs check" };
}

function evidenceClass(level?: Source["evidenceLevel"]) {
  if (level === "strong") return "evidence-strong";
  if (level === "medium") return "evidence-medium";
  if (level === "weak") return "evidence-weak";
  return "evidence-needs-checking";
}

function evidenceLevelText(level?: Source["evidenceLevel"]) {
  if (level === "strong") return { zh: "强证据", en: "strong" };
  if (level === "medium") return { zh: "中证据", en: "medium" };
  if (level === "weak") return { zh: "弱证据", en: "weak" };
  return { zh: "待核验", en: "needs checking" };
}

function Evidence({ ids, sources }: { ids: string[]; sources: Record<string, Source> }) {
  const linked = ids.map((id) => sources[id]).filter(Boolean);
  if (linked.length === 0) return null;

  return (
    <div className="evidence">
      {linked.map((source) => (
        <a
          className={evidenceClass(source.evidenceLevel)}
          href={source.url}
          target="_blank"
          rel="noreferrer"
          key={source.id}
          title={`${source.type} · ${evidenceLevelLabel(source).zh}`}
        >
          {source.publisher}
          <TextPair text={evidenceLevelLabel(source)} />
          <ExternalLink size={13} aria-hidden="true" />
        </a>
      ))}
    </div>
  );
}

function FailureConditionsPanel({
  conditions = [],
  sources,
}: {
  conditions?: FailureCondition[];
  sources: Record<string, Source>;
}) {
  if (conditions.length === 0) return null;

  return (
    <article className="info-card wide failure-panel">
      <h2>什么情况说明判断错了</h2>
      <div className="failure-list">
        {conditions.map((condition, index) => (
          <section className="failure-item" key={`${condition.condition}-${index}`}>
            <strong>
              <TextPair text={localizedField(condition, "condition")} />
            </strong>
            <p>
              <TextPair text={localizedField(condition, "monitor")} />
            </p>
            <Evidence ids={condition.sourceIds ?? []} sources={sources} />
          </section>
        ))}
      </div>
    </article>
  );
}

function ScarceLayersPanel({
  layers = [],
  sources,
}: {
  layers?: ScarceLayer[];
  sources: Record<string, Source>;
}) {
  if (layers.length === 0) return null;

  const sortedLayers = [...layers].sort((a, b) => a.rank - b.rank);

  return (
    <article className="info-card wide scarce-layer-panel">
      <h2>产业链卡点排序</h2>
      <div className="scarce-layer-list">
        {sortedLayers.map((layer) => (
          <section className="scarce-layer-item" key={`${layer.rank}-${layer.name}`}>
            <div className="scarce-layer-top">
              <span>#{layer.rank}</span>
              <strong>
                <TextPair text={localizedField(layer, "name")} />
              </strong>
              <em className={`evidence-pill ${evidenceClass(layer.evidenceLevel)}`}>
                <TextPair text={evidenceLevelText(layer.evidenceLevel)} />
              </em>
            </div>
            <p>
              <TextPair text={localizedField(layer, "whyScarce")} />
            </p>
            <div className="pill-row compact">
              <span className="pill">
                <TextPair text={localizedField(layer, "constraintType")} />
              </span>
              {layer.relatedCompanies.map((company) => (
                <span className="pill" key={`${layer.name}-${company}`}>
                  {company}
                </span>
              ))}
            </div>
            {layer.failureConditions.length > 0 ? (
              <div className="layer-failure">
                <strong>证伪观察</strong>
                {layer.failureConditions.map((condition, index) => (
                  <p key={`${layer.name}-failure-${index}`}>
                    <TextPair text={localizedField(condition, "condition")} />
                  </p>
                ))}
              </div>
            ) : null}
            <Evidence ids={layer.sourceIds} sources={sources} />
          </section>
        ))}
      </div>
    </article>
  );
}

function SegmentBars({ segments, sources }: { segments: BusinessSegment[]; sources: Record<string, Source> }) {
  const maxRevenue = Math.max(...segments.map((segment) => segment.revenue ?? 0), 1);

  return (
    <div className="bars">
      {segments.map((segment) => (
        <div className="bar-row" key={segment.name}>
          <div className="bar-label">
            <TextPair text={localizedField(segment, "name")} />
            <strong>
              {segment.revenue && segment.unit ? formatFinancialValue(segment.revenue, segment.unit) : "n/a"}
            </strong>
          </div>
          <div className="bar-track">
            <div className="bar-fill" style={{ width: `${((segment.revenue ?? 0) / maxRevenue) * 100}%` }} />
          </div>
          <p>
            <TextPair text={localizedField(segment, "note")} />
          </p>
          <Evidence ids={segment.sourceIds} sources={sources} />
        </div>
      ))}
    </div>
  );
}

function listingText(listing: SupplierListing) {
  if (listing.status === "listed" && listing.ticker && listing.exchange) {
    return `${listing.exchange} ${listing.ticker}`;
  }
  if (listing.status === "listed-parent" && listing.parentTicker && listing.parentExchange) {
    return `${listing.parentExchange} ${listing.parentTicker}`;
  }
  if (listing.status === "delisted") {
    return listing.formerTicker ? `已退市 ${listing.formerTicker}` : "已退市";
  }
  if (listing.status === "private") return "未上市";
  return "上市状态待确认";
}

function listingHref(listing: SupplierListing) {
  if (listing.status === "listed") return listing.stockUrl;
  if (listing.status === "listed-parent") return listing.parentStockUrl;
  return undefined;
}

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

function quoteHref(report: CompanyReport) {
  if (report.market === "US") {
    return `https://www.nasdaq.com/market-activity/stocks/${encodeURIComponent(report.ticker.toLowerCase())}`;
  }

  return `https://quote.eastmoney.com/${cnQuoteSymbol(report.ticker, report.exchange)}.html`;
}

function strengthClass(score: number) {
  if (score >= 5) return "strength-5";
  if (score >= 4) return "strength-4";
  if (score >= 3) return "strength-3";
  if (score >= 2) return "strength-2";
  return "strength-1";
}

function RelationshipStrengthBadge({ strength }: { strength?: RelationshipStrength }) {
  if (!strength) return null;

  return (
    <div className={`relationship-strength ${strengthClass(strength.score)}`}>
      <strong>
        <TextPair text={localizedField(strength, "label")} />
      </strong>
      <span>{strength.score}/5</span>
    </div>
  );
}

function RelationshipStrengthNote({ strength }: { strength?: RelationshipStrength }) {
  if (!strength) return null;

  return (
    <div className="strength-note">
      <p>
        <TextPair text={localizedField(strength, "rationale")} />
      </p>
    </div>
  );
}

function ThemeExposureStrip({ exposures = [] }: { exposures?: ThemeExposure[] }) {
  if (exposures.length === 0) return null;

  return (
    <div className="theme-exposure-strip" aria-label="theme exposure">
      {exposures.map((exposure) => (
        <div className={`theme-exposure-chip ${strengthClass(exposure.score)}`} key={exposure.theme}>
          <span>
            <TextPair text={localizedField(exposure, "theme")} />
          </span>
          <strong>
            <TextPair text={localizedField(exposure, "role")} />
          </strong>
          <em>{exposure.score}/5</em>
        </div>
      ))}
    </div>
  );
}

function ThemeExposurePanel({ exposures = [] }: { exposures?: ThemeExposure[] }) {
  if (exposures.length === 0) return null;

  return (
    <article className="info-card wide exposure-panel">
      <h2>相关性提示</h2>
      <div className="exposure-list">
        {exposures.map((exposure) => (
          <section className={`exposure-item ${strengthClass(exposure.score)}`} key={exposure.theme}>
            <div>
              <span>
                <TextPair text={localizedField(exposure, "theme")} />
              </span>
              <strong>
                <TextPair text={localizedField(exposure, "role")} />
              </strong>
            </div>
            <em>{exposure.score}/5</em>
            <p>
              <TextPair text={localizedField(exposure, "rationale")} />
            </p>
          </section>
        ))}
      </div>
    </article>
  );
}

function DownstreamPanel({
  downstream,
  sources,
}: {
  downstream?: DownstreamChain;
  sources: Record<string, Source>;
}) {
  if (!downstream) return null;

  return (
    <article className="info-card wide downstream-panel">
      <h2>下游客户与应用去向</h2>
      <p>
        <TextPair text={localizedField(downstream, "thesis")} />
      </p>
      <div className="downstream-list">
        {downstream.tiers.map((tier) => (
          <section className="downstream-tier" key={`${tier.level}-${tier.title}`}>
            <div className="tier-top">
              <span>Downstream {tier.level}</span>
              <strong>
                <TextPair text={localizedField(tier, "title")} />
              </strong>
              <em>{tier.confidence}</em>
            </div>
            <p>
              <TextPair text={localizedField(tier, "notes")} />
            </p>
            <div className="supplier-list">
              {tier.entities.map((entity) => {
                const href = listingHref(entity.listing);
                return (
                  <div className="supplier-row" key={`${tier.title}-${entity.name}`}>
                    <div className="supplier-main">
                      <div className="supplier-name">
                        <TextPair text={localizedField(entity, "name")} />
                      </div>
                      <span className="customer-role">
                        <TextPair text={localizedField(entity, "customerRole")} />
                      </span>
                      {href ? (
                        <a className="listing-link" href={href} target="_blank" rel="noreferrer">
                          {listingText(entity.listing)}
                          <ExternalLink size={13} aria-hidden="true" />
                        </a>
                      ) : (
                        <span className="listing-status">{listingText(entity.listing)}</span>
                      )}
                      <RelationshipStrengthBadge strength={entity.relationshipStrength} />
                    </div>
                    <div className="supplier-detail">
                      <p>
                        <TextPair text={localizedField(entity, "relationship")} />
                      </p>
                      <RelationshipStrengthNote strength={entity.relationshipStrength} />
                      <div className="supplier-tags">
                        {localizedList(entity, "productsServices").map((item) => (
                          <span className="pill" key={`${entity.name}-${item.zh}`}>
                            <Factory size={13} aria-hidden="true" />
                            <TextPair text={item} />
                          </span>
                        ))}
                      </div>
                      <div className="supplier-links">
                        {entity.companyUrl ? (
                          <a href={entity.companyUrl} target="_blank" rel="noreferrer">
                            公司
                            <ExternalLink size={13} aria-hidden="true" />
                          </a>
                        ) : null}
                        <span>{entity.confidence}</span>
                      </div>
                      <Evidence ids={entity.sourceIds} sources={sources} />
                    </div>
                  </div>
                );
              })}
            </div>
            <Evidence ids={tier.sourceIds} sources={sources} />
          </section>
        ))}
      </div>
    </article>
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
            <a
              aria-label={`${report.ticker} 实时行情 / Live quote`}
              className="quote-link"
              href={quoteHref(report)}
              target="_blank"
              rel="noreferrer"
            >
              <LineChart size={13} aria-hidden="true" />
              <TextPair text={{ zh: "实时行情", en: "Live quote" }} />
              <ExternalLink size={13} aria-hidden="true" />
            </a>
          </div>
          <h1>{report.name}</h1>
          <div className="detail-labels" aria-label="company labels">
            {report.labels.map((label) => (
              <span key={`${report.id}-${label}`}>{label}</span>
            ))}
          </div>
          <p>{report.summary}</p>
          <ThemeExposureStrip exposures={report.themeExposure} />
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
          <ThemeExposurePanel exposures={report.themeExposure} />
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
          <FailureConditionsPanel conditions={report.business.failureConditions} sources={sources} />
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
          <ScarceLayersPanel layers={report.supplyChain.scarceLayers} sources={sources} />
          <div className="tier-list">
            {report.supplyChain.tiers.map((tier) => (
              <article className="tier-card" key={`${tier.level}-${tier.title}`}>
                <div className="tier-top">
                  <span>Tier {tier.level}</span>
                  <strong>
                    <TextPair text={localizedField(tier, "title")} />
                  </strong>
                  <em>{tier.confidence}</em>
                </div>
                <p>
                  <TextPair text={localizedField(tier, "notes")} />
                </p>
                <div className="supplier-list">
                  {tier.entities.map((entity) => {
                    const href = listingHref(entity.listing);
                    return (
                      <div className="supplier-row" key={entity.name}>
                        <div className="supplier-main">
                          <div className="supplier-name">
                            <TextPair text={localizedField(entity, "name")} />
                          </div>
                          {href ? (
                            <a className="listing-link" href={href} target="_blank" rel="noreferrer">
                              {listingText(entity.listing)}
                              <ExternalLink size={13} aria-hidden="true" />
                            </a>
                          ) : (
                            <span className="listing-status">{listingText(entity.listing)}</span>
                          )}
                          {entity.listing.note ? (
                            <TextPair className="listing-note" text={localizedField(entity.listing, "note")} />
                          ) : null}
                          <RelationshipStrengthBadge strength={entity.relationshipStrength} />
                        </div>
                        <div className="supplier-detail">
                          <p>
                            <TextPair text={localizedField(entity, "relationship")} />
                          </p>
                          <RelationshipStrengthNote strength={entity.relationshipStrength} />
                          <div className="supplier-tags">
                            {localizedList(entity, "productsServices").map((item) => (
                              <span className="pill" key={`${entity.name}-${item.zh}`}>
                                <Factory size={13} aria-hidden="true" />
                                <TextPair text={item} />
                              </span>
                            ))}
                          </div>
                          <div className="supplier-links">
                            {entity.companyUrl ? (
                              <a href={entity.companyUrl} target="_blank" rel="noreferrer">
                                公司
                                <ExternalLink size={13} aria-hidden="true" />
                              </a>
                            ) : null}
                            <span>{entity.confidence}</span>
                          </div>
                          <Evidence ids={entity.sourceIds} sources={sources} />
                        </div>
                      </div>
                    );
                  })}
                </div>
                <div className="subline">
                  <TextPair
                    text={{
                      zh: localizedList(tier, "materials")
                        .map((item) => item.zh)
                        .join(" / "),
                      en: localizedList(tier, "materials")
                        .map((item) => item.en)
                        .filter(Boolean)
                        .join(" / "),
                    }}
                  />
                </div>
                <Evidence ids={tier.sourceIds} sources={sources} />
              </article>
            ))}
          </div>
          <article className="info-card wide">
            <h2>原材料层</h2>
            <div className="raw-grid">
              {report.supplyChain.rawMaterials.map((material) => (
                <div className="raw-item" key={material.name}>
                  <strong>
                    <TextPair text={localizedField(material, "name")} />
                  </strong>
                  <span>
                    <TextPair text={localizedField(material, "usedIn")} />
                  </span>
                  <p>
                    <TextPair text={localizedField(material, "risk")} />
                  </p>
                  <small>
                    <TextPair
                      text={{
                        zh: `上游：${localizedList(material, "upstream")
                          .map((item) => item.zh)
                          .join(" / ")}`,
                        en: `Upstream: ${localizedList(material, "upstream")
                          .map((item) => item.en)
                          .filter(Boolean)
                          .join(" / ")}`,
                      }}
                    />
                  </small>
                </div>
              ))}
            </div>
          </article>
          <DownstreamPanel downstream={report.supplyChain.downstream} sources={sources} />
        </div>
      )}

      {activeTab === "financials" && (
        <div className="content-stack">
          <article className="info-card wide">
            <h2>
              <TextPair text={localizedField(report.financials, "latestPeriod")} />
            </h2>
            <div className="metric-list">
              {report.financials.highlights.map((metric) => (
                <div className="metric-row" key={`${metric.label}-${metric.period}`}>
                  <TextPair text={localizedField(metric, "label")} />
                  <strong>{formatFinancialValue(metric.value, metric.unit)}</strong>
                  <TextPair
                    className="metric-context"
                    text={combineLocalized(
                      [localizedField(metric, "period"), metric.change ? localizedField(metric, "change") : null].filter(
                        Boolean,
                      ) as ReturnType<typeof localizedField>[],
                    )}
                  />
                  <Evidence ids={metric.sourceIds} sources={sources} />
                </div>
              ))}
            </div>
          </article>
          <FinancialTrendCharts
            revenueMixHistory={report.financials.revenueMixHistory}
            sources={sources}
            trends={report.financials.trends}
          />
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
                <span className="category">
                  <TextPair text={localizedField(item, "category")} />
                </span>
                <h2>
                  <TextPair text={localizedField(item, "title")} />
                </h2>
                <p>
                  <TextPair text={localizedField(item, "summary")} />
                </p>
                <strong>
                  <TextPair text={localizedField(item, "impact")} />
                </strong>
                <Evidence ids={item.sourceIds} sources={sources} />
              </div>
            </article>
          ))}
        </div>
      )}

      {activeTab === "sources" && (
        <div className="source-list">
          {report.sources.map((source) => (
            <a
              className={`source-card ${evidenceClass(source.evidenceLevel)}`}
              href={source.url}
              target="_blank"
              rel="noreferrer"
              key={source.id}
            >
              <span>
                {source.type}
                <TextPair text={evidenceLevelLabel(source)} />
              </span>
              <strong>
                <TextPair text={localizedField(source, "title")} />
              </strong>
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
