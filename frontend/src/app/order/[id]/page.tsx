"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { Suspense, useCallback, useEffect, useState } from "react";
import { Header } from "@/components/Header";
import { api, inr, type Order } from "@/lib/api";
import { t, useLang } from "@/lib/i18n";

const fmt = (iso?: string | null, withTime = false) =>
  iso
    ? new Date(iso).toLocaleString("en-IN", {
        day: "numeric",
        month: "short",
        ...(withTime ? { hour: "numeric", minute: "2-digit" } : {}),
      })
    : "";

function slotOptions(): string[] {
  const out: string[] = [];
  const d = new Date();
  for (let i = 1; out.length < 6; i++) {
    const day = new Date(d.getTime() + i * 86400000);
    if (day.getDay() === 0) continue;
    const label = day.toLocaleDateString("en-IN", { weekday: "short", day: "numeric", month: "short" });
    out.push(`${label}, 10am–1pm`, `${label}, 2pm–6pm`);
  }
  return out.slice(0, 6);
}

const DOT: Record<string, string> = {
  done: "bg-ok text-white",
  current: "bg-brand text-brand-ink ring-4 ring-brand-soft",
  next: "border-2 border-brand bg-surface",
  upcoming: "border-2 border-border bg-surface",
  blocked: "bg-bad text-white",
};

function TrackerPageInner() {
  const { id } = useParams<{ id: string }>();
  const [lang, setLang] = useLang();
  const [order, setOrder] = useState<Order | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const load = useCallback(() => {
    api.order(id).then(setOrder).catch(() => setError("Order not found. Check the ID and try again."));
  }, [id]);

  useEffect(() => {
    load();
    const h = setInterval(load, 10000); // live updates while the page is open
    return () => clearInterval(h);
  }, [load]);

  if (error) return <p className="p-6">{error}</p>;
  if (!order) return <p className="p-6 text-muted">…</p>;
  const tr = order.tracker;
  const needsKyc = !order.consent?.accepted || order.status === "kyc_action_needed" || !order.kyc;
  const canPickSlot = ["kyc_verified", "feasibility_ok"].includes(order.status) && !tr.slot;

  return (
    <>
      <Header lang={lang} setLang={setLang} title={order.id} backHref="/" />
      <main className="mx-auto w-full max-w-2xl flex-1 space-y-4 px-4 py-4 pb-16">
        <section className="rounded-2xl border border-border bg-surface p-4">
          <p className="text-sm text-muted">{t(lang, "eta")}</p>
          <p className="text-2xl font-bold">{order.status === "activated" ? "Live ✓" : fmt(tr.eta)}</p>
          <p className="mt-1 text-sm text-muted">
            {order.profile.business_type} · {order.profile.city} · {inr(order.quote.totals.monthly_total)}
            {t(lang, "perMonth")}
          </p>
          {order.esign?.signed && (
            <p className="mt-2 text-xs text-ok">
              ✓ Agreement e-signed · SHA-256 {order.esign.document_hash?.slice(0, 12)}…
            </p>
          )}
          {needsKyc && (
            <Link href={`/order/${id}/kyc`} className="mt-3 block rounded-xl bg-brand py-3 text-center font-semibold text-brand-ink">
              {order.status === "kyc_action_needed" ? "Fix documents →" : "Complete KYC (2 min) →"}
            </Link>
          )}
        </section>

        <section className="rounded-2xl border border-border bg-surface p-4">
          <ol className="relative">
            {tr.stages.map((s, i) => (
              <li key={s.stage} className="relative flex gap-3 pb-5 last:pb-0">
                {i < tr.stages.length - 1 && <span className="absolute left-[11px] top-6 h-full w-0.5 bg-border" aria-hidden />}
                <span className={`relative z-10 grid h-6 w-6 shrink-0 place-items-center rounded-full text-xs ${DOT[s.state]}`}>
                  {s.state === "done" ? "✓" : s.state === "blocked" ? "!" : ""}
                </span>
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-baseline justify-between gap-x-2">
                    <p className={`font-medium ${s.state === "upcoming" ? "text-muted" : ""}`}>{s.title}</p>
                    <p className="text-xs text-muted">
                      {s.at ? fmt(s.at, true) : s.expected ? `expected ${fmt(s.expected)}` : ""}
                    </p>
                  </div>
                  {(s.state === "current" || s.state === "blocked" || s.state === "next") && <p className="text-sm text-muted">{s.body}</p>}
                </div>
              </li>
            ))}
          </ol>
        </section>

        {canPickSlot && (
          <section className="rounded-2xl border border-border bg-surface p-4">
            <h2 className="mb-3 font-semibold">{t(lang, "chooseSlot")}</h2>
            <div className="grid grid-cols-2 gap-2">
              {slotOptions().map((s) => (
                <button
                  key={s}
                  onClick={async () => setOrder(await api.slot(id, s))}
                  className="rounded-xl border border-border px-2 py-2 text-sm hover:border-brand"
                >
                  {s}
                </button>
              ))}
            </div>
          </section>
        )}
        {tr.slot && <p className="rounded-xl bg-ok-soft p-3 text-sm text-ok">🗓 Installation slot: {tr.slot}</p>}

        <section className="rounded-2xl border border-border bg-surface p-4">
          <h2 className="mb-2 font-semibold">{t(lang, "yourBundle")}</h2>
          <ul className="divide-y divide-border text-sm">
            {tr.products.map((p) => {
              const line = order.quote.lines.find((l) => l.product_id === p.product_id);
              return (
                <li key={p.product_id} className="flex justify-between gap-2 py-2">
                  <span>
                    {p.name}
                    {line && line.quantity > 1 ? ` × ${line.quantity}` : ""}
                  </span>
                  <span className="text-muted">{order.status === "activated" ? "Active" : `by ${fmt(p.ready_by)}`}</span>
                </li>
              );
            })}
          </ul>
        </section>

        <section className="rounded-2xl border border-border bg-surface p-4">
          <h2 className="mb-2 font-semibold">{t(lang, "updates")}</h2>
          <ul className="space-y-2">
            {[...tr.notifications].reverse().map((n, i) => (
              <li key={i} className="rounded-xl bg-[#e7f8ee] p-3 text-sm text-[#0b3d1f] dark:bg-[#12301d] dark:text-[#cdeed9]">
                <p className="font-semibold">{n.title}</p>
                <p>{n.body}</p>
                <p className="mt-1 text-right text-[11px] opacity-70">WhatsApp · {fmt(n.at, true)}</p>
              </li>
            ))}
          </ul>
        </section>

        <Link
          href={`/account/${id}`}
          className={`block rounded-2xl border p-4 text-center font-semibold ${
            order.status === "activated" ? "border-brand bg-brand text-brand-ink" : "border-border bg-surface"
          }`}
        >
          My business account: one bill, one support channel →
        </Link>

        <section className="space-y-2 text-center text-sm">
          <Link href="/advisor?new=1" className="block text-muted underline">
            {t(lang, "help")}
          </Link>
          {order.consent?.accepted && !order.consent.withdrawn_at && (
            <button
              onClick={async () => {
                if (!confirm("This deletes your uploaded document details. Continue?")) return;
                const r = await api.withdraw(id);
                setNotice(r.message);
                load();
              }}
              className="text-bad underline"
            >
              {t(lang, "deleteData")}
            </button>
          )}
          {notice && <p className="text-ok">{notice}</p>}
        </section>
      </main>
    </>
  );
}

export default function TrackerPage() {
  return (
    <Suspense fallback={<p className="p-6 text-muted">…</p>}>
      <TrackerPageInner />
    </Suspense>
  );
}
