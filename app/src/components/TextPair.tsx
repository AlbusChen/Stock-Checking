import type { LocalizedText } from "../lib/localization";

interface TextPairProps {
  text: LocalizedText;
  className?: string;
}

export function TextPair({ text, className }: TextPairProps) {
  const classes = ["text-pair", className].filter(Boolean).join(" ");

  return (
    <span className={classes}>
      <span>{text.zh}</span>
      {text.en ? <small lang="en">{text.en}</small> : null}
    </span>
  );
}
