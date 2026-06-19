import type { CompanyIndex, CompanyReport } from "../types/company";
import type { VolumeBreakoutReport } from "../types/volumeBreakout";

const withBase = (path: string) => {
  const base = import.meta.env.BASE_URL.endsWith("/")
    ? import.meta.env.BASE_URL
    : `${import.meta.env.BASE_URL}/`;
  return `${base}${path.replace(/^\//, "")}`;
};

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(withBase(path));
  if (!response.ok) {
    throw new Error(`Failed to load ${path}: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export const loadCompanyIndex = () => getJson<CompanyIndex>("data/company-index.json");

export const loadCompanyReport = (path: string) => getJson<CompanyReport>(path);

export const loadVolumeBreakouts = () => getJson<VolumeBreakoutReport>("data/volume-breakouts.json");
