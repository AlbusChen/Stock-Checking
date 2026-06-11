export function formatFinancialValue(value: number, unit: string) {
  const sign = value < 0 ? "-" : "";
  const absoluteValue = Math.abs(value);

  if (unit === "USD billions") {
    return `${sign}$${absoluteValue.toLocaleString("en-US", { maximumFractionDigits: absoluteValue >= 100 ? 0 : 3 })}B`;
  }
  if (unit === "CNY billions") {
    return `${sign}¥${absoluteValue.toLocaleString("en-US", { maximumFractionDigits: absoluteValue >= 100 ? 0 : 3 })}B`;
  }
  if (unit === "USD millions") {
    return `${sign}$${absoluteValue.toLocaleString("en-US", { maximumFractionDigits: absoluteValue >= 100 ? 0 : 2 })}M`;
  }
  if (unit === "CNY millions") {
    return `${sign}¥${absoluteValue.toLocaleString("en-US", { maximumFractionDigits: absoluteValue >= 100 ? 0 : 2 })}M`;
  }
  if (unit === "percent") {
    return `${value.toLocaleString("en-US", { maximumFractionDigits: 1 })}%`;
  }
  if (unit === "USD") {
    return `${sign}$${absoluteValue.toLocaleString("en-US", { maximumFractionDigits: 2 })}`;
  }
  if (unit === "CNY") {
    return `${sign}¥${absoluteValue.toLocaleString("en-US", { maximumFractionDigits: 2 })}`;
  }
  return value.toLocaleString("en-US", { maximumFractionDigits: 2 });
}

export function isMoneyScale(unit: string) {
  return unit === "USD billions" || unit === "CNY billions" || unit === "USD millions" || unit === "CNY millions";
}
