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
  publisher: string;
  url: string;
  publishedAt?: string;
  accessedAt?: string;
  type: SourceType;
}

export interface BusinessSegment {
  name: string;
  revenue?: number;
  unit?: string;
  period?: string;
  share?: number;
  note: string;
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
}

export interface SupplyChainEntity {
  name: string;
  relationship: string;
  productsServices: string[];
  listing: SupplierListing;
  companyUrl?: string;
  confidence: Confidence;
  sourceIds: string[];
}

export interface SupplierTier {
  level: number;
  title: string;
  companies: string[];
  entities: SupplyChainEntity[];
  geography: string[];
  materials: string[];
  notes: string;
  confidence: Confidence;
  sourceIds: string[];
}

export interface RawMaterial {
  name: string;
  usedIn: string;
  upstream: string[];
  risk: string;
  confidence: Confidence;
}

export interface FinancialHighlight {
  label: string;
  value: number;
  unit: string;
  period: string;
  change?: string;
  sourceIds: string[];
}

export interface NewsItem {
  date: string;
  title: string;
  category: string;
  summary: string;
  impact: string;
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
