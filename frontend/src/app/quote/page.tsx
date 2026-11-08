"use client";

import Link from "next/link";

import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useMemo, useState } from "react";
import { Header } from "@/components/Header";
import { ApiError, api, inr, type Profile, type QuoteLine, type Session, type Totals } from "@/lib/api";
import { t, useLang } from "@/lib/i18n";

type Row = QuoteLine & { on: boolean; core: boolean };

function Quote() {
  const [lang, setLang] = useLang();
  const router = useRouter();
  const params = useSearchParams();
  const sid = params.get("session");
  const [session, setSession] = useState<Session | null>(null);
  const [tier, setTier] = useState<string | null>(params.get("tier"));
  const [rows, setRows] = useState<Row[]>([]);
  const [contract, setContract] = useState(12);
  const [quoted, setTotals] = useState<Totals | null>(null);
  const [prices, setPrices] = useState<Record<string, QuoteLine>>({});
  const [problems, setProblems] = useState<{ product_id: string; message: string }[]>([]);
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [placing, setPlacing] = useState(false);
  const [override, setOverride] = useState<Profile | null>(null);
  const [pin, setPin] = useState("");
  const [coverage, setCoverage] = useState<{ ok: boolean; text: string } | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!sid) return;
    api
      .getSession(sid)
      .then((s) => {
        setSession(s);
        if (!s.recommendation) return;
        const name = tier && s.recommendation.tiers[tier] ? tier : (s.recommendation.default ?? Object.keys(s.recommendation.tiers)[0]);
        setTier(name);
        const core = s.recommendation.tiers[name].lines.map((l) => ({ ...l, on: true, core: true }));
        const coreIds = new Set(core.map((l) => l.product_id));
        const extras = s.recommendation.addons.filter((a) => !coreIds.has(a.product_id)).map((l) => ({ ...l, on: false, core: false }));
        setRows([...core, ...extras]);
      })
      .catch(() => setError("Session not found."));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sid]);

  const profile: Profile | null = override ?? session?.profile ?? null;

  const checkCoverage = async () => {
    if (!session || !profile) return;
    const r = await api.feasibility(pin, typeof profile.city_tier === "number" ? profile.city_tier : undefined);
    if (!r.valid) {
      setCoverage({ ok: false, text: "Please enter a valid 6-digit PIN code." });
      return;
    }
    const next = { ...profile, pin: r.pin, fibre_available: !!r.fibre };
    setOverride(next);
    setCoverage({ ok: !!r.fibre, text: r.message ?? "" });
    if (!r.fibre) {
      // Re-plan the bundle for this address: fibre lines become 5G AirFiber, dependents stay valid.
      const offer = await api.offer(next, contract, lang);
      const name = tier && offer.tiers[tier] ? tier : (offer.default ?? Object.keys(offer.tiers)[0]);
      const core = offer.tiers[name].lines.map((l) => ({ ...l, on: true, core: true }));
      const ids = new Set(core.map((l) => l.product_id));
      setRows([...core, ...offer.addons.filter((a) => !ids.has(a.product_id)).map((l) => ({ ...l, on: false, core: false }))]);
    }
  };

  const selected = useMemo(
    () => rows.filter((r) => r.on).map((r) => ({ product_id: r.product_id, quantity: r.quantity })),
    [rows],
  );

  // Live re-pricing on every change; the server is the only source of prices.
  useEffect(() => {
    if (!profile || selected.length === 0) return;
    const h = setTimeout(() => {
      api
        .quote(profile, selected, contract, lang)
        .then((q) => {
          setTotals(q.totals);
          setPrices(Object.fromEntries(q.lines.map((l) => [l.product_id, l])));
          setProblems(q.problems);
        })
        .catch(() => setError("Could not update the price."));
    }, 150);
    return () => clearTimeout(h);
  }, [profile, selected, contract, lang]);

  const totals = selected.length ? quoted : null;

  const update = (pid: string, patch: Partial<Row>) =>
    setRows((rs) => rs.map((r) => (r.product_id === pid ? { ...r, ...patch } : r)));

  const place = async () => {
    if (!session) return;
    setPlacing(true);
    setError(null);
    try {
      const o = await api.createOrder({
        session_id: session.id,
        profile: profile ?? session.profile,
        items: selected,
        contract_months: contract,
        lang,
        contact: { name, phone },
      });
      router.push(`/order/${o.id}/kyc`);
    } catch (e) {
      if (e instanceof ApiError && e.status === 422) {
        setError("Some items can't be combined. Please check the highlighted lines.");
      } else setError("Could not place the order. Please try again.");
      setPlacing(false);
    }
  };

  if (!sid)
    return (
      <main className="mx-auto w-full max-w-xl flex-1 px-4 py-16 text-center">
        <p className="eyebrow mb-3">Quote</p>
        <h1 className="text-[34px]">Your quote starts with three questions.</h1>
        <p className="mt-3 text-muted">Tell the advisor about your business and it builds a bundle with one monthly price.</p>
        <Link href="/advisor" className="mt-8 inline-flex h-12 items-center rounded-full bg-foreground px-7 font-semibold text-background">
          Start with the advisor →
        </Link>
      </main>
    );

  const problemFor = (pid: string) => problems.filter((p) => p.product_id === pid);
  const section = (core: boolean) => rows.filter((r) => r.core === core);

  const renderRow = (r: Row) => {
    const priced = prices[r.product_id];
    const probs = problemFor(r.product_id);
    const perUnit = !["per account", "per pack"].includes(r.unit);
    return (
      <li key={r.product_id} className={`py-3 ${r.on ? "" : "opacity-70"}`}>
        <div className="flex items-start gap-3">
          <input
            type="checkbox"
            checked={r.on}
            onChange={(e) => update(r.product_id, { on: e.target.checked })}
            className="mt-1 h-5 w-5 accent-[var(--brand)]"
            aria-label={r.name}
          />
          <div className="min-w-0 flex-1">
            <div className="flex justify-between gap-2">
              <p className="font-medium">{r.name}</p>
              <p className="shrink-0 tabular">{inr(r.on ? (priced?.monthly ?? r.monthly) : r.unit_price * r.quantity)}</p>
            </div>
            <p className="text-xs text-muted">{r.why || r.description}</p>
            {perUnit && r.on && (
              <div className="mt-2 flex items-center gap-2 text-sm">
                <button
                  aria-label="Fewer"
                  onClick={() => update(r.product_id, { quantity: Math.max(1, r.quantity - 1) })}
                  className="h-7 w-7 rounded-full border border-border"
                >
                  −
                </button>
                <span className="w-8 text-center tabular">{r.quantity}</span>
                <button
                  aria-label="More"
                  onClick={() => update(r.product_id, { quantity: r.quantity + 1 })}
                  className="h-7 w-7 rounded-full border border-border"
                >
                  +
                </button>
                <span className="text-xs text-muted">
                  {r.unit} · {inr(priced?.unit_price ?? r.unit_price)} each
                </span>
              </div>
            )}
            {probs.map((p) => (
              <p key={p.message} className="mt-1 text-xs text-bad">
                ⚠ {p.message}
              </p>
            ))}
          </div>
        </div>
      </li>
    );
  };

  return (
    <>
      <Header lang={lang} setLang={setLang} title={t(lang, "yourBundle")} backHref={`/advisor?session=${sid}`} />
      <main className="mx-auto w-full max-w-3xl flex-1 px-4 pb-48">
        {session?.recommendation && Object.keys(session.recommendation.tiers).length > 1 && (
          <div className="mt-4 flex gap-2">
            {Object.entries(session.recommendation.tiers).map(([n, tr]) => (
              <button
                key={n}
                onClick={() => {
                  setTier(n);
                  const core = tr.lines.map((l) => ({ ...l, on: true, core: true }));
                  const ids = new Set(core.map((l) => l.product_id));
                  setRows([
                    ...core,
                    ...session.recommendation!.addons.filter((a) => !ids.has(a.product_id)).map((l) => ({ ...l, on: false, core: false })),
                  ]);
                }}
                className={`flex-1 rounded-xl border px-3 py-2 text-sm ${n === tier ? "border-foreground bg-brand-soft font-semibold text-brand" : "border-border bg-surface"}`}
              >
                {tr.label}
              </button>
            ))}
          </div>
        )}

        <section className="mt-4 rounded-[20px] border border-border bg-surface px-4">
          <ul className="divide-y divide-border">
            {section(true).map(renderRow)}
          </ul>
        </section>

        {section(false).length > 0 && (
          <section className="mt-4">
            <h2 className="mb-2 text-[22px]">{t(lang, "addons")}</h2>
            <ul className="divide-y divide-border rounded-[20px] border border-border bg-surface px-4">
              {section(false).map(renderRow)}
            </ul>
          </section>
        )}

        <section className="mt-4 rounded-[20px] border border-border bg-surface p-4">
          <h2 className="text-[22px]">Check coverage at your address</h2>
          <form
            className="mt-2 flex gap-2"
            onSubmit={(e) => {
              e.preventDefault();
              checkCoverage().catch(() => setCoverage({ ok: false, text: "Could not check coverage." }));
            }}
          >
            <input
              value={pin}
              onChange={(e) => setPin(e.target.value.replace(/\D/g, "").slice(0, 6))}
              inputMode="numeric"
              placeholder="PIN code"
              className="w-32 rounded-lg border border-border bg-background px-3 py-2 tabular"
            />
            <button disabled={pin.length !== 6} className="rounded-lg bg-foreground px-4 text-background disabled:opacity-40">
              Check
            </button>
          </form>
          {coverage && <p className={`mt-2 text-sm ${coverage.ok ? "text-ok" : "text-warn"}`}>{coverage.ok ? "✓ " : "ⓘ "}{coverage.text}</p>}
        </section>

        <section className="mt-4 rounded-[20px] border border-border bg-surface p-4">
          <h2 className="text-[22px]">{t(lang, "contract")}</h2>
          <div className="mt-3 grid grid-cols-3 gap-2">
            {[12, 24, 36].map((m) => (
              <button
                key={m}
                onClick={() => setContract(m)}
                className={`rounded-xl border py-2 ${m === contract ? "border-foreground bg-brand-soft font-semibold text-brand" : "border-border"}`}
              >
                {m} {t(lang, "months")}
              </button>
            ))}
          </div>
          {totals && (
            <dl className="mt-4 space-y-1 text-sm">
              <div className="flex justify-between">
                <dt className="text-muted">{t(lang, "subtotal")}</dt>
                <dd className="tabular">{inr(totals.monthly_before_tax)}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-muted">{t(lang, "gst")}</dt>
                <dd className="tabular">{inr(totals.monthly_gst)}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-muted">{t(lang, "oneTime")}</dt>
                <dd className="tabular">{inr(totals.setup_total)}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-muted">{t(lang, "firstBill")}</dt>
                <dd className="tabular">{inr(totals.first_bill)}</dd>
              </div>
            </dl>
          )}
        </section>

        <section className="mt-4 grid gap-3 rounded-[20px] border border-border bg-surface p-4 sm:grid-cols-2">
          <label className="text-sm">
            {t(lang, "contactName")}
            <input value={name} onChange={(e) => setName(e.target.value)} autoComplete="name" className="mt-1 w-full rounded-lg border border-border bg-background px-3 py-2" />
          </label>
          <label className="text-sm">
            {t(lang, "contactPhone")}
            <input
              value={phone}
              onChange={(e) => setPhone(e.target.value.replace(/[^\d+ ]/g, ""))}
              inputMode="tel"
              autoComplete="tel"
              className="mt-1 w-full rounded-lg border border-border bg-background px-3 py-2"
            />
          </label>
          <p className="text-xs text-muted sm:col-span-2">We only use your number to send order updates.</p>
        </section>
        {error && <p className="mt-4 rounded-lg bg-bad-soft p-3 text-sm text-bad">{error}</p>}
      </main>

      <div className="fixed inset-x-0 bottom-0 border-t border-border bg-surface/95 backdrop-blur">
        <div className="mx-auto flex max-w-3xl items-center justify-between gap-4 px-4 py-3">
          <div>
            <p className="text-xs text-muted">{t(lang, "total")}</p>
            <p className="text-2xl font-bold tabular">
              {inr(totals?.monthly_total)}
              <span className="text-sm font-medium text-muted">{t(lang, "perMonth")}</span>
            </p>
            {totals && <p className="text-xs text-muted">{t(lang, "inclGst")} · {t(lang, "readyIn", { d: totals.ready_in_days })}</p>}
          </div>
          <button
            onClick={place}
            disabled={placing || !totals || problems.length > 0}
            className="h-12 rounded-full bg-saffron px-6 font-semibold text-[#1f1d1a] disabled:opacity-40"
          >
            {placing ? t(lang, "placing") : t(lang, "placeOrder")}
          </button>
        </div>
      </div>
    </>
  );
}

export default function QuotePage() {
  return (
    <Suspense>
      <Quote />
    </Suspense>
  );
}
