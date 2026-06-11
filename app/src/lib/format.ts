export function formatFinancialValue(value: number, unit: string) {
  if (unit === "USD billions") {
    return `$${value.toLocaleString("en-US", { maximumFractionDigits: value >= 100 ? 0 : 3 })}B`;
  }
  if (unit === "CNY billions") {
    return `¥${value.toLocaleString("en-US", { maximumFractionDigits: value >= 100 ? 0 : 3 })}B`;
  }
  if (unit === "USD millions") {
    return `$${value.toLocaleString("en-US", { maximumFractionDigits: value >= 100 ? 0 : 2 })}M`;
  }
  if (unit === "CNY millions") {
    return `¥${value.toLocaleString("en-US", { maximumFractionDigits: value >= 100 ? 0 : 2 })}M`;
  }
  if (unit === "percent") {
    return `${value.toLocaleString("en-US", { maximumFractionDigits: 1 })}%`;
  }
  if (unit === "USD") {
    return `$${value.toLocaleString("en-US", { maximumFractionDigits: 2 })}`;
  }
  if (unit === "CNY") {
    return `¥${value.toLocaleString("en-US", { maximumFractionDigits: 2 })}`;
  }
  return value.toLocaleString("en-US", { maximumFractionDigits: 2 });
}

export function isMoneyScale(unit: string) {
  return unit === "USD billions" || unit === "CNY billions" || unit === "USD millions" || unit === "CNY millions";
}
