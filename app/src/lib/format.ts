export function formatFinancialValue(value: number, unit: string) {
  const sign = value < 0 ? "-" : "";
  const absoluteValue = Math.abs(value);
  const moneyUnit = unit.match(/^(USD|CNY|EUR|TWD)(?: (trillions|billions|millions))?$/);

  if (moneyUnit) {
    const [, currency, scale] = moneyUnit;
    const symbols: Record<string, string> = {
      USD: "$",
      CNY: "¥",
      EUR: "€",
      TWD: "NT$",
    };
    const suffixes: Record<string, string> = {
      trillions: "T",
      billions: "B",
      millions: "M",
    };
    const maximumFractionDigits = scale === "millions" ? 2 : 3;
    return `${sign}${symbols[currency]}${absoluteValue.toLocaleString("en-US", {
      maximumFractionDigits: absoluteValue >= 100 ? 0 : maximumFractionDigits,
    })}${scale ? suffixes[scale] : ""}`;
  }
  if (unit === "percent") {
    return `${value.toLocaleString("en-US", { maximumFractionDigits: 1 })}%`;
  }
  return value.toLocaleString("en-US", { maximumFractionDigits: 2 });
}

export function isMoneyScale(unit: string) {
  return /^(USD|CNY|EUR|TWD) (trillions|billions|millions)$/.test(unit);
}
