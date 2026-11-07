"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import { Header } from "@/components/Header";
import { api, type Check, type DocResult, type Order } from "@/lib/api";
import { t, useLang } from "@/lib/i18n";

const SLOTS = [
  { id: "gst_certificate", en: "GST certificate", hi: "GST सर्टिफ़िकेट" },
  { id: "udyam_certificate", en: "Udyam certificate", hi: "Udyam सर्टिफ़िकेट" },
  { id: "signatory_id", en: "Authorised signatory ID", hi: "साइनेटरी ID" },
  { id: "address_proof", en: "Address proof (utility bill, < 90 days)", hi: "पते का प्रमाण (बिल, 90 दिन से कम)" },
] as const;

const FIELD_LABELS: Record<string, string> = {
  gstin: "GSTIN", legal_name: "Legal name", trade_name: "Trade name", constitution: "Constitution", address: "Address",
  date_of_liability: "Registered on", udyam_number: "Udyam no.", enterprise_name: "Enterprise", major_activity: "Activity",
  city: "City", state: "State", date_of_registration: "Registered on", name: "Name", designation: "Designation",
  business_name: "For business", id_number: "ID no.", valid_till: "Valid till", consumer_number: "Consumer no.",
  billed_to: "Billed to", bill_date: "Bill date", amount_due: "Amount due",
};

const STATUS_STYLE: Record<Check["status"], string> = {
  pass: "bg-ok-soft text-ok",
  warn: "bg-warn-soft text-warn",
  fail: "bg-bad-soft text-bad",
  info: "bg-surface-2 text-muted",
};
const STATUS_ICON: Record<Check["status"], string> = { pass: "✓", warn: "!", fail: "✕", info: "i" };

type Consent = Awaited<ReturnType<typeof api.consentText>>;

