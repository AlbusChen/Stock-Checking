import { ExternalLink } from "lucide-react";
import { localizedField } from "../lib/localization";
import type {
  FinancialTrendSeries,
  RevenueMixHistoryPeriod,
  RevenueMixHistorySegment,
  Source,
} from "../types/company";
import { formatFinancialValue, isMoneyScale } from "../lib/format";
import { TextPair } from "./TextPair";

interface FinancialTrendChartsProps {
  trends?: FinancialTrendSeries[];
  revenueMixHistory?: RevenueMixHistoryPeriod[];
  sources: Record<string, Source>;
}

const chartColors = ["#2b7a78", "#8a6f28", "#4a627a", "#7d5b68", "#5f6d68", "#a06d3b"];

function chartDomain(values: number[], unit: string) {
  const rawMin = Math.min(...values);
  const rawMax = Math.max(...values);
  const span = rawMax - rawMin || Math.max(Math.abs(rawMax), 1);
  const padding = span * 0.18;

  if (isMoneyScale(unit)) {
    if (rawMin >= 0) return { min: 0, max: rawMax + padding };
    if (rawMax <= 0) return { min: rawMin - padding, max: 0 };
    return { min: rawMin - padding, max: rawMax + padding };
  }

  return {
    min: rawMin >= 0 ? Math.max(0, rawMin - padding) : rawMin - padding,
    max: rawMax + padding,
  };
}

function formatShare(value: number) {
  return `${value.toLocaleString("en-US", { maximumFractionDigits: 1 })}%`;
}

function segmentShare(segment: RevenueMixHistorySegment | undefined, period: RevenueMixHistoryPeriod) {
  if (!segment) return 0;
  if (typeof segment.share === "number") return segment.share;
  if (period.totalRevenue && period.totalRevenue > 0) return (segment.revenue / period.totalRevenue) * 100;
  const stackTotal = period.segments.reduce((sum, item) => sum + item.revenue, 0);
  return stackTotal > 0 ? (segment.revenue / stackTotal) * 100 : 0;
}

function EvidenceLinks({ ids, sources }: { ids: string[]; sources: Record<string, Source> }) {
  const linked = ids.map((id) => sources[id]).filter(Boolean);
  if (linked.length === 0) return null;

  return (
    <div className="evidence trend-evidence">
      {linked.map((source) => (
        <a href={source.url} target="_blank" rel="noreferrer" key={source.id}>
          {source.publisher}
          <ExternalLink size={13} aria-hidden="true" />
        </a>
      ))}
    </div>
  );
}

function LineTrendCard({ trend, sources }: { trend: FinancialTrendSeries; sources: Record<string, Source> }) {
  const width = 660;
  const height = 210;
  const padding = { top: 18, right: 16, bottom: 44, left: 58 };
  const values = trend.points.map((point) => point.value);
  const { min, max } = chartDomain(values, trend.unit);
  const innerWidth = width - padding.left - padding.right;
  const innerHeight = height - padding.top - padding.bottom;
  const xStep = trend.points.length > 1 ? innerWidth / (trend.points.length - 1) : innerWidth;
  const range = max - min || 1;

  const points = trend.points.map((point, index) => {
    const x = padding.left + index * xStep;
    const y = padding.top + innerHeight - ((point.value - min) / range) * innerHeight;
    return { ...point, x, y };
  });

  const path = points.map((point, index) => `${index === 0 ? "M" : "L"} ${point.x} ${point.y}`).join(" ");
  const area = `${path} L ${points[points.length - 1]?.x ?? padding.left} ${padding.top + innerHeight} L ${
    points[0]?.x ?? padding.left
  } ${padding.top + innerHeight} Z`;
  const sourceIds = Array.from(new Set([...trend.sourceIds, ...trend.points.flatMap((point) => point.sourceIds ?? [])]));

  return (
    <article className="trend-card">
      <div className="trend-card-top">
        <h3>
          <TextPair text={localizedField(trend, "label")} />
        </h3>
        <span>{trend.cadence === "quarterly" ? "财季 / Qtr" : "财年 / FY"}</span>
      </div>
      <svg className="line-chart" viewBox={`0 0 ${width} ${height}`} role="img" aria-label={trend.label}>
        <line
          className="chart-grid-line"
          x1={padding.left}
          x2={width - padding.right}
          y1={padding.top + innerHeight}
          y2={padding.top + innerHeight}
        />
        <line className="chart-grid-line" x1={padding.left} x2={width - padding.right} y1={padding.top} y2={padding.top} />
        <text className="axis-label" x={8} y={padding.top + 4}>
          {formatFinancialValue(max, trend.unit)}
        </text>
        <text className="axis-label" x={8} y={padding.top + innerHeight + 4}>
          {formatFinancialValue(min, trend.unit)}
        </text>
        <path className="line-area" d={area} />
        <path className="trend-line" d={path} />
        {points.map((point) => (
          <g key={`${trend.id}-${point.period}`}>
            <circle className="trend-dot" cx={point.x} cy={point.y} r="4" />
            <text className="point-value" x={point.x} y={point.y - 10}>
              {formatFinancialValue(point.value, trend.unit)}
            </text>
            <text className="axis-label x-label" x={point.x} y={height - 16}>
              {point.periodZh ?? point.period}
            </text>
          </g>
        ))}
      </svg>
      {trend.note ? (
        <p className="trend-note">
          <TextPair text={localizedField(trend, "note")} />
        </p>
      ) : null}
      <EvidenceLinks ids={sourceIds} sources={sources} />
    </article>
  );
}

