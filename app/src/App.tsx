import { AlertCircle, BarChart3, Building2, List, Loader2, Network, RefreshCcw, Search, Star } from "lucide-react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { CompanyDetail } from "./components/CompanyDetail";
import { IndustryChainMap } from "./components/IndustryChainMap";
import { VolumeBreakouts } from "./components/VolumeBreakouts";
import { loadCompanyIndex, loadCompanyReport } from "./lib/data";
import type { CompanyIndex, CompanyIndexItem, CompanyReport } from "./types/company";

const preferredLabelOrder = [
  "半导体",
  "科技",
  "太空",
  "卫星通信",
  "AI",
  "英伟达相关",
  "数据中心",
  "电子材料",
  "国防",
  "美股",
  "A股",
];

const watchlistLabel = "自选";
type ActiveMode = "companies" | "watchlist" | "chain" | "breakouts";

function scoreCompany(company: CompanyIndexItem, query: string) {
  const target = query.trim().toLowerCase();
  if (!target) return 1;

  const haystack = [
    company.ticker,
    company.name,
    company.legalName,
    company.exchange,
    company.market,
    company.sector,
    ...company.labels,
    ...company.aliases,
  ]
    .join(" ")
    .toLowerCase();

  if (company.ticker.toLowerCase() === target) return 100;
  if (company.aliases.some((alias) => alias.toLowerCase() === target)) return 90;
  if (company.labels.some((label) => label.toLowerCase() === target)) return 85;
  if (company.name.toLowerCase().includes(target)) return 75;
  if (haystack.includes(target)) return 50;
  return 0;
}

function sortLabels(labels: string[]) {
  return [...labels].sort((a, b) => {
    const preferredA = preferredLabelOrder.indexOf(a);
    const preferredB = preferredLabelOrder.indexOf(b);
    if (preferredA !== -1 || preferredB !== -1) {
      return (preferredA === -1 ? Number.MAX_SAFE_INTEGER : preferredA) - (preferredB === -1 ? Number.MAX_SAFE_INTEGER : preferredB);
    }
    return a.localeCompare(b, "zh-CN");
  });
}

