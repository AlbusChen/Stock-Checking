export interface LocalizedText {
  zh: string;
  en?: string;
}

function isString(value: unknown): value is string {
  return typeof value === "string";
}

function isStringList(value: unknown): value is string[] {
  return Array.isArray(value) && value.every((item) => typeof item === "string");
}

export function hasCjk(value: string) {
  return /[\u3400-\u9fff]/.test(value);
}

export function localizedField(item: object, field: string): LocalizedText {
  const record = item as Record<string, unknown>;
  const base = isString(record[field]) ? record[field] : "";
  const explicitZh = record[`${field}Zh`];
  const explicitEn = record[`${field}En`];
  const zh = isString(explicitZh) && explicitZh ? explicitZh : hasCjk(base) ? base : base;
  const en = isString(explicitEn) && explicitEn ? explicitEn : base && !hasCjk(base) ? base : undefined;

  return {
    zh,
    en: en && en !== zh ? en : undefined,
  };
}

export function localizedList(item: object, field: string): LocalizedText[] {
  const record = item as Record<string, unknown>;
  const base = isStringList(record[field]) ? record[field] : [];
  const zhList = isStringList(record[`${field}Zh`])
    ? (record[`${field}Zh`] as string[])
    : base;
  const enList = isStringList(record[`${field}En`])
    ? (record[`${field}En`] as string[])
    : base.every((value) => !hasCjk(value))
      ? base
      : [];

  return zhList.map((zh, index) => {
    const en = enList[index];
    return {
      zh,
      en: en && en !== zh ? en : undefined,
    };
  });
}

export function combineLocalized(parts: LocalizedText[], separator = " · "): LocalizedText {
  const zh = parts
    .map((part) => part.zh)
    .filter(Boolean)
    .join(separator);
  const en = parts
    .map((part) => part.en)
    .filter(Boolean)
    .join(separator);

  return {
    zh,
    en: en && en !== zh ? en : undefined,
  };
}
