"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { Header } from "@/components/Header";
import { LANGS, t, useLang } from "@/lib/i18n";

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
      <Header lang={lang} setLang={setLang} />
      <main className="mx-auto w-full max-w-3xl flex-1 px-4 pb-16">
        <section className="pt-10 pb-8">
          <p className="mb-3 inline-block rounded-full bg-brand-soft px-3 py-1 text-xs font-semibold text-brand">Udyam Digital</p>
          <h1 className="text-3xl font-bold leading-tight sm:text-4xl">{t(lang, "tagline")}</h1>
          <p className="mt-4 text-muted">{t(lang, "sub")}</p>

          <div className="mt-6">
            <p className="mb-2 text-sm font-medium">{t(lang, "language")}</p>
            <div className="flex flex-wrap gap-2">
              {Object.entries(LANGS).map(([code, name]) => (
                <button
                  key={code}
                  onClick={() => setLang(code)}
                  className={`rounded-full border px-3 py-1.5 text-sm ${
                    lang === code ? "border-brand bg-brand text-brand-ink" : "border-border bg-surface"
                  }`}
                >
                  {name}
                </button>
              ))}
            </div>
          </div>

          <Link
            href={startHref}
            className="mt-8 flex w-full items-center justify-center rounded-xl bg-brand px-6 py-4 text-lg font-semibold text-brand-ink shadow-sm active:scale-[0.99] sm:w-auto sm:inline-flex"
          >
            {t(lang, "start")} →
          </Link>
          <Link
            href="/whatsapp"
            className="mt-3 flex w-full items-center justify-center gap-2 rounded-xl border border-[#25d366] px-6 py-3 font-semibold text-[#128c4b] sm:ml-3 sm:w-auto sm:inline-flex dark:text-[#5dd38a]"
          >
            💬 Or chat on WhatsApp
          </Link>
        </section>

        <section className="rounded-2xl border border-border bg-surface p-5">
          <h2 className="mb-4 font-semibold">{t(lang, "howItWorks")}</h2>
          <ol className="grid gap-4 sm:grid-cols-2">
            {steps.map(([a, b], i) => (
              <li key={a} className="flex gap-3">
                <span className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-surface-2 font-semibold">{i + 1}</span>
                <div>
                  <p className="font-medium">{t(lang, a)}</p>
                  <p className="text-sm text-muted">{t(lang, b)}</p>
                </div>
              </li>
            ))}
          </ol>
        </section>

        <section className="mt-6 grid gap-4 sm:grid-cols-2">
          <form
            className="rounded-2xl border border-border bg-surface p-5"
            onSubmit={(e) => {
              e.preventDefault();
              if (orderId.trim()) router.push(`/order/${orderId.trim().toUpperCase()}`);
            }}
          >
            <label className="mb-2 block font-semibold" htmlFor="order">
              {t(lang, "track")}
            </label>
            <div className="flex gap-2">
              <input
                id="order"
                value={orderId}
                onChange={(e) => setOrderId(e.target.value)}
                placeholder={t(lang, "trackPlaceholder")}
                className="min-w-0 flex-1 rounded-lg border border-border bg-background px-3 py-2"
              />
              <button className="rounded-lg bg-foreground px-4 text-background">→</button>
            </div>
          </form>
          <div className="rounded-2xl border border-border bg-surface p-5">
            <label className="mb-2 block font-semibold" htmlFor="partner">
              {t(lang, "partnerMode")}
            </label>
            <input
              id="partner"
              value={partner}
              onChange={(e) => setPartner(e.target.value)}
              placeholder="Partner code, e.g. PTR-INDORE-07"
              className="w-full rounded-lg border border-border bg-background px-3 py-2"
            />
            <p className="mt-2 text-xs text-muted">
              Local resellers run the same advisor on the owner&apos;s phone and get credit for the sale.
            </p>
          </div>
        </section>

        <p className="mt-8 text-center text-sm text-muted">
          <Link href="/backoffice" className="underline">
            Sales & partner back-office
          </Link>
        </p>
      </main>
    </>
  );
}