function collectSegments(periods: RevenueMixHistoryPeriod[]) {
  const names: RevenueMixHistorySegment[] = [];
  const seen = new Set<string>();

  periods.forEach((period) => {
    period.segments.forEach((segment) => {
      if (!seen.has(segment.name)) {
        seen.add(segment.name);
        names.push(segment);
      }
    });
  });

  return names;
}

function RevenueMixHistoryChart({
  periods,
  sources,
}: {
  periods: RevenueMixHistoryPeriod[];
  sources: Record<string, Source>;
}) {
  const width = 760;
  const height = 260;
  const padding = { top: 22, right: 18, bottom: 42, left: 58 };
  const segmentNames = collectSegments(periods);
  const maxTotal = Math.max(...periods.map((period) => period.segments.reduce((sum, segment) => sum + segment.revenue, 0)), 1);
  const valueUnit = periods.find((period) => period.segments.length > 0)?.segments[0]?.unit ?? "USD billions";
  const innerHeight = height - padding.top - padding.bottom;
  const innerWidth = width - padding.left - padding.right;
  const slotWidth = innerWidth / periods.length;
  const barWidth = Math.min(76, slotWidth * 0.58);
  const sourceIds = Array.from(
    new Set([
      ...periods.flatMap((period) => period.sourceIds),
      ...periods.flatMap((period) => period.segments.flatMap((segment) => segment.sourceIds ?? [])),
    ]),
  );

  return (
    <article className="trend-card wide-chart">
      <div className="trend-card-top">
        <h3>
          <TextPair text={{ zh: "收入构成历史", en: "Historical revenue mix" }} />
        </h3>
        <span>构成 / Mix</span>
      </div>
      <svg className="stack-chart" viewBox={`0 0 ${width} ${height}`} role="img" aria-label="historical revenue mix">
        <line
          className="chart-grid-line"
          x1={padding.left}
          x2={width - padding.right}
          y1={padding.top + innerHeight}
          y2={padding.top + innerHeight}
        />
        <text className="axis-label" x={8} y={padding.top + 4}>
          {formatFinancialValue(maxTotal, valueUnit)}
        </text>
        {periods.map((period, periodIndex) => {
          let offset = 0;
          const stackTotal = period.segments.reduce((sum, segment) => sum + segment.revenue, 0);
          const x = padding.left + periodIndex * slotWidth + (slotWidth - barWidth) / 2;

          return (
            <g key={period.period}>
              {segmentNames.map((segmentName, segmentIndex) => {
                const segment = period.segments.find((item) => item.name === segmentName.name);
                const value = segment?.revenue ?? 0;
                const share = segmentShare(segment, period);
                const segmentHeight = (value / maxTotal) * innerHeight;
                const y = padding.top + innerHeight - offset - segmentHeight;
                offset += segmentHeight;

                return (
                  <g key={`${period.period}-${segmentName.name}`}>
                    <rect
                      className="stack-segment"
                      fill={chartColors[segmentIndex % chartColors.length]}
                      height={Math.max(segmentHeight, value > 0 ? 2 : 0)}
                      rx="3"
                      width={barWidth}
                      x={x}
                      y={y}
                    />
                    {segmentHeight >= 24 ? (
                      <text className="stack-percent" x={x + barWidth / 2} y={y + segmentHeight / 2 + 4}>
                        {formatShare(share)}
                      </text>
                    ) : null}
                  </g>
                );
              })}
              <text className="axis-label x-label" x={x + barWidth / 2} y={height - 16}>
                {period.periodZh ?? period.period}
              </text>
              <text className="point-value" x={x + barWidth / 2} y={padding.top + innerHeight - offset - 8}>
                {formatFinancialValue(stackTotal, valueUnit)}
              </text>
            </g>
          );
        })}
      </svg>
      <div className="chart-legend">
        {segmentNames.map((segment, index) => (
          <span key={segment.name}>
            <i style={{ background: chartColors[index % chartColors.length] }} />
            <TextPair text={localizedField(segment, "name")} />
          </span>
        ))}
      </div>
      <div className="mix-share-table">
        <div className="mix-share-header">
          <span>分部 / Segment</span>
          {periods.map((period) => (
            <span key={period.period}>{period.periodZh ?? period.period}</span>
          ))}
        </div>
        {segmentNames.map((segmentName) => (
          <div className="mix-share-row" key={`${segmentName.name}-share-row`}>
            <span>
              <TextPair text={localizedField(segmentName, "name")} />
            </span>
            {periods.map((period) => {
              const segment = period.segments.find((item) => item.name === segmentName.name);
              return (
                <span key={`${period.period}-${segmentName.name}-share`}>
                  {segment ? (
                    <>
                      <strong>{formatShare(segmentShare(segment, period))}</strong>
                      <small>{formatFinancialValue(segment.revenue, segment.unit)}</small>
                    </>
                  ) : (
                    "n/a"
                  )}
                </span>
              );
            })}
          </div>
        ))}
      </div>
      <div className="mix-history-notes">
        {periods
          .filter((period) => period.note)
          .map((period) => (
            <p key={`${period.period}-note`}>
              <TextPair text={localizedField(period, "note")} />
            </p>
          ))}
      </div>
      <EvidenceLinks ids={sourceIds} sources={sources} />
    </article>
  );
}

export function FinancialTrendCharts({ trends = [], revenueMixHistory = [], sources }: FinancialTrendChartsProps) {
  if (trends.length === 0 && revenueMixHistory.length === 0) return null;

  return (
    <section className="trend-section">
      <div className="trend-grid">
        {trends.map((trend) => (
          <LineTrendCard key={trend.id} trend={trend} sources={sources} />
        ))}
      </div>
      {revenueMixHistory.length ? <RevenueMixHistoryChart periods={revenueMixHistory} sources={sources} /> : null}
    </section>
  );
}
