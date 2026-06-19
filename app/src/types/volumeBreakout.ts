export interface LocalizedText {
  zh: string;
  en: string;
}

export interface VolumeBreakoutCriterion {
  key: string;
  labelZh: string;
  labelEn: string;
  value: string | number;
}

export interface VolumeBreakoutFactor {
  labelZh: string;
  labelEn: string;
  valueZh: string;
  valueEn: string;
}

export interface VolumeBreakoutExternalSignal {
  sourceZh: string;
  sourceEn: string;
  queries: string[];
  signals: string[];
  noteZh: string;
  noteEn: string;
}

export interface VolumeBreakoutProviderStatus {
  id: string;
  nameZh: string;
  nameEn: string;
  status: "ok" | "partial" | "failed" | "skipped";
  count: number;
  noteZh: string;
  noteEn: string;
  queries: string[];
  errors?: string[];
}

export interface VolumeBreakoutStock {
  code: string;
  name: string;
  exchange: "SSE" | "SZSE" | "BSE" | "UNKNOWN";
  market: "CN";
  quoteUrl: string;
  industry?: string;
  region?: string;
  tradeDate: string;
  windowDays: number;
  close: number;
  high: number;
  previousHigh: number;
  breakoutPct: number;
  pctChange: number;
  volume: number;
  averageVolume: number;
  volumeRatio: number;
  amountCny: number;
  turnoverRate?: number;
  rankScore: number;
  tags: string[];
  candidateSources?: string[];
  externalSignals?: VolumeBreakoutExternalSignal[];
  reasonZh: string;
  reasonEn: string;
  factors: VolumeBreakoutFactor[];
}

export interface VolumeBreakoutWindow {
  days: number;
  labelZh: string;
  labelEn: string;
  descriptionZh: string;
  descriptionEn: string;
  stocks: VolumeBreakoutStock[];
}

export interface VolumeBreakoutReport {
  schemaVersion: number;
  generatedAt: string;
  tradeDate: string;
  source: {
    name: string;
    url: string;
    noteZh: string;
    noteEn: string;
  };
  candidateProvider?: "computed" | "hybrid" | "ths";
  providerStatuses?: VolumeBreakoutProviderStatus[];
  scopeZh: string;
  scopeEn: string;
  criteria: VolumeBreakoutCriterion[];
  disclaimerZh: string;
  disclaimerEn: string;
  windows: VolumeBreakoutWindow[];
}
