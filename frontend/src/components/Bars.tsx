"use client";

import { useState } from "react";

/** Single-series horizontal bar chart: direct value labels, hover tooltip, one highlighted bar. */
export function Bars({
  data,
  format = (n) => n.toLocaleString("en-IN"),
  highlight,
  label,
}: {
  data: { label: string; value: number; note?: string }[];
  format?: (n: number) => string;
  highlight?: string;
  label: string;
}) {
  const [hover, setHover] = useState<number | null>(null);
  const max = Math.max(...data.map((d) => d.value), 1);
  return (
    <figure aria-label={label} className="space-y-1.5">
      {data.map((d, i) => (
        <div
          key={d.label}
          className="group grid grid-cols-[minmax(7rem,38%)_1fr] items-center gap-3 rounded-md py-0.5 text-sm"
          onMouseEnter={() => setHover(i)}
          onMouseLeave={() => setHover(null)}
        >
          <span className="truncate text-muted" title={d.label}>
            {d.label}
          </span>
          <div className="relative flex items-center gap-2">
            <div
              className="h-4 rounded-r-[4px] transition-opacity"
              style={{
                width: `${Math.max((d.value / max) * 100, 1.5)}%`,
                background: d.label === highlight ? "var(--chart-hi)" : "var(--chart-bar)",
                opacity: hover === null || hover === i ? 1 : 0.55,
              }}
            />
            <span className="shrink-0 tabular text-xs text-foreground">{format(d.value)}</span>
            {hover === i && d.note && (
              <span className="absolute left-0 top-6 z-10 whitespace-nowrap rounded-md border border-border bg-surface px-2 py-1 text-xs shadow">
                {d.note}
              </span>
            )}
          </div>
        </div>
      ))}
    </figure>
  );
}