function KycPageInner() {
  const { id } = useParams<{ id: string }>();
  const [lang, setLang] = useLang();
  const [order, setOrder] = useState<Order | null>(null);
  const [consent, setConsent] = useState<Consent | null>(null);
  const [docs, setDocs] = useState<Record<string, DocResult>>({});
  const [busySlot, setBusySlot] = useState<string | null>(null);
  const [samples, setSamples] = useState<string[]>([]);
  const [sample, setSample] = useState("K03");
  const [noUdyam, setNoUdyam] = useState(false);
  const [result, setResult] = useState<{ verdict: string; checks: Check[]; blocked_products: { message: string }[] } | null>(null);
  const [verifying, setVerifying] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .order(id)
      .then((o) => {
        setOrder(o);
        const existing: Record<string, DocResult> = {};
        for (const [slot, d] of Object.entries(o.documents)) {
          existing[slot] = { slot, detected_type: d.detected_type, quality: d.quality as DocResult["quality"], fields: d.fields };
        }
        setDocs(existing);
        if (o.kyc) setResult({ verdict: o.kyc.verdict, checks: o.kyc.checks, blocked_products: [] });
      })
      .catch(() => setError("Order not found."));
    api.samples().then(setSamples).catch(() => {});
  }, [id]);

  useEffect(() => {
    api.consentText(lang).then(setConsent).catch(() => {});
  }, [lang]);

  const consented = !!order?.consent?.accepted && !order.consent.withdrawn_at;

  const accept = async () => {
    await api.consent(id, true);
    setOrder(await api.order(id));
  };

  const upload = async (slot: string, file?: File) => {
    setBusySlot(slot);
    setError(null);
    setResult(null);
    try {
      const r = file ? await api.upload(id, slot, file) : await api.uploadSample(id, slot, sample);
      setDocs((d) => ({ ...d, [slot]: r }));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Upload failed");
    } finally {
      setBusySlot(null);
    }
  };

  const loadAllSamples = async () => {
    for (const s of SLOTS) {
      if (s.id === "udyam_certificate" && noUdyam) continue;
      await upload(s.id).catch(() => {});
    }
  };

  const verify = async () => {
    setVerifying(true);
    try {
      const r = await api.verify(id, noUdyam ? false : null);
      setResult(r);
      setOrder(r.order);
    } catch {
      setError("Verification failed. Please try again.");
    } finally {
      setVerifying(false);
    }
  };

  if (error && !order) return <p className="p-6">{error}</p>;
  if (!order) return <p className="p-6 text-muted">…</p>;

  // ---- consent screen (DPDP: notice before collection, purpose, retention, rights)
  if (!consented) {
    return (
      <>
        <Header lang={lang} setLang={setLang} title={t(lang, "consentTitle")} />
        <main className="mx-auto w-full max-w-2xl flex-1 px-4 py-6">
          <p className="mb-4 rounded-xl bg-ok-soft p-3 text-sm text-ok">
            ✓ {t(lang, "orderPlaced")}: <b>{order.id}</b>
          </p>
          {consent && (
            <article className="space-y-4 rounded-2xl border border-border bg-surface p-5">
              <h2 className="text-lg font-semibold">{consent.title}</h2>
              <p>{consent.purpose}</p>
              <ul className="list-inside list-disc text-sm">
                {consent.data.map((d) => (
                  <li key={d}>{d}</li>
                ))}
              </ul>
              <p className="text-sm">{consent.how}</p>
              <p className="text-sm">{consent.share}</p>
              <p className="text-sm text-muted">{consent.rights}</p>
              <p className="text-xs text-muted">Consent version {consent.version} · DPDP Act, 2023</p>
            </article>
          )}
          <div className="mt-6 flex gap-3">
            <Link href={`/order/${id}`} className="flex-1 rounded-xl border border-border py-3 text-center">
              {t(lang, "decline")}
            </Link>
            <button onClick={accept} className="flex-[2] rounded-xl bg-brand py-3 font-semibold text-brand-ink">
              {t(lang, "agree")}
            </button>
          </div>
        </main>
      </>
    );
  }

  // Udyam can be missing: the server flags it, so the owner sees exactly what to fix.
  const ready = SLOTS.filter((s) => s.id !== "udyam_certificate").every((s) => docs[s.id]);

  return (
    <>
      <Header lang={lang} setLang={setLang} title={t(lang, "documents")} backHref={`/order/${id}`} />
      <main className="mx-auto w-full max-w-2xl flex-1 px-4 py-4 pb-32">
        {samples.length > 0 && (
          <div className="mb-4 flex flex-wrap items-center gap-2 rounded-xl border border-dashed border-border p-3 text-sm">
            <span className="text-muted">Demo: specimen applicant</span>
            <select value={sample} onChange={(e) => setSample(e.target.value)} className="rounded-lg border border-border bg-surface px-2 py-1">
              {samples.map((s) => (
                <option key={s}>{s}</option>
              ))}
            </select>
            <button onClick={loadAllSamples} disabled={!!busySlot} className="rounded-lg bg-foreground px-3 py-1 text-background">
              Load all 4
            </button>
          </div>
        )}

        <ul className="space-y-3">
          {SLOTS.map((s) => {
            const d = docs[s.id];
            const skipped = s.id === "udyam_certificate" && noUdyam;
            const slotChecks = result?.checks.filter((c) => c.doc === s.id && c.status !== "pass") ?? [];
            return (
              <li key={s.id} className={`rounded-2xl border border-border bg-surface p-4 ${skipped ? "opacity-60" : ""}`}>
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="font-medium">{lang === "hi" ? s.hi : s.en}</p>
                    {d && (
                      <p className={`text-xs ${d.quality.unreadable ? "text-bad" : "text-ok"}`}>
                        {d.quality.unreadable
                          ? "Too blurry to read. Please retake in good light."
                          : `Read ✓${d.quality.rotation_deg ? ` · straightened ${d.quality.rotation_deg}°` : ""}`}
                      </p>
                    )}
                  </div>
                  {!skipped && (
                    <div className="flex shrink-0 gap-2">
                      <label className="cursor-pointer rounded-lg bg-brand px-3 py-1.5 text-sm font-medium text-brand-ink">
                        {busySlot === s.id ? "…" : d ? "↻" : t(lang, "upload")}
                        <input
                          type="file"
                          accept="image/*"
                          capture="environment"
                          className="sr-only"
                          disabled={!!busySlot}
                          onChange={(e) => e.target.files?.[0] && upload(s.id, e.target.files[0])}
                        />
                      </label>
                      {samples.length > 0 && (
                        <button
                          onClick={() => upload(s.id)}
                          disabled={!!busySlot}
                          className="rounded-lg border border-border px-2 py-1.5 text-xs"
                          title={t(lang, "useSample")}
                        >
                          {sample}
                        </button>
                      )}
                    </div>
                  )}
                </div>
                {s.id === "udyam_certificate" && (
                  <label className="mt-2 flex items-center gap-2 text-xs text-muted">
                    <input type="checkbox" checked={noUdyam} onChange={(e) => setNoUdyam(e.target.checked)} />
                    My business is not Udyam-registered
                  </label>
                )}
                {d && !d.quality.unreadable && Object.keys(d.fields).length > 0 && (
                  <dl className="mt-3 grid grid-cols-[auto_1fr] gap-x-3 gap-y-1 rounded-lg bg-surface-2 p-3 text-sm">
                    {Object.entries(d.fields).map(([k, v]) => (
                      <div key={k} className="contents">
                        <dt className="text-muted">{FIELD_LABELS[k] ?? k}</dt>
                        <dd className="break-words">{v}</dd>
                      </div>
                    ))}
                  </dl>
                )}
                {slotChecks.map((c) => (
                  <p key={c.id} className={`mt-2 rounded-lg px-3 py-2 text-sm ${STATUS_STYLE[c.status]}`}>
                    {STATUS_ICON[c.status]} {c.message}
                  </p>
                ))}
              </li>
            );
          })}
        </ul>

        {result && (
          <section className="mt-5 rounded-2xl border border-border bg-surface p-4">
            <p
              className={`rounded-xl p-3 font-semibold ${
                result.verdict === "verified" ? "bg-ok-soft text-ok" : result.verdict === "rejected" ? "bg-bad-soft text-bad" : "bg-warn-soft text-warn"
              }`}
            >
              {result.verdict === "verified"
                ? "✓ All documents verified"
                : result.verdict === "rejected"
                  ? "Some documents need fixing before we can activate"
                  : "Verified, with notes for our team"}
            </p>
            <ul className="mt-3 space-y-1.5 text-sm">
              {result.checks.map((c) => (
                <li key={c.id} className="flex gap-2">
                  <span className={`grid h-5 w-5 shrink-0 place-items-center rounded-full text-xs ${STATUS_STYLE[c.status]}`}>{STATUS_ICON[c.status]}</span>
                  <span>{c.message}</span>
                </li>
              ))}
            </ul>
            {result.blocked_products?.length > 0 && (
              <div className="mt-3 rounded-lg bg-bad-soft p-3 text-sm text-bad">
                {result.blocked_products.map((b) => (
                  <p key={b.message}>⚠ {b.message}</p>
                ))}
              </div>
            )}
          </section>
        )}
        {error && <p className="mt-4 rounded-lg bg-bad-soft p-3 text-sm text-bad">{error}</p>}
      </main>

      <div className="fixed inset-x-0 bottom-0 border-t border-border bg-surface/95 backdrop-blur">
        <div className="mx-auto flex max-w-2xl gap-3 px-4 py-3">
          {result && (
            <Link href={`/order/${id}`} className="flex-1 rounded-xl border border-border py-3 text-center font-medium">
              {t(lang, "trackOrder")}
            </Link>
          )}
          <button
            onClick={verify}
            disabled={!ready || verifying || !!busySlot}
            className="flex-[2] rounded-xl bg-brand py-3 font-semibold text-brand-ink disabled:opacity-40"
          >
            {verifying ? t(lang, "verifying") : t(lang, "verify")}
          </button>
        </div>
      </div>
    </>
  );
}

export default function KycPage() {
  return (
    <Suspense fallback={<p className="p-6 text-muted">…</p>}>
      <KycPageInner />
    </Suspense>
  );
}
