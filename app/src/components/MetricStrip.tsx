import type { FinancialHighlight } from "../types/company";
import { formatFinancialValue } from "../lib/format";
import { combineLocalized, localizedField } from "../lib/localization";
import { TextPair } from "./TextPair";

interface MetricStripProps {
  metrics: FinancialHighlight[];
}

export function MetricStrip({ metrics }: MetricStripProps) {
  return (
    <div className="metric-strip" aria-label="financial metrics">
      {metrics.slice(0, 4).map((metric) => (
        <div className="metric" key={`${metric.label}-${metric.period}`}>
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
        </div>
      ))}
    </div>
  );
}
