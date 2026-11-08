"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { Bars } from "@/components/Bars";
import { Logo } from "@/components/Header";
import { api, inr, type CallItem, type Insights, type QueueItem, type ScenarioRun } from "@/lib/api";

const TABS = ["Queue", "Orders", "Call-back list", "Insights", "Advisor QA"] as const;
type Tab = (typeof TABS)[number];

const REASON: Record<string, string> = {
  asked_for_human: "Asked for a person",
  wants_expert: "Wants an expert visit",
  abandoned_mid_chat: "Left mid-chat",
  saw_offer_did_not_buy: "Saw offer, didn't buy",
  kyc_failed: "KYC failed",
};
const OWNER: Record<string, string> = { field_sales: "Field sales", channel_partner: "Channel partner", telesales: "Telesales" };
const SEG: Record<string, string> = { micro: "Micro retail", prof: "Professional", multi: "Multi-site", mfg: "Manufacturer" };
const pct = (n: number) => `${(n * 100).toFixed(1)}%`;

function ScorePill({ score, p }: { score: number; p: number }) {
  const tone = score >= 60 ? "bg-ok-soft text-ok" : score >= 40 ? "bg-warn-soft text-warn" : "bg-surface-2 text-muted";
  return (
    <span className={`rounded-full px-2 py-0.5 text-xs font-semibold tabular ${tone}`} title={`Expected activation ${pct(p)}`}>
      {score}
    </span>
  );
}

