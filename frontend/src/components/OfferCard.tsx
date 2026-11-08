"use client";

import { useState } from "react";
import { inr, type Offer } from "@/lib/api";
import { t } from "@/lib/i18n";

export function OfferCard({
  offer,
  lang,
  explanation,
  onCheckout,
}: {
  offer: Offer;
  lang: string;
  explanation?: string;
  onCheckout?: (tier: string) => void;
}) {
  const names = Object.keys(offer.tiers);
  const [tier, setTier] = useState(offer.default ?? names[0]);
  const [open, setOpen] = useState<string | null>(null);
  const cur = offer.tiers[tier];
  if (!cur) return null;
  const tt = cur.totals;

  return (
    <div className="w-full overflow-hidden rounded-[20px] border border-border bg-surface shadow-sm">
      {names.length > 1 && (
        <div role="tablist" className="grid border-b border-border" style={{ gridTemplateColumns: `repeat(${names.length}, 1fr)` }}>
          {names.map((n) => (
            <button
              key={n}
              role="tab"
              aria-selected={n === tier}
              onClick={() => setTier(n)}
              className={`px-2 py-2.5 text-sm font-medium ${n === tier ? "border-b-2 border-foreground text-brand" : "text-muted"}`}
            >
              {offer.tiers[n].label}
              <span className="block text-xs font-normal tabular">{inr(offer.tiers[n].totals.monthly_total)}</span>
            </button>
          ))}
        </div>
      )}
      <div className="p-4">
        <div className="flex items-end justify-between gap-3">
          <div>
            <p className="text-3xl font-bold tabular">
              {inr(tt.monthly_total)}
              <span className="text-base font-medium text-muted">{t(lang, "perMonth")}</span>
            </p>
            <p className="text-xs text-muted">
              {t(lang, "inclGst")} · {t(lang, "lockIn")} {tt.lock_in_months} {t(lang, "months")}
              {tt.setup_total > 0 && ` · ${t(lang, "oneTime")} ${inr(tt.setup_total)}`}
            </p>
          </div>
          <p className="rounded-full bg-ok-soft px-2.5 py-1 text-xs font-medium text-ok">{t(lang, "readyIn", { d: tt.ready_in_days })}</p>
        </div>
        {tt.current_spend != null && tt.difference_vs_current != null && (
          <p className={`mt-2 text-sm ${tt.difference_vs_current <= 0 ? "text-ok" : "text-muted"}`}>
            {tt.difference_vs_current <= 0 ? "▼" : "▲"} {inr(Math.abs(tt.difference_vs_current))} {t(lang, "vsToday")} ({inr(tt.current_spend)})
          </p>
        )}

        <ul className="mt-4 divide-y divide-border">
          {cur.lines.map((l) => (
            <li key={l.product_id} className="py-2.5">
              <button
                className="flex w-full items-start justify-between gap-3 text-left"
                onClick={() => setOpen(open === l.product_id ? null : l.product_id)}
                aria-expanded={open === l.product_id}
              >
                <span>
                  <span className="font-medium">{l.name}</span>
                  {l.quantity > 1 && <span className="text-muted"> × {l.quantity}</span>}
                  <span className="block text-xs text-muted">{l.category}</span>
                </span>
                <span className="shrink-0 text-sm tabular">{inr(l.monthly)}</span>
              </button>
              {open === l.product_id ? (
                <p className="mt-1.5 rounded-lg bg-surface-2 p-2 text-sm">{l.why}</p>
              ) : (
                <p className="mt-0.5 line-clamp-1 text-xs text-muted">{l.why}</p>
              )}
            </li>
          ))}
        </ul>

        {cur.notes.length > 0 && (
          <div className="mt-3 space-y-1 rounded-lg bg-warn-soft p-3 text-sm text-warn">
            {cur.notes.map((n) => (
              <p key={n}>ⓘ {n}</p>
            ))}
          </div>
        )}
        {explanation && <p className="mt-3 whitespace-pre-line text-sm text-muted">{explanation}</p>}
        {offer.why_not && offer.why_not.length > 0 && (
          <details className="mt-3 rounded-lg border border-border p-3 text-sm">
            <summary className="cursor-pointer font-medium">Why not other products? ({offer.why_not.length})</summary>
            <ul className="mt-2 space-y-1">
              {offer.why_not.map((w) => (
                <li key={w.product_id}>
                  <span className="font-medium">{w.name}</span>
                  <span className="text-muted">: {w.reasons.join("; ")}</span>
                </li>
              ))}
            </ul>
            <p className="mt-2 text-xs text-muted">Checked by our rules engine against the product catalogue, not guessed.</p>
          </details>
        )}
        {onCheckout && (
          <button onClick={() => onCheckout(tier)} className="mt-4 w-full rounded-full bg-foreground py-3 font-semibold text-background">
            {t(lang, "seeQuote")} →
          </button>
        )}
      </div>
    </div>
  );
}
