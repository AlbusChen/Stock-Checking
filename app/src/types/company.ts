export type Market = "US" | "CN";

export type SourceType =
  | "company"
  | "sec"
  | "exchange"
  | "news"
  | "research"
  | "industry";

export type Confidence = "high" | "medium" | "low";

export interface CompanyIndexItem {
  id: string;
  ticker: string;
  name: string;
  legalName: string;
  exchange: string;
  market: Market;
  dataPath: string;
  aliases: string[];
  sector: string;
  lastUpdated: string;
  summary: string;
}

export interface CompanyIndex {
  generatedAt: string;
  companies: CompanyIndexItem[];
}

export interface Source {
  id: string;
  title: string;
  titleZh?: string;
  titleEn?: string;
  publisher: string;
  url: string;
  publishedAt?: string;
  accessedAt?: string;
  type: SourceType;
}

export interface BusinessSegment {
  name: string;
  nameZh?: string;
  nameEn?: string;
  revenue?: number;
  unit?: string;
  period?: string;
  periodZh?: string;
  periodEn?: string;
  share?: number;
  note: string;
  noteZh?: string;
  noteEn?: string;
  sourceIds: string[];
}

export type ListingStatus = "listed" | "listed-parent" | "private" | "delisted" | "unknown";

export interface SupplierListing {
  status: ListingStatus;
  ticker?: string;
  exchange?: string;
  market?: string;
  stockUrl?: string;
  parentCompany?: string;
  parentTicker?: string;
  parentExchange?: string;
  parentStockUrl?: string;
  formerTicker?: string;
  note?: string;
  noteZh?: string;
  noteEn?: string;
}

export interface SupplyChainEntity {
  name: string;
  relationship: string;
  relationshipZh?: string;
  relationshipEn?: string;
  productsServices: string[];
  productsServicesZh?: string[];
  productsServicesEn?: string[];
  listing: SupplierListing;
  companyUrl?: string;
  confidence: Confidence;
  sourceIds: string[];
}

export interface SupplierTier {
  level: number;
  title: string;
  titleZh?: string;
  titleEn?: string;
  companies: string[];
  entities: SupplyChainEntity[];
  geography: string[];
  materials: string[];
  materialsZh?: string[];
  materialsEn?: string[];
  notes: string;
  notesZh?: string;
  notesEn?: string;
  confidence: Confidence;
  sourceIds: string[];
}

export interface RawMaterial {
  name: string;
  nameZh?: string;
  nameEn?: string;
  usedIn: string;
  usedInZh?: string;
  usedInEn?: string;
  upstream: string[];
  upstreamZh?: string[];
  upstreamEn?: string[];
  risk: string;
  riskZh?: string;
  riskEn?: string;
  confidence: Confidence;
}

export interface FinancialHighlight {
  label: string;
  labelZh?: string;
  labelEn?: string;
  value: number;
  unit: string;
  period: string;
  periodZh?: string;
  periodEn?: string;
  change?: string;
  changeZh?: string;
  changeEn?: string;
  sourceIds: string[];
}

export interface NewsItem {
  date: string;
  title: string;
  titleZh?: string;
  titleEn?: string;
  category: string;
  categoryZh?: string;
  categoryEn?: string;
  summary: string;
  summaryZh?: string;
  summaryEn?: string;
  impact: string;
  impactZh?: string;
  impactEn?: string;
  sourceIds: string[];
}

export interface FilingItem {
  form: string;
  filedAt: string;
  reportDate?: string;
  title: string;
  url: string;
}

export interface CompanyReport {
  schemaVersion: number;
  id: string;
  ticker: string;
  exchange: string;
  market: Market;
  name: string;
  legalName: string;
  cik?: string;
  currency: string;
  sector: string;
  industry: string[];
  homepage: string;
  lastUpdated: string;
  summary: string;
  updateCadence: Record<string, string>;
  business: {
    description: string;
    revenueModel: string[];
    segments: BusinessSegment[];
    thesis: string;
    riskNotes: string[];
  };
  supplyChain: {
    updatedAt: string;
    thesis: string;
    tiers: SupplierTier[];
    rawMaterials: RawMaterial[];
  };
  financials: {
    latestPeriod: string;
    latestPeriodZh?: string;
    latestPeriodEn?: string;
    highlights: FinancialHighlight[];
    revenueMix: BusinessSegment[];
  };
  news: NewsItem[];
  filings: FilingItem[];
  sources: Source[];
  automation?: {
    sec?: {
      cik: string;
      forms: string[];
    };
    newsFeeds?: Array<{
      url: string;
      publisher: string;
      sourceType: SourceType;
    }>;
  };
}
