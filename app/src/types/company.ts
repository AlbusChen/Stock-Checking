export type Market = "US" | "CN";

export type SourceType =
  | "company"
  | "sec"
  | "exchange"
  | "news"
  | "research"
  | "industry";

export type Confidence = "high" | "medium" | "low";

export type EvidenceLevel = "strong" | "medium" | "weak" | "needs-checking";

export type ScarcityConstraintType =
  | "capacity"
  | "yield"
  | "purity"
  | "qualification"
  | "technology"
  | "regulatory"
  | "customer-demand"
  | "capital-intensity"
  | "unknown";

export type RelationshipDirection =
  | "target"
  | "upstream-raw-material"
  | "upstream-component"
  | "upstream-equipment"
  | "upstream-manufacturing"
  | "direct-supplier"
  | "system-integration"
  | "downstream-customer"
  | "indirect-demand"
  | "peer-theme"
  | "partner"
  | "unknown";

export interface RelationshipStrength {
  score: 1 | 2 | 3 | 4 | 5;
  label: string;
  labelZh?: string;
  labelEn?: string;
  direction: RelationshipDirection;
  rationale: string;
  rationaleZh?: string;
  rationaleEn?: string;
  confidence: Confidence;
}

export interface FailureCondition {
  condition: string;
  conditionZh?: string;
  conditionEn?: string;
  monitor: string;
  monitorZh?: string;
  monitorEn?: string;
  sourceIds?: string[];
}

export interface ThemeExposure {
  theme: string;
  themeZh?: string;
  themeEn?: string;
  score: 1 | 2 | 3 | 4 | 5;
  role: string;
  roleZh?: string;
  roleEn?: string;
  rationale: string;
  rationaleZh?: string;
  rationaleEn?: string;
  confidence: Confidence;
  failureConditions?: FailureCondition[];
}

export interface CompanyIndexItem {
  id: string;
  ticker: string;
  name: string;
  legalName: string;
  exchange: string;
  market: Market;
  dataPath: string;
  aliases: string[];
  labels: string[];
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
  evidenceLevel?: EvidenceLevel;
  evidenceLevelZh?: string;
  evidenceLevelEn?: string;
}

export interface ScarceLayer {
  name: string;
  nameZh?: string;
  nameEn?: string;
  rank: number;
  constraintType: ScarcityConstraintType;
  constraintTypeZh?: string;
  constraintTypeEn?: string;
  whyScarce: string;
  whyScarceZh?: string;
  whyScarceEn?: string;
  relatedCompanies: string[];
  evidenceLevel: EvidenceLevel;
  confidence: Confidence;
  sourceIds: string[];
  failureConditions: FailureCondition[];
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
  nameZh?: string;
  nameEn?: string;
  relationship: string;
  relationshipZh?: string;
  relationshipEn?: string;
  productsServices: string[];
  productsServicesZh?: string[];
  productsServicesEn?: string[];
  listing: SupplierListing;
  companyUrl?: string;
  confidence: Confidence;
  relationshipStrength?: RelationshipStrength;
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

export interface DownstreamEntity {
  name: string;
  nameZh?: string;
  nameEn?: string;
  customerRole: string;
  customerRoleZh?: string;
  customerRoleEn?: string;
  relationship: string;
  relationshipZh?: string;
  relationshipEn?: string;
  productsServices: string[];
  productsServicesZh?: string[];
  productsServicesEn?: string[];
  listing: SupplierListing;
  companyUrl?: string;
  confidence: Confidence;
  relationshipStrength?: RelationshipStrength;
  sourceIds: string[];
}

export interface DownstreamTier {
  level: number;
  title: string;
  titleZh?: string;
  titleEn?: string;
  entities: DownstreamEntity[];
  notes: string;
  notesZh?: string;
  notesEn?: string;
  confidence: Confidence;
  sourceIds: string[];
}

export interface DownstreamChain {
  updatedAt: string;
  thesis: string;
  thesisZh?: string;
  thesisEn?: string;
  tiers: DownstreamTier[];
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

export interface FinancialTrendPoint {
  period: string;
  periodZh?: string;
  periodEn?: string;
  value: number;
  sourceIds?: string[];
}

export interface FinancialTrendSeries {
  id: string;
  label: string;
  labelZh?: string;
  labelEn?: string;
  unit: string;
  cadence: "quarterly" | "annual";
  note?: string;
  noteZh?: string;
  noteEn?: string;
  sourceIds: string[];
  points: FinancialTrendPoint[];
}

export interface RevenueMixHistorySegment {
  name: string;
  nameZh?: string;
  nameEn?: string;
  revenue: number;
  unit: string;
  share?: number;
  sourceIds?: string[];
}

export interface RevenueMixHistoryPeriod {
  period: string;
  periodZh?: string;
  periodEn?: string;
  totalRevenue?: number;
  note?: string;
  noteZh?: string;
  noteEn?: string;
  sourceIds: string[];
  segments: RevenueMixHistorySegment[];
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
  labels: string[];
  themeExposure?: ThemeExposure[];
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
    failureConditions?: FailureCondition[];
  };
  supplyChain: {
    updatedAt: string;
    thesis: string;
    scarceLayers?: ScarceLayer[];
    tiers: SupplierTier[];
    rawMaterials: RawMaterial[];
    downstream?: DownstreamChain;
  };
  financials: {
    latestPeriod: string;
    latestPeriodZh?: string;
    latestPeriodEn?: string;
    highlights: FinancialHighlight[];
    trends?: FinancialTrendSeries[];
    revenueMix: BusinessSegment[];
    revenueMixHistory?: RevenueMixHistoryPeriod[];
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