function App() {
  const sidebarRef = useRef<HTMLElement | null>(null);
  const workspaceRef = useRef<HTMLElement | null>(null);
  const [activeMode, setActiveMode] = useState<ActiveMode>("companies");
  const [index, setIndex] = useState<CompanyIndex | null>(null);
  const [query, setQuery] = useState("");
  const [activeLabel, setActiveLabel] = useState<string | null>(null);
  const [selected, setSelected] = useState<CompanyIndexItem | null>(null);
  const [report, setReport] = useState<CompanyReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [companyError, setCompanyError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    loadCompanyIndex()
      .then((payload) => {
        if (!active) return;
        setIndex(payload);
        setSelected(payload.companies[0] ?? null);
      })
      .catch((err: unknown) => {
        if (!active) return;
        setCompanyError(err instanceof Error ? err.message : "Data load failed");
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    if (!selected) return;

    let active = true;
    setReport(null);
    setCompanyError(null);

    loadCompanyReport(selected.dataPath)
      .then((payload) => {
        if (active) setReport(payload);
      })
      .catch((err: unknown) => {
        if (active) setCompanyError(err instanceof Error ? err.message : "Report load failed");
      });

    return () => {
      active = false;
    };
  }, [selected]);

  const matches = useMemo(() => {
    if (!index) return [];
    return index.companies
      .filter((company) => activeMode !== "watchlist" || company.labels.includes(watchlistLabel))
      .map((company) => ({ company, score: scoreCompany(company, query) }))
      .filter(({ score }) => score > 0)
      .filter(({ company }) => activeMode !== "companies" || !activeLabel || company.labels.includes(activeLabel))
      .sort((a, b) => b.score - a.score)
      .map(({ company }) => company);
  }, [activeLabel, activeMode, index, query]);

  const labelFacets = useMemo(() => {
    if (!index) return [];
    const counts = new Map<string, number>();
    index.companies.forEach((company) => {
      company.labels
        .filter((label) => label !== watchlistLabel)
        .forEach((label) => counts.set(label, (counts.get(label) ?? 0) + 1));
    });
    return sortLabels([...counts.keys()]).map((label) => ({ label, count: counts.get(label) ?? 0 }));
  }, [index]);

  const displayLabels = useCallback((company: CompanyIndexItem) => {
    return company.labels.filter((label) => label !== watchlistLabel).slice(0, 4);
  }, []);

  const switchMode = useCallback((mode: ActiveMode) => {
    setActiveMode(mode);
    if (mode !== "companies") setActiveLabel(null);
  }, []);

  useEffect(() => {
    if (!index || loading) return;
    if (matches.length === 0) {
      setSelected(null);
      setReport(null);
      return;
    }
    if (!selected || !matches.some((company) => company.id === selected.id)) {
      setSelected(matches[0]);
    }
  }, [index, loading, matches, selected]);

  const scrollIntoViewOnMobile = useCallback((element: HTMLElement | null) => {
    if (!element || !window.matchMedia("(max-width: 980px)").matches) return;
    window.requestAnimationFrame(() => {
      element.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  }, []);

  const selectCompany = useCallback(
    (company: CompanyIndexItem) => {
      setSelected(company);
      scrollIntoViewOnMobile(workspaceRef.current);
    },
    [scrollIntoViewOnMobile],
  );

  const openCompanyFromChain = useCallback(
    (company: CompanyIndexItem) => {
      setActiveMode("companies");
      setActiveLabel(null);
      setQuery("");
      selectCompany(company);
    },
    [selectCompany],
  );

  const returnToCompanyList = useCallback(() => {
    scrollIntoViewOnMobile(sidebarRef.current);
  }, [scrollIntoViewOnMobile]);

  return (
    <main className="app-shell">
      <aside className="sidebar" ref={sidebarRef}>
        <div className="brand">
          <span>Stock Checking</span>
          <strong>公开公司溯源</strong>
        </div>

        <nav className="mode-switch" aria-label="workspace mode">
          <button
            aria-pressed={activeMode === "companies"}
            className={activeMode === "companies" ? "mode-button active" : "mode-button"}
            onClick={() => switchMode("companies")}
            type="button"
          >
            <Building2 size={16} aria-hidden="true" />
            <span>公司溯源</span>
          </button>
          <button
            aria-pressed={activeMode === "watchlist"}
            className={activeMode === "watchlist" ? "mode-button active" : "mode-button"}
            onClick={() => switchMode("watchlist")}
            type="button"
          >
            <Star size={16} aria-hidden="true" />
            <span>自选</span>
          </button>
          <button
            aria-pressed={activeMode === "chain"}
            className={activeMode === "chain" ? "mode-button active" : "mode-button"}
            onClick={() => switchMode("chain")}
            type="button"
          >
            <Network size={16} aria-hidden="true" />
            <span>产业链</span>
          </button>
          <button
            aria-pressed={activeMode === "breakouts"}
            className={activeMode === "breakouts" ? "mode-button active" : "mode-button"}
            onClick={() => switchMode("breakouts")}
            type="button"
          >
            <BarChart3 size={16} aria-hidden="true" />
            <span>放量突破</span>
          </button>
        </nav>

        {activeMode === "companies" || activeMode === "watchlist" ? (
          <>
            <label className="search-box">
              <Search size={18} aria-hidden="true" />
              <input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="AAPL / Apple / NVDA"
                aria-label="search stock"
              />
            </label>

            {activeMode === "companies" ? (
              <div className="label-filter" aria-label="company label filters">
                <button
                  aria-label={`全部公司 (${index?.companies.length ?? 0})`}
                  aria-pressed={!activeLabel}
                  className={!activeLabel ? "label-chip active" : "label-chip"}
                  onClick={() => setActiveLabel(null)}
                  type="button"
                >
                  全部
                  <span>{index?.companies.length ?? 0}</span>
                </button>
                {labelFacets.map(({ label, count }) => (
                  <button
                    aria-label={`${label} (${count})`}
                    aria-pressed={activeLabel === label}
                    className={activeLabel === label ? "label-chip active" : "label-chip"}
                    key={label}
                    onClick={() => setActiveLabel(label)}
                    type="button"
                  >
                    {label}
                    <span>{count}</span>
                  </button>
                ))}
              </div>
            ) : (
              <div className="sidebar-mode-card compact">
                <strong>自选股票</strong>
                <span>{matches.length} / {index?.companies.filter((company) => company.labels.includes(watchlistLabel)).length ?? 0}</span>
              </div>
            )}

            <div className="result-list">
              {loading && (
                <div className="state-line">
                  <Loader2 className="spin" size={16} aria-hidden="true" />
                  <span>读取数据</span>
                </div>
              )}

              {!loading &&
                matches.map((company) => (
                  <button
                    className={[
                      "company-button",
                      `market-${company.market.toLowerCase()}`,
                      selected?.id === company.id ? "active" : "",
                    ]
                      .filter(Boolean)
                      .join(" ")}
                    key={company.id}
                    onClick={() => selectCompany(company)}
                    type="button"
                  >
                    <span>{company.ticker}</span>
                    <strong>{company.name}</strong>
                    <small>{company.sector}</small>
                    <div className="company-labels">
                      {displayLabels(company).map((label) => (
                        <em key={`${company.id}-${label}`}>{label}</em>
                      ))}
                    </div>
                  </button>
                ))}

              {!loading && matches.length === 0 && (
                <div className="state-line warn">
                  <AlertCircle size={16} aria-hidden="true" />
                  <span>未收录</span>
                </div>
              )}
            </div>
          </>
        ) : activeMode === "chain" ? (
          <div className="sidebar-mode-card">
            <strong>产业链图谱</strong>
            <span>按当前收录公司与标签生成上游、中游、下游视图。</span>
            <small>{index ? `${index.companies.length} companies mapped` : "Loading company index"}</small>
          </div>
        ) : (
          <div className="sidebar-mode-card">
            <strong>放量突破</strong>
            <span>每日收盘后更新 A 股量价突破名单，支持 20 / 60 / 120 日窗口。</span>
            <small>Daily A-share breakout scan</small>
          </div>
        )}

        <footer className="sidebar-footer">
          <RefreshCcw size={15} aria-hidden="true" />
          <span>
            {activeMode === "companies"
              ? index
                ? new Date(index.generatedAt).toLocaleString("zh-CN")
                : "未生成"
              : activeMode === "watchlist"
                ? "自选"
                : activeMode === "chain"
                  ? "产业链"
                  : "每日更新"}
          </span>
        </footer>
      </aside>

      <section className="workspace" ref={workspaceRef}>
        {activeMode === "breakouts" ? (
          <VolumeBreakouts />
        ) : activeMode === "chain" ? (
          <>
            {companyError && (
              <div className="error-banner">
                <AlertCircle size={18} aria-hidden="true" />
                <span>{companyError}</span>
              </div>
            )}
            {!companyError && loading && (
              <div className="loading-panel">
                <Loader2 className="spin" size={22} aria-hidden="true" />
                <span>加载产业链图谱</span>
              </div>
            )}
            {!companyError && index && <IndustryChainMap index={index} onOpenCompany={openCompanyFromChain} />}
          </>
        ) : (
          <>
            {selected && (
              <button className="mobile-list-return" onClick={returnToCompanyList} type="button">
                <List size={16} aria-hidden="true" />
                <span>返回股票列表</span>
              </button>
            )}
            {companyError && (
              <div className="error-banner">
                <AlertCircle size={18} aria-hidden="true" />
                <span>{companyError}</span>
              </div>
            )}
            {!companyError && !loading && !selected && (
              <div className="loading-panel">
                <AlertCircle size={22} aria-hidden="true" />
                <span>未找到符合条件的公司</span>
              </div>
            )}
            {!companyError && !report && selected && (
              <div className="loading-panel">
                <Loader2 className="spin" size={22} aria-hidden="true" />
                <span>加载公司档案</span>
              </div>
            )}
            {report && <CompanyDetail report={report} />}
          </>
        )}
      </section>
    </main>
  );
}

export default App;
