import {
  AlertCircle,
  BarChart3,
  CalendarDays,
  ExternalLink,
  FileText,
  Gauge,
  Info,
  LineChart,
  Loader2,
  Newspaper,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { loadVolumeBreakouts } from "../lib/data";
import type {
  VolumeBreakoutProviderStatus,
  VolumeBreakoutReport,
  VolumeBreakoutStock,
  VolumeBreakoutWindow,
} from "../types/volumeBreakout";

function formatPercent(value: number) {
  return `${value.toLocaleString("zh-CN", {
    maximumFractionDigits: 2,
    minimumFractionDigits: 2,
  })}%`;
}

function formatPrice(value: number) {
  return value.toLocaleString("zh-CN", {
    maximumFractionDigits: 2,
    minimumFractionDigits: 2,
  });
}

function formatAmount(value: number) {
  if (Math.abs(value) >= 100_000_000) {
    return `${(value / 100_000_000).toLocaleString("zh-CN", {
      maximumFractionDigits: 2,
      minimumFractionDigits: 2,
    })} 亿`;
  }
  if (Math.abs(value) >= 10_000) {
    return `${(value / 10_000).toLocaleString("zh-CN", {
      maximumFractionDigits: 0,
    })} 万`;
  }
  return value.toLocaleString("zh-CN", { maximumFractionDigits: 0 });
}

function formatShares(value: number) {
  if (Math.abs(value) >= 100_000_000) {
    return `${(value / 100_000_000).toLocaleString("zh-CN", {
      maximumFractionDigits: 2,
    })} 亿手`;
  }
  if (Math.abs(value) >= 10_000) {
    return `${(value / 10_000).toLocaleString("zh-CN", {
      maximumFractionDigits: 2,
    })} 万手`;
  }
  return `${value.toLocaleString("zh-CN", { maximumFractionDigits: 0 })} 手`;
}

function marketLabel(exchange: string) {
  if (exchange === "SSE") return "上交所 / SSE";
  if (exchange === "SZSE") return "深交所 / SZSE";
  if (exchange === "BSE") return "北交所 / BSE";
  return "A股 / A-share";
}

function WindowSummary({ activeWindow, report }: { activeWindow: VolumeBreakoutWindow; report: VolumeBreakoutReport }) {
  const topVolumeRatio = activeWindow.stocks[0]?.volumeRatio ?? 0;
  const averageBreakout =
    activeWindow.stocks.length > 0
      ? activeWindow.stocks.reduce((sum, stock) => sum + stock.breakoutPct, 0) / activeWindow.stocks.length
      : 0;

  return (
    <div className="breakout-summary-grid">
      <div className="breakout-summary-item">
        <span>入选数量</span>
        <small>Qualified names</small>
        <strong>{activeWindow.stocks.length}</strong>
      </div>
      <div className="breakout-summary-item">
        <span>交易日期</span>
        <small>Trade date</small>
        <strong>{report.tradeDate}</strong>
      </div>
      <div className="breakout-summary-item">
        <span>最高量比</span>
        <small>Top volume ratio</small>
        <strong>{topVolumeRatio.toFixed(2)}x</strong>
      </div>
      <div className="breakout-summary-item">
        <span>平均突破幅度</span>
        <small>Avg breakout</small>
        <strong>{formatPercent(averageBreakout)}</strong>
      </div>
    </div>
  );
}

function StockMetrics({ stock }: { stock: VolumeBreakoutStock }) {
  const metrics = [
    {
      labelZh: "收盘价",
      labelEn: "Close",
      value: `¥${formatPrice(stock.close)}`,
    },
    {
      labelZh: "涨跌幅",
      labelEn: "Change",
      value: formatPercent(stock.pctChange),
      className: stock.pctChange >= 0 ? "positive" : "negative",
    },
    {
      labelZh: "突破幅度",
      labelEn: "Breakout",
      value: formatPercent(stock.breakoutPct),
      className: "positive",
    },
    {
      labelZh: "量比",
      labelEn: "Volume ratio",
      value: `${stock.volumeRatio.toFixed(2)}x`,
    },
    {
      labelZh: "成交额",
      labelEn: "Turnover value",
      value: `¥${formatAmount(stock.amountCny)}`,
    },
    {
      labelZh: "换手率",
      labelEn: "Turnover rate",
      value: stock.turnoverRate === undefined ? "n/a" : formatPercent(stock.turnoverRate),
    },
  ];

  return (
    <div className="breakout-metrics">
      {metrics.map((metric) => (
        <div className={metric.className ? `breakout-metric ${metric.className}` : "breakout-metric"} key={metric.labelEn}>
          <span>{metric.labelZh}</span>
          <small>{metric.labelEn}</small>
          <strong>{metric.value}</strong>
        </div>
      ))}
    </div>
  );
}

function ProviderStatusList({ providers = [] }: { providers?: VolumeBreakoutProviderStatus[] }) {
  if (providers.length === 0) return null;

  return (
    <div className="breakout-provider-list">
      {providers.map((provider) => (
        <div className={`breakout-provider-item status-${provider.status}`} key={provider.id}>
          <span>{provider.nameZh}</span>
          <small>{provider.nameEn}</small>
          <strong>{provider.count}</strong>
          <em>{provider.status}</em>
          <p>{provider.noteZh}</p>
        </div>
      ))}
    </div>
  );
}

function ExternalSignals({ stock }: { stock: VolumeBreakoutStock }) {
  const signals = stock.externalSignals ?? [];
  if (signals.length === 0 && !stock.candidateSources?.length) return null;

  return (
    <div className="breakout-source-signal">
      {stock.candidateSources?.length ? (
        <div className="breakout-source-chips">
          {stock.candidateSources.map((source) => (
            <span key={`${stock.code}-${source}`}>{source}</span>
          ))}
        </div>
      ) : null}
      {signals.map((signal) => (
        <div className="breakout-signal-block" key={`${stock.code}-${signal.sourceEn}`}>
          <strong>
            {signal.sourceZh}
            <small>{signal.sourceEn}</small>
          </strong>
          <p>{signal.noteZh}</p>
          <div>
            {signal.signals.slice(0, 8).map((item) => (
              <span key={`${stock.code}-${signal.sourceEn}-${item}`}>{item}</span>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

function FundamentalCatalysts({ stock }: { stock: VolumeBreakoutStock }) {
  const catalysts = stock.fundamentalCatalysts ?? [];

  return (
    <section className={`breakout-catalysts status-${stock.fundamentalCatalystStatus ?? "not-found"}`}>
      <div className="breakout-catalyst-heading">
        <Newspaper size={16} aria-hidden="true" />
        <div>
          <strong>基本面/消息催化</strong>
          <small>Fundamental and news catalysts</small>
        </div>
      </div>
      <p>{stock.fundamentalSummaryZh ?? "未找到可核验的基本面催化。"}</p>
      {stock.fundamentalSummaryEn ? <p className="breakout-catalyst-en">{stock.fundamentalSummaryEn}</p> : null}
      {catalysts.length > 0 ? (
        <div className="breakout-catalyst-list">
          {catalysts.map((catalyst) => (
            <a
              className={`breakout-catalyst-card confidence-${catalyst.confidence}`}
              href={catalyst.url}
              key={`${stock.code}-${catalyst.date}-${catalyst.title}`}
              target="_blank"
              rel="noreferrer"
            >
              <span>
                {catalyst.sourceType === "announcement" ? <FileText size={14} aria-hidden="true" /> : <Newspaper size={14} aria-hidden="true" />}
                {catalyst.sourceNameZh}
                <small>{catalyst.date}</small>
              </span>
              <strong>{catalyst.title}</strong>
              <em>
                {catalyst.catalystTypeZh} · {catalyst.confidenceZh}
              </em>
              <small>{catalyst.catalystTypeEn} · {catalyst.confidenceEn}</small>
              <ExternalLink size={13} aria-hidden="true" />
            </a>
          ))}
        </div>
      ) : null}
    </section>
  );
}

function StockCard({ stock }: { stock: VolumeBreakoutStock }) {
  return (
    <article className="breakout-stock-card">
      <header className="breakout-stock-top">
        <div className="breakout-stock-title">
          <span>{stock.code}</span>
          <strong>{stock.name}</strong>
          <small>
            {marketLabel(stock.exchange)}
            {stock.industry ? ` · ${stock.industry}` : ""}
          </small>
        </div>
        <a className="quote-link breakout-quote-link" href={stock.quoteUrl} target="_blank" rel="noreferrer">
          <LineChart size={14} aria-hidden="true" />
          <span>行情</span>
          <small>Quote</small>
          <ExternalLink size={13} aria-hidden="true" />
        </a>
      </header>

      <ExternalSignals stock={stock} />

      <StockMetrics stock={stock} />

      <FundamentalCatalysts stock={stock} />

      <div className="breakout-reason">
        <div>
          <strong>量价确认</strong>
          <small>Price-volume confirmation</small>
        </div>
        <p>{stock.reasonZh}</p>
        <p className="breakout-reason-en">{stock.reasonEn}</p>
      </div>

      <div className="breakout-factor-grid">
        {stock.factors.map((factor) => (
          <div className="breakout-factor" key={`${stock.code}-${factor.labelEn}`}>
            <span>{factor.labelZh}</span>
            <small>{factor.labelEn}</small>
            <strong>{factor.valueZh}</strong>
            <em>{factor.valueEn}</em>
          </div>
        ))}
      </div>

      <div className="breakout-tags">
        {stock.tags.map((tag) => (
          <span key={`${stock.code}-${tag}`}>{tag}</span>
        ))}
      </div>
    </article>
  );
}

export function VolumeBreakouts() {
  const [report, setReport] = useState<VolumeBreakoutReport | null>(null);
  const [activeDays, setActiveDays] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    loadVolumeBreakouts()
      .then((payload) => {
        if (!active) return;
        setReport(payload);
        setActiveDays(payload.windows[0]?.days ?? null);
      })
      .catch((err: unknown) => {
        if (!active) return;
        setError(err instanceof Error ? err.message : "Breakout data load failed");
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, []);

  const activeWindow = useMemo(() => {
    if (!report) return null;
    return report.windows.find((window) => window.days === activeDays) ?? report.windows[0] ?? null;
  }, [activeDays, report]);

  if (loading) {
    return (
      <div className="loading-panel">
        <Loader2 className="spin" size={22} aria-hidden="true" />
        <span>加载放量突破数据</span>
      </div>
    );
  }

  if (error || !report || !activeWindow) {
    return (
      <div className="loading-panel">
        <AlertCircle size={22} aria-hidden="true" />
        <span>{error ?? "未生成放量突破数据"}</span>
      </div>
    );
  }

  return (
    <section className="breakout-panel">
      <header className="breakout-header">
        <div>
          <div className="section-kicker">
            <BarChart3 size={16} aria-hidden="true" />
            <span>A股量价扫描 / A-share breakout scan</span>
          </div>
          <h1>放量突破</h1>
          <p>
            先用量价条件筛出放量突破股票，再用公开公告、新闻标题和行业线索提示可能的基本面催化；没有可靠消息时会明确标注继续核验。
          </p>
        </div>
        <div className="breakout-freshness">
          <CalendarDays size={18} aria-hidden="true" />
          <span>{new Date(report.generatedAt).toLocaleString("zh-CN")}</span>
          <small>Generated</small>
        </div>
      </header>

      <nav className="breakout-window-tabs" aria-label="breakout time windows">
        {report.windows.map((window) => (
          <button
            className={window.days === activeWindow.days ? "breakout-window-tab active" : "breakout-window-tab"}
            key={window.days}
            onClick={() => setActiveDays(window.days)}
            type="button"
          >
            <strong>{window.labelZh}</strong>
            <small>{window.labelEn}</small>
            <span>{window.stocks.length}</span>
          </button>
        ))}
      </nav>

      <WindowSummary activeWindow={activeWindow} report={report} />

      <article className="breakout-criteria-card">
        <div className="breakout-criteria-title">
          <Gauge size={17} aria-hidden="true" />
          <div>
            <strong>{activeWindow.descriptionZh}</strong>
            <small>{activeWindow.descriptionEn}</small>
          </div>
        </div>
        <div className="breakout-criteria-list">
          {report.criteria.map((criterion) => (
            <span key={criterion.key}>
              <strong>{criterion.labelZh}</strong>
              <small>{criterion.labelEn}</small>
              <em>{criterion.value}</em>
            </span>
          ))}
        </div>
        <p>
          <Info size={14} aria-hidden="true" />
          {report.disclaimerZh}
        </p>
        <div className="breakout-source-note">
          <a href={report.source.url} target="_blank" rel="noreferrer">
            {report.source.name}
            <ExternalLink size={13} aria-hidden="true" />
          </a>
          <span>{report.source.noteZh}</span>
          <small>{report.source.noteEn}</small>
          <span>{report.scopeZh}</span>
          <small>{report.scopeEn}</small>
        </div>
        <ProviderStatusList providers={report.providerStatuses} />
      </article>

      <div className="breakout-list">
        {activeWindow.stocks.length === 0 ? (
          <div className="loading-panel">
            <Info size={22} aria-hidden="true" />
            <span>所选窗口当日暂无符合条件的股票</span>
          </div>
        ) : (
          activeWindow.stocks.map((stock) => <StockCard key={`${stock.windowDays}-${stock.code}`} stock={stock} />)
        )}
      </div>
    </section>
  );
}
