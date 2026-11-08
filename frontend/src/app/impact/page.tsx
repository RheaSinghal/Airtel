"use client";

import { useEffect, useState } from "react";
import { Bars } from "@/components/Bars";
import { Logo } from "@/components/Header";
import { api, inr, type Impact } from "@/lib/api";

const pct = (n: number) => `${(n * 100).toFixed(1)}%`;
const crore = (n: number) => `₹${(n / 1e7).toFixed(1)} Cr`;

type State = { levers: Record<string, number>; digital_share: number; status_calls: number };

export default function ImpactPage() {
  const [state, setState] = useState<State | null>(null);
  const [res, setRes] = useState<Impact | null>(null);
  const [preset, setPreset] = useState("conservative");
  const [error, setError] = useState<string | null>(null);

  // First load: server defaults (conservative)
  useEffect(() => {
    api
      .impact({})
      .then((r) => {
        setRes(r);
        setState({ levers: Object.fromEntries(r.levers.map((l) => [l.key, l.value])), digital_share: r.digital_share, status_calls: r.status_calls });
      })
      .catch(() => setError("Backend not reachable."));
  }, []);

  // Re-simulate on every change (debounced)
  useEffect(() => {
    if (!state) return;
    const h = setTimeout(() => api.impact(state).then(setRes).catch(() => {}), 120);
    return () => clearTimeout(h);
  }, [state]);

  if (error) return <p className="p-6">{error}</p>;
  if (!res || !state) return <p className="p-6 text-muted">Loading…</p>;
  const b = res.baseline;
  const s = res.scenario;
  const maxF = Math.max(...s.funnel.map((f) => f.count), ...b.funnel.map((f) => f.count));

  const tiles: [string, string, string, boolean][] = [
    ["Lead → activation", pct(b.rate), pct(s.rate), s.rate >= b.rate],
    ["Activations / quarter", b.activations.toLocaleString("en-IN"), s.activations.toLocaleString("en-IN"), true],
    ["Cost per activation", inr(b.cac), inr(s.cac), s.cac <= b.cac],
    ["Days to activate", String(b.days), String(s.days), true],
    ["6-month churn", pct(b.churn_6m), pct(s.churn_6m), s.churn_6m <= b.churn_6m],
    ["Annual recurring revenue", crore(b.arr), crore(s.arr), true],
  ];

  return (
    <>
      <header className="sticky top-0 z-20 border-b border-border bg-background/90 backdrop-blur">
        <div className="mx-auto flex h-14 max-w-6xl items-center justify-between gap-3 px-4">
          <div className="flex items-center gap-3">
            <Logo />
            <span className="hidden rounded-full bg-surface-2 px-2.5 py-0.5 text-xs text-muted sm:inline">Impact simulator</span>
          </div>
          <div className="flex gap-1 rounded-full border border-border p-0.5 text-sm" role="group" aria-label="Preset">
            {Object.keys(res.presets).map((p) => (
              <button
                key={p}
                onClick={() => {
                  setPreset(p);
                  setState(res.presets[p]);
                }}
                className={`rounded-full px-3 py-1.5 capitalize ${preset === p ? "bg-foreground text-background" : "text-muted"}`}
              >
                {p}
              </button>
            ))}
          </div>
        </div>
      </header>

      <main className="mx-auto grid w-full max-w-6xl flex-1 gap-5 px-4 py-5 lg:grid-cols-[minmax(0,22rem)_1fr]">
        <section className="space-y-4 rounded-[20px] border border-border bg-surface p-4 lg:sticky lg:top-20 lg:self-start">
          <h2 className="text-[22px]">What the digital journey fixes</h2>
          <p className="text-xs text-muted">Share of each drop reason we recover. Every number is computed from the 5,000 leads in smb_leads.csv.</p>
          {res.levers.map((l) => (
            <label key={l.key} className="block text-sm">
              <span className="flex justify-between gap-2">
                <span className="font-medium">{l.label}</span>
                <span className="tabular">{Math.round(state.levers[l.key] * 100)}%</span>
              </span>
              <input
                type="range"
                min={0}
                max={100}
                value={Math.round(state.levers[l.key] * 100)}
                onChange={(e) => {
                  setPreset("custom");
                  setState({ ...state, levers: { ...state.levers, [l.key]: Number(e.target.value) / 100 } });
                }}
                className="w-full accent-[var(--brand)]"
              />
              <span className="block text-xs text-muted">
                {l.stage}: {l.addresses.join(", ").toLowerCase()}
              </span>
            </label>
          ))}
          <label className="block text-sm">
            <span className="flex justify-between">
              <span className="font-medium">Leads served digitally</span>
              <span className="tabular">{Math.round(state.digital_share * 100)}%</span>
            </span>
            <input
              type="range"
              min={0}
              max={100}
              value={Math.round(state.digital_share * 100)}
              onChange={(e) => {
                setPreset("custom");
                setState({ ...state, digital_share: Number(e.target.value) / 100 });
              }}
              className="w-full accent-[var(--brand)]"
            />
            <span className="block text-xs text-muted">Digital leads cost like today&apos;s website leads.</span>
          </label>
          <label className="block text-sm">
            <span className="flex justify-between">
              <span className="font-medium">Status calls per customer</span>
              <span className="tabular">{state.status_calls.toFixed(1)}</span>
            </span>
            <input
              type="range"
              min={10}
              max={50}
              value={Math.round(state.status_calls * 10)}
              onChange={(e) => {
                setPreset("custom");
                setState({ ...state, status_calls: Number(e.target.value) / 10 });
              }}
              className="w-full accent-[var(--brand)]"
            />
            <span className="block text-xs text-muted">Today 3.0. The tracker and WhatsApp updates bring it down; churn follows the data.</span>
          </label>
        </section>

        <div className="min-w-0 space-y-5">
          <div className="grid grid-cols-2 gap-3 md:grid-cols-3">
            {tiles.map(([k, before, after, good]) => (
              <div key={k} className="rounded-xl border border-border bg-surface p-4">
                <p className="text-xs text-muted">{k}</p>
                <p className="text-2xl font-bold tabular">{after}</p>
                <p className={`text-xs ${good ? "text-ok" : "text-bad"}`}>today {before}</p>
              </div>
            ))}
          </div>

          <div className="rounded-xl border border-border bg-surface p-4">
            <div className="mb-3 flex flex-wrap items-baseline justify-between gap-2">
              <h3 className="font-semibold">Funnel, one quarter</h3>
              <div className="flex gap-3 text-xs text-muted" aria-label="Legend">
                <span className="flex items-center gap-1.5">
                  <span className="h-2.5 w-2.5 rounded-sm" style={{ background: "var(--muted)" }} /> Today
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="h-2.5 w-2.5 rounded-sm" style={{ background: "var(--chart-bar)" }} /> With Udyam Digital
                </span>
              </div>
            </div>
            <div className="space-y-2.5">
              {s.funnel.map((f, i) => (
                <div key={f.stage} className="grid grid-cols-[8rem_1fr] items-center gap-3 text-sm">
                  <span className="text-muted">{f.stage}</span>
                  <div className="space-y-0.5">
                    <div className="flex items-center gap-2" title={`Today: ${b.funnel[i].count.toLocaleString("en-IN")}`}>
                      <div className="h-2.5 rounded-r-[4px]" style={{ width: `${(b.funnel[i].count / maxF) * 100}%`, background: "var(--muted)" }} />
                      <span className="text-xs tabular text-muted">{b.funnel[i].count.toLocaleString("en-IN")}</span>
                    </div>
                    <div className="flex items-center gap-2" title={`With Udyam Digital: ${f.count.toLocaleString("en-IN")}`}>
                      <div className="h-2.5 rounded-r-[4px]" style={{ width: `${(f.count / maxF) * 100}%`, background: "var(--chart-bar)" }} />
                      <span className="text-xs font-semibold tabular">{f.count.toLocaleString("en-IN")}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-xl border border-border bg-surface p-4">
            <h3 className="font-semibold">Extra activations per quarter, by fix (each on its own)</h3>
            <p className="mb-3 text-xs text-muted">Together they compound: recovered leads also benefit from every later fix.</p>
            <Bars
              label="Contribution by lever"
              data={res.contributions.map((c) => ({ label: c.label, value: c.extra_activations }))}
              format={(n) => `+${n}`}
            />
          </div>

          <details className="rounded-xl border border-border bg-surface p-4 text-sm">
            <summary className="cursor-pointer font-semibold">Assumptions</summary>
            <ul className="mt-2 list-inside list-disc space-y-1 text-muted">
              {res.assumptions.map((a) => (
                <li key={a}>{a}</li>
              ))}
            </ul>
          </details>
        </div>
      </main>
    </>
  );
}
