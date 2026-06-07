import type { FinancialHighlight } from "../types/company";

interface MetricStripProps {
  metrics: FinancialHighlight[];
}

export function MetricStrip({ metrics }: MetricStripProps) {
  return (
    <div className="metric-strip" aria-label="financial metrics">
      {metrics.slice(0, 4).map((metric) => (
        <div className="metric" key={`${metric.label}-${metric.period}`}>
          <span>{metric.label}</span>
          <strong>
            {metric.unit === "USD billions" ? "$" : ""}
            {metric.value.toLocaleString("en-US")}
            {metric.unit === "USD billions" ? "B" : metric.unit === "percent" ? "%" : ""}
          </strong>
          <small>
            {metric.period}
            {metric.change ? ` · ${metric.change}` : ""}
          </small>
        </div>
      ))}
    </div>
  );
}