export default function BackOffice() {
  const [tab, setTab] = useState<Tab>("Queue");
  const [queue, setQueue] = useState<QueueItem[]>([]);
  const [orders, setOrders] = useState<Awaited<ReturnType<typeof api.boOrders>>>([]);
  const [calls, setCalls] = useState<CallItem[]>([]);
  const [ins, setIns] = useState<Insights | null>(null);
  const [qa, setQa] = useState<ScenarioRun | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    Promise.all([api.queue(), api.boOrders()])
      .then(([q, o]) => {
        setQueue(q);
        setOrders(o);
        setError(null);
      })
      .catch(() => setError("Backend not reachable."));
  }, []);

  useEffect(() => {
    load();
  }, [load]);
  useEffect(() => {
    if (tab === "Call-back list" && calls.length === 0) api.callList().then(setCalls).catch(() => {});
    if (tab === "Insights" && !ins) api.insights().then(setIns).catch(() => {});
    if (tab === "Advisor QA" && !qa) api.scenarios().then(setQa).catch(() => {});
  }, [tab, calls.length, ins, qa]);

  return (
    <>
      <header className="sticky top-0 z-20 border-b border-border bg-surface/95 backdrop-blur">
        <div className="mx-auto flex h-14 max-w-6xl items-center justify-between gap-3 px-4">
          <div className="flex items-center gap-3">
            <Logo />
            <span className="rounded-md bg-surface-2 px-2 py-0.5 text-xs text-muted">Back-office</span>
          </div>
          <div className="flex gap-2">
            <Link href="/impact" className="rounded-lg bg-foreground px-3 py-1.5 text-sm text-background">
              Impact simulator
            </Link>
            <button onClick={load} className="rounded-lg border border-border px-3 py-1.5 text-sm">
              Refresh
            </button>
          </div>
        </div>
        <nav className="mx-auto flex max-w-6xl gap-1 overflow-x-auto px-4" role="tablist">
          {TABS.map((t) => (
            <button
              key={t}
              role="tab"
              aria-selected={tab === t}
              onClick={() => setTab(t)}
              className={`whitespace-nowrap border-b-2 px-3 py-2 text-sm ${tab === t ? "border-brand font-semibold" : "border-transparent text-muted"}`}
            >
              {t}
              {t === "Queue" && queue.length > 0 && <span className="ml-1.5 rounded-full bg-brand px-1.5 text-xs text-brand-ink">{queue.length}</span>}
            </button>
          ))}
        </nav>
      </header>

      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-5">
        {error && <p className="mb-4 rounded-lg bg-bad-soft p-3 text-sm text-bad">{error}</p>}

        {tab === "Queue" && (
          <section>
            <p className="mb-3 text-sm text-muted">
              Leads the digital journey could not close, ranked by propensity score. Partner-sourced leads stay with the partner.
            </p>
            {queue.length === 0 ? (
              <p className="rounded-xl border border-dashed border-border p-6 text-center text-muted">Nothing waiting. Every lead self-served.</p>
            ) : (
              <div className="overflow-x-auto rounded-xl border border-border bg-surface">
                <table className="w-full text-sm">
                  <thead className="bg-surface-2 text-left text-xs text-muted">
                    <tr>
                      <th className="px-3 py-2">Score</th>
                      <th className="px-3 py-2">Business</th>
                      <th className="px-3 py-2">Why it&apos;s here</th>
                      <th className="px-3 py-2">Offer</th>
                      <th className="px-3 py-2">Route to</th>
                      <th className="px-3 py-2">Ref</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {queue.map((q) => (
                      <tr key={q.id}>
                        <td className="px-3 py-2">
                          <ScorePill score={q.score} p={q.expected_activation} />
                        </td>
                        <td className="px-3 py-2">
                          <p className="font-medium">{q.business ?? "Unknown"}</p>
                          <p className="text-xs text-muted">
                            {[q.city, q.segment && SEG[q.segment], q.employees && `${q.employees} staff`, q.sites && `${q.sites} site(s)`]
                              .filter(Boolean)
                              .join(" · ")}
                          </p>
                        </td>
                        <td className="px-3 py-2">
                          {REASON[q.reason] ?? q.reason}
                          {q.kyc_issues?.map((k) => (
                            <p key={k} className="text-xs text-bad">
                              {k}
                            </p>
                          ))}
                        </td>
                        <td className="px-3 py-2 tabular">{q.offer_monthly ? inr(q.offer_monthly) : "–"}</td>
                        <td className="px-3 py-2">{q.partner_id ? `Partner ${q.partner_id}` : OWNER[q.owner]}</td>
                        <td className="px-3 py-2 text-xs">
                          {q.kind === "order" ? (
                            <Link className="underline" href={`/order/${q.id}`}>
                              {q.id}
                            </Link>
                          ) : (
                            <Link className="underline" href={`/advisor?session=${q.id}`}>
                              {q.id}
                            </Link>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        )}

        {tab === "Orders" && (
          <section className="overflow-x-auto rounded-xl border border-border bg-surface">
            <table className="w-full text-sm">
              <thead className="bg-surface-2 text-left text-xs text-muted">
                <tr>
                  <th className="px-3 py-2">Order</th>
                  <th className="px-3 py-2">Business</th>
                  <th className="px-3 py-2">Monthly</th>
                  <th className="px-3 py-2">KYC</th>
                  <th className="px-3 py-2">Status</th>
                  <th className="px-3 py-2">Field update</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {orders.map((o) => (
                  <tr key={o.id}>
                    <td className="px-3 py-2">
                      <Link className="underline" href={`/order/${o.id}`}>
                        {o.id}
                      </Link>
                    </td>
                    <td className="px-3 py-2">
                      {o.business} <span className="text-muted">· {o.city}</span>
                    </td>
                    <td className="px-3 py-2 tabular">{inr(o.monthly)}</td>
                    <td className="px-3 py-2">{o.kyc ?? "pending"}</td>
                    <td className="px-3 py-2">{o.status.replaceAll("_", " ")}</td>
                    <td className="px-3 py-2">
                      <button
                        disabled={o.status === "activated" || o.status === "kyc_action_needed"}
                        onClick={async () => {
                          await api.advance(o.id).catch(() => {});
                          load();
                        }}
                        className="rounded-lg border border-border px-2 py-1 text-xs disabled:opacity-40"
                      >
                        Advance stage →
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {orders.length === 0 && <p className="p-6 text-center text-muted">No orders yet.</p>}
          </section>
        )}

        {tab === "Call-back list" && (
          <section>
            <p className="mb-3 text-sm text-muted">
              Historical leads dropped for fixable reasons (unreachable, slow quote, paperwork), ranked by the propensity model. Hand these to
              field sales or partners first.
            </p>
            <div className="overflow-x-auto rounded-xl border border-border bg-surface">
              <table className="w-full text-sm">
                <thead className="bg-surface-2 text-left text-xs text-muted">
                  <tr>
                    <th className="px-3 py-2">Score</th>
                    <th className="px-3 py-2">Lead</th>
                    <th className="px-3 py-2">Dropped because</th>
                    <th className="px-3 py-2">Source</th>
                    <th className="px-3 py-2">Route to</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {calls.map((c) => (
                    <tr key={c.lead_id}>
                      <td className="px-3 py-2">
                        <ScorePill score={c.score} p={c.expected_activation} />
                      </td>
                      <td className="px-3 py-2">
                        <p className="font-medium">{c.business}</p>
                        <p className="text-xs text-muted">
                          {c.lead_id} · {c.business_type} · {c.city}
                        </p>
                      </td>
                      <td className="px-3 py-2">{c.drop_reason}</td>
                      <td className="px-3 py-2">{c.source}</td>
                      <td className="px-3 py-2">{OWNER[c.owner]}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}

        {tab === "Insights" && ins && (
          <section className="space-y-5">
            <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
              {[
                ["Lead → activation", pct(ins.activation_rate)],
                ["Days to activate", String(ins.avg_days_to_activate)],
                ["Status calls / customer", String(ins.avg_follow_up_calls)],
                ["Cost per activation", inr(ins.cac_per_activation)],
              ].map(([k, v]) => (
                <div key={k} className="rounded-xl border border-border bg-surface p-4">
                  <p className="text-xs text-muted">{k}</p>
                  <p className="text-2xl font-bold tabular">{v}</p>
                </div>
              ))}
            </div>

            <div className="grid gap-5 lg:grid-cols-2">
              <div className="rounded-xl border border-border bg-surface p-4">
                <h3 className="font-semibold">Funnel, Apr–Jun 2026</h3>
                <p className="mb-3 text-xs text-muted">Leads reaching each stage. Biggest drop: needs assessed → quote accepted.</p>
                <Bars
                  label="Funnel"
                  highlight="Quote accepted"
                  data={ins.funnel.map((f, i) => ({
                    label: f.stage,
                    value: f.count,
                    note: i ? `${pct(f.count / ins.funnel[i - 1].count)} of previous stage` : undefined,
                  }))}
                />
              </div>
              <div className="rounded-xl border border-border bg-surface p-4">
                <h3 className="font-semibold">Why leads drop</h3>
                <p className="mb-3 text-xs text-muted">Top reasons. Most are friction the digital journey removes.</p>
                <Bars label="Drop reasons" data={ins.drop_reasons.map((d) => ({ label: d.reason, value: d.count }))} />
              </div>
              <div className="rounded-xl border border-border bg-surface p-4">
                <h3 className="font-semibold">6-month churn by status calls</h3>
                <p className="mb-3 text-xs text-muted">Customers who chased status more often churned more. The tracker exists for this.</p>
                <Bars
                  label="Churn by follow-up calls"
                  format={pct}
                  data={ins.follow_up_vs_churn.map((r) => ({
                    label: `${r.calls} call${r.calls > 1 ? "s" : ""}`,
                    value: r.churn_6m,
                    note: `${r.customers} customers · NPS ${r.nps}`,
                  }))}
                />
              </div>
              <div className="rounded-xl border border-border bg-surface p-4">
                <h3 className="font-semibold">Propensity model</h3>
                <p className="mb-3 text-xs text-muted">
                  Logistic regression on lead-time facts only. Hold-out AUC <b className="text-foreground">{ins.model.auc}</b>.
                </p>
                <ul className="space-y-1 text-sm">
                  {ins.model.drivers.map((d) => (
                    <li key={d.feature} className="flex justify-between gap-2">
                      <span className="truncate text-muted">{d.feature.replaceAll("_", " ")}</span>
                      <span className={`tabular ${d.weight > 0 ? "text-ok" : "text-bad"}`}>
                        {d.weight > 0 ? "▲" : "▼"} {Math.abs(d.weight)}
                      </span>
                    </li>
                  ))}
                </ul>
                <p className="mt-3 rounded-lg bg-bad-soft p-2 text-xs text-bad">
                  ⚠ {ins.activated_on_inactive_gstin} customers were activated on a cancelled or suspended GSTIN. Smart KYC now blocks this.
                </p>
              </div>
            </div>

            <div className="overflow-x-auto rounded-xl border border-border bg-surface">
              <table className="w-full text-sm">
                <thead className="bg-surface-2 text-left text-xs text-muted">
                  <tr>
                    <th className="px-3 py-2">Segment</th>
                    <th className="px-3 py-2 text-right">Leads</th>
                    <th className="px-3 py-2 text-right">Conversion</th>
                    <th className="px-3 py-2 text-right">Cost / activation</th>
                    <th className="px-3 py-2 text-right">Median bundle / mo</th>
                    <th className="px-3 py-2 text-right">6-mo churn</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border tabular">
                  {ins.segments.map((s) => (
                    <tr key={s.segment}>
                      <td className="px-3 py-2">{s.name}</td>
                      <td className="px-3 py-2 text-right">{s.leads.toLocaleString("en-IN")}</td>
                      <td className="px-3 py-2 text-right">{pct(s.conversion)}</td>
                      <td className="px-3 py-2 text-right">{inr(s.cac_per_activation)}</td>
                      <td className="px-3 py-2 text-right">{inr(s.median_monthly)}</td>
                      <td className="px-3 py-2 text-right">{pct(s.churn_6m)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}
        {tab === "Insights" && !ins && <p className="text-muted">Loading…</p>}

        {tab === "Advisor QA" && !qa && <p className="text-muted">Running scenarios…</p>}
        {tab === "Advisor QA" && qa && (
          <section className="space-y-4">
            <div className="grid grid-cols-3 gap-3">
              {[
                ["Scenarios passing", `${qa.passed} / ${qa.total}`],
                ["Avg. turns to a bundle", String(qa.avg_turns)],
                ["Rule violations", String(qa.results.filter((r) => r.failures.some((f) => f.includes("breaks rules"))).length)],
              ].map(([k, v]) => (
                <div key={k} className="rounded-xl border border-border bg-surface p-4">
                  <p className="text-xs text-muted">{k}</p>
                  <p className="text-2xl font-bold tabular">{v}</p>
                </div>
              ))}
            </div>
            <p className="text-sm text-muted">
              Each scenario types a real owner message into the advisor, answers whatever it asks, and checks the recommended bundle:
              must-include and must-exclude products, quantities, segment, and that every tier passes the rules engine.
            </p>
            <ul className="space-y-2">
              {qa.results.map((r) => (
                <li key={r.id} className="rounded-xl border border-border bg-surface p-4">
                  <div className="flex flex-wrap items-baseline justify-between gap-2">
                    <p className="font-semibold">
                      <span className={`mr-2 rounded-full px-2 py-0.5 text-xs ${r.passed ? "bg-ok-soft text-ok" : "bg-bad-soft text-bad"}`}>
                        {r.passed ? "✓ pass" : "✕ fail"}
                      </span>
                      {r.id} · {r.title}
                    </p>
                    <p className="text-sm tabular text-muted">
                      {r.turns} turns · {inr(r.monthly_total)}/mo · {SEG[r.segment] ?? r.segment}
                    </p>
                  </div>
                  <p className="mt-1 text-sm italic text-muted">&ldquo;{r.input}&rdquo;</p>
                  <p className="mt-2 text-sm">{r.bundle.map((b) => `${b.name}${b.qty > 1 ? ` ×${b.qty}` : ""}`).join(" · ")}</p>
                  {r.excluded.map((e) => (
                    <p key={e} className="text-xs text-warn">
                      ⊘ {e}
                    </p>
                  ))}
                  {r.failures.map((f) => (
                    <p key={f} className="text-xs text-bad">
                      {f}
                    </p>
                  ))}
                </li>
              ))}
            </ul>
          </section>
        )}
      </main>
    </>
  );
}
