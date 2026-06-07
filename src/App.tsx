import { AlertCircle, Loader2, RefreshCcw, Search } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { CompanyDetail } from "./components/CompanyDetail";
import { loadCompanyIndex, loadCompanyReport } from "./lib/data";
import type { CompanyIndex, CompanyIndexItem, CompanyReport } from "./types/company";

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
    ...company.aliases,
  ]
    .join(" ")
    .toLowerCase();

  if (company.ticker.toLowerCase() === target) return 100;
  if (company.aliases.some((alias) => alias.toLowerCase() === target)) return 90;
  if (company.name.toLowerCase().includes(target)) return 75;
  if (haystack.includes(target)) return 50;
  return 0;
}

function App() {
  const [index, setIndex] = useState<CompanyIndex | null>(null);
  const [query, setQuery] = useState("");
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
      .sort((a, b) => b.score - a.score)
      .map(({ company }) => company);
  }, [index, query]);

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
                className={selected?.id === company.id ? "company-button active" : "company-button"}
                key={company.id}
                onClick={() => setSelected(company)}
                type="button"
              >
                <span>{company.ticker}</span>
                <strong>{company.name}</strong>
                <small>{company.sector}</small>
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
        {!error && !report && (
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
