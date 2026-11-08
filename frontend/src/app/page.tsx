"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { Header } from "@/components/Header";
import { LANGS, t, useLang } from "@/lib/i18n";

const PROOF: [string, string][] = [
  ["3 min", "to a priced bundle, in your language"],
  ["1", "monthly price, GST included"],
  ["30 s", "KYC with DigiLocker, no photocopies"],
  ["0", "calls to ask “where is my order?”"],
];

export default function Home() {
  const [lang, setLang] = useLang();
  const router = useRouter();
  const [orderId, setOrderId] = useState("");
  const [partner, setPartner] = useState("");

  const steps = [
    ["step1", "step1b"],
    ["step2", "step2b"],
    ["step3", "step3b"],
    ["step4", "step4b"],
  ] as const;

  const startHref = partner.trim() ? `/advisor?partner=${encodeURIComponent(partner.trim())}` : "/advisor";

  return (
    <>
      <Header lang={lang} setLang={setLang} full />
      <main className="mx-auto w-full max-w-5xl flex-1 px-4 pb-20 sm:px-6">
        {/* Hero */}
        <section className="grid gap-10 pt-12 pb-14 md:grid-cols-[1.25fr_1fr] md:items-end md:pt-20">
          <div className="rise">
            <p className="eyebrow mb-4">Udyam Digital · for shops, clinics, offices & units</p>
            <h1 className="text-[44px] sm:text-[56px] md:text-[72px]">
              {lang === "en" ? (
                <>
                  Your business online, <em className="text-brand">in one sitting.</em>
                </>
              ) : (
                t(lang, "tagline")
              )}
            </h1>
            <p className="mt-5 max-w-xl text-lg text-muted">{t(lang, "sub")}</p>
            <div className="mt-8 flex flex-col gap-3 sm:flex-row">
              <Link
                href={startHref}
                className="inline-flex h-12 items-center justify-center rounded-full bg-foreground px-7 text-base font-semibold text-background"
              >
                {t(lang, "start")} →
              </Link>
              <Link
                href="/whatsapp"
                className="inline-flex h-12 items-center justify-center rounded-full border border-foreground px-7 text-base font-semibold"
              >
                Chat on WhatsApp
              </Link>
            </div>
          </div>

          {/* Type-and-shape composition (DESIGN.md §13): the one-bill promise */}
          <div aria-hidden className="rise rise-2 relative mx-auto w-full max-w-sm">
            <div className="absolute -top-4 -right-3 h-24 w-24 rounded-full bg-saffron/80" />
            <div className="relative rounded-[20px] border border-border bg-surface p-6">
              <p className="eyebrow">One bill · a CA firm in Pune, 8 staff</p>
              <ul className="mt-4 space-y-2 text-sm">
                {["Biz Fibre 300", "Cloud Email ×5", "Cloud Backup 1 TB", "Endpoint Security ×5"].map((x) => (
                  <li key={x} className="flex justify-between border-b border-dashed border-border pb-2">
                    <span>{x}</span>
                    <span className="text-muted">included</span>
                  </li>
                ))}
              </ul>
              <p className="mt-5 font-display text-5xl tabular">₹4,712</p>
              <p className="text-sm text-muted">per month, GST included · ready in 5 days</p>
            </div>
          </div>
        </section>

        {/* Language picker */}
        <section className="rise rise-3 border-y border-border py-6">
          <p className="eyebrow mb-3">{t(lang, "language")}</p>
          <div className="flex flex-wrap gap-2">
            {Object.entries(LANGS).map(([code, name]) => (
              <button
                key={code}
                onClick={() => setLang(code)}
                className={`h-11 rounded-full border px-4 text-sm ${
                  lang === code ? "border-foreground bg-foreground text-background" : "border-border bg-surface"
                }`}
              >
                {name}
              </button>
            ))}
          </div>
        </section>

        {/* Proof numbers */}
        <section className="grid grid-cols-2 gap-6 py-12 md:grid-cols-4">
          {PROOF.map(([n, l]) => (
            <div key={l}>
              <p className="font-display text-5xl text-brand tabular">{n}</p>
              <p className="mt-1 text-sm text-muted">{l}</p>
            </div>
          ))}
        </section>

        {/* How it works: editorial numbered list (DESIGN.md §8) */}
        <section id="how" className="py-10">
          <h2 className="mb-8 text-[36px] sm:text-[44px]">{t(lang, "howItWorks")}</h2>
          <ol className="grid gap-x-10 gap-y-8 sm:grid-cols-2">
            {steps.map(([a, b], i) => (
              <li key={a} className="flex gap-5 border-t border-border pt-5">
                <span className="font-display text-[40px] leading-none text-saffron tabular">0{i + 1}</span>
                <div>
                  <p className="text-lg font-semibold">{t(lang, a)}</p>
                  <p className="mt-1 text-muted">{t(lang, b)}</p>
                </div>
              </li>
            ))}
          </ol>
        </section>

        {/* Track + partner */}
        <section className="mt-6 grid gap-4 sm:grid-cols-2">
          <form
            id="track"
            className="rounded-[20px] border border-border bg-surface p-6"
            onSubmit={(e) => {
              e.preventDefault();
              if (orderId.trim()) router.push(`/order/${orderId.trim().toUpperCase()}`);
            }}
          >
            <label className="mb-1 block font-display text-2xl" htmlFor="order">
              {t(lang, "track")}
            </label>
            <p className="mb-4 text-sm text-muted">Every step and date, without calling anyone.</p>
            <div className="flex gap-2">
              <input
                id="order"
                value={orderId}
                onChange={(e) => setOrderId(e.target.value)}
                placeholder={t(lang, "trackPlaceholder")}
                className="h-12 min-w-0 flex-1 rounded-xl border border-border bg-background px-4"
              />
              <button aria-label="Track" className="h-12 w-12 rounded-full bg-foreground text-background">
                →
              </button>
            </div>
          </form>
          <div id="partner" className="rounded-[20px] border border-border bg-surface p-6">
            <label className="mb-1 block font-display text-2xl" htmlFor="partner-code">
              {t(lang, "partnerMode")}
            </label>
            <p className="mb-4 text-sm text-muted">
              Local resellers run the same advisor on the owner&apos;s phone and keep credit for the sale.
            </p>
            <input
              id="partner-code"
              value={partner}
              onChange={(e) => setPartner(e.target.value)}
              placeholder="Partner code, e.g. PTR-INDORE-07"
              className="h-12 w-full rounded-xl border border-border bg-background px-4"
            />
          </div>
        </section>

        {/* Privacy promise */}
        <section id="privacy" className="mt-14 rounded-[20px] bg-brand-soft p-6 sm:p-8">
          <p className="eyebrow mb-2">Your data</p>
          <h2 className="text-[30px] sm:text-[36px]">We read your documents, then delete the photos.</h2>
          <p className="mt-3 max-w-2xl text-muted">
            You get a consent receipt, a passbook of every time your data was used, and one tap to withdraw. Built for the DPDP
            Act, 2023.
          </p>
        </section>
      </main>
    </>
  );
}
