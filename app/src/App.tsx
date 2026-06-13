import { AlertCircle, Loader2, RefreshCcw, Search } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { CompanyDetail } from "./components/CompanyDetail";
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
  const [index, setIndex] = useState<CompanyIndex | null>(null);
  const [query, setQuery] = useState("");
  const [activeLabel, setActiveLabel] = useState<string | null>(null);
  const [selected, setSelected] = useState<CompanyIndexItem | null>(null);
  const [report, setReport] = useState<CompanyReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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
        setError(err instanceof Error ? err.message : "Data load failed");
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
    setError(null);

    loadCompanyReport(selected.dataPath)
      .then((payload) => {
        if (active) setReport(payload);
      })
      .catch((err: unknown) => {
        if (active) setError(err instanceof Error ? err.message : "Report load failed");
      });

    return () => {
      active = false;
    };
  }, [selected]);

  const matches = useMemo(() => {
    if (!index) return [];
    return index.companies
      .map((company) => ({ company, score: scoreCompany(company, query) }))
      .filter(({ score }) => score > 0)
      .filter(({ company }) => !activeLabel || company.labels.includes(activeLabel))
      .sort((a, b) => b.score - a.score)
      .map(({ company }) => company);
  }, [activeLabel, index, query]);

  const labelFacets = useMemo(() => {
    if (!index) return [];
    const counts = new Map<string, number>();
    index.companies.forEach((company) => {
      company.labels.forEach((label) => counts.set(label, (counts.get(label) ?? 0) + 1));
    });
    return sortLabels([...counts.keys()]).map((label) => ({ label, count: counts.get(label) ?? 0 }));
  }, [index]);

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

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <span>Stock Checking</span>
          <strong>公开公司溯源</strong>
        </div>

        <label className="search-box">
          <Search size={18} aria-hidden="true" />
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="AAPL / Apple / NVDA"
            aria-label="search stock"
          />
        </label>

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
                onClick={() => setSelected(company)}
                type="button"
              >
                <span>{company.ticker}</span>
                <strong>{company.name}</strong>
                <small>{company.sector}</small>
                <div className="company-labels">
                  {company.labels.slice(0, 4).map((label) => (
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

        <footer className="sidebar-footer">
          <RefreshCcw size={15} aria-hidden="true" />
          <span>{index ? new Date(index.generatedAt).toLocaleString("zh-CN") : "未生成"}</span>
        </footer>
      </aside>

      <section className="workspace">
        {error && (
          <div className="error-banner">
            <AlertCircle size={18} aria-hidden="true" />
            <span>{error}</span>
          </div>
        )}
        {!error && !loading && !selected && (
          <div className="loading-panel">
            <AlertCircle size={22} aria-hidden="true" />
            <span>未找到符合条件的公司</span>
          </div>
        )}
        {!error && !report && selected && (
          <div className="loading-panel">
            <Loader2 className="spin" size={22} aria-hidden="true" />
            <span>加载公司档案</span>
          </div>
        )}
        {report && <CompanyDetail report={report} />}
      </section>
    </main>
  );
}

export default App;
