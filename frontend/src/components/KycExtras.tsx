"use client";

import { useState } from "react";
import { api, errMsg, inr, type Agreement } from "@/lib/api";

/** One-tap KYC: pull issuer-signed documents from DigiLocker instead of photographing them. */
export function DigiLockerCard({ orderId, gstin, onFetched }: { orderId: string; gstin?: string; onFetched: () => void }) {
  const [step, setStep] = useState<"idle" | "mobile" | "otp" | "gstin" | "done">("idle");
  const [mobile, setMobile] = useState("");
  const [otp, setOtp] = useState("");
  const [g, setG] = useState(gstin ?? "");
  const [hint, setHint] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [summary, setSummary] = useState<string | null>(null);

  const run = async (fn: () => Promise<void>) => {
    setBusy(true);
    setError(null);
    try {
      await fn();
    } catch (e) {
      setError(errMsg(e));
    } finally {
      setBusy(false);
    }
  };

  if (step === "done") {
    return <p className="rounded-2xl bg-ok-soft p-4 text-sm text-ok">✓ {summary}</p>;
  }

  return (
    <section className="rounded-2xl border-2 border-brand bg-brand-soft/40 p-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="font-semibold">⚡ Fastest: fetch from DigiLocker</p>
          <p className="text-sm text-muted">Issuer-verified GST, Udyam and e-KYC in about 30 seconds. No photos needed.</p>
        </div>
        {step === "idle" && (
          <button onClick={() => setStep("mobile")} className="shrink-0 rounded-lg bg-brand px-3 py-2 text-sm font-semibold text-brand-ink">
            Use DigiLocker
          </button>
        )}
      </div>

      {step === "mobile" && (
        <form
          className="mt-3 flex gap-2"
          onSubmit={(e) => {
            e.preventDefault();
            run(async () => {
              const r = await api.dlStart(orderId, mobile);
              setHint(`OTP sent to ${r.sent_to} (demo OTP: ${r.demo_otp})`);
              setStep("otp");
            });
          }}
        >
          <input
            value={mobile}
            onChange={(e) => setMobile(e.target.value)}
            inputMode="tel"
            placeholder="Mobile linked to DigiLocker"
            className="min-w-0 flex-1 rounded-lg border border-border bg-surface px-3 py-2"
          />
          <button disabled={busy} className="rounded-lg bg-foreground px-4 text-background">
            Send OTP
          </button>
        </form>
      )}

      {step === "otp" && (
        <form
          className="mt-3 flex gap-2"
          onSubmit={(e) => {
            e.preventDefault();
            run(async () => {
              await api.dlAuthorise(orderId, otp);
              setStep("gstin");
            });
          }}
        >
          <input
            value={otp}
            onChange={(e) => setOtp(e.target.value)}
            inputMode="numeric"
            maxLength={6}
            placeholder="6-digit OTP"
            className="min-w-0 flex-1 rounded-lg border border-border bg-surface px-3 py-2 tracking-widest"
          />
          <button disabled={busy} className="rounded-lg bg-foreground px-4 text-background">
            Allow access
          </button>
        </form>
      )}

      {step === "gstin" && (
        <form
          className="mt-3 space-y-2"
          onSubmit={(e) => {
            e.preventDefault();
            run(async () => {
              const r = await api.dlFetch(orderId, g);
              const names: Record<string, string> = {
                gst_certificate: "GST certificate",
                udyam_certificate: "Udyam certificate",
                signatory_id: "Signatory e-KYC",
                address_proof: "Address (from GST)",
              };
              setSummary(
                `Fetched ${r.fetched.map((f) => `${names[f.slot]} (${f.issuer})`).join(", ")}.` +
                  (r.still_needed.length ? ` Still needed: ${r.still_needed.map((s) => names[s]).join(", ")}.` : " Tap Verify."),
              );
              setStep("done");
              onFetched();
            });
          }}
        >
          <p className="text-sm text-muted">Pick the documents to share: GST certificate, Udyam certificate and Aadhaar e-KYC of the proprietor.</p>
          <div className="flex gap-2">
            <input
              value={g}
              onChange={(e) => setG(e.target.value.toUpperCase())}
              placeholder="GSTIN"
              className="min-w-0 flex-1 rounded-lg border border-border bg-surface px-3 py-2 font-mono"
            />
            <button disabled={busy || g.length < 15} className="rounded-lg bg-brand px-4 font-semibold text-brand-ink disabled:opacity-40">
              Fetch
            </button>
          </div>
        </form>
      )}
      {hint && step === "otp" && <p className="mt-2 text-xs text-muted">{hint}</p>}
      {error && <p className="mt-2 text-sm text-bad">{error}</p>}
    </section>
  );
}

/** Aadhaar OTP e-Sign of the customer agreement, so there is no paper form. */
export function ESignCard({ orderId, signed, onSigned }: { orderId: string; signed?: boolean; onSigned: () => void }) {
  const [doc, setDoc] = useState<{ agreement: Agreement; document_hash: string; demo_otp: string } | null>(null);
  const [otp, setOtp] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(signed);

  if (done) {
    return <p className="rounded-2xl bg-ok-soft p-4 text-sm text-ok">✓ Agreement e-signed. A copy is on its way to you on WhatsApp.</p>;
  }

  return (
    <section className="rounded-2xl border border-border bg-surface p-4">
      <p className="font-semibold">Sign your agreement</p>
      <p className="text-sm text-muted">Aadhaar OTP e-Sign: legally valid, no printing or couriers.</p>
      {!doc ? (
        <button
          onClick={async () => {
            try {
              setDoc(await api.esignRequest(orderId));
            } catch (e) {
              setError(errMsg(e));
            }
          }}
          className="mt-3 w-full rounded-xl bg-foreground py-2.5 text-background"
        >
          Review agreement
        </button>
      ) : (
        <>
          <div className="mt-3 rounded-lg bg-surface-2 p-3 text-sm">
            <ul className="space-y-0.5">
              {doc.agreement.lines.map((l) => (
                <li key={l.product} className="flex justify-between gap-2">
                  <span>
                    {l.product}
                    {l.qty > 1 && ` × ${l.qty}`}
                  </span>
                  <span className="tabular">{inr(l.monthly)}</span>
                </li>
              ))}
            </ul>
            <p className="mt-2 border-t border-border pt-2 font-semibold">
              {inr(doc.agreement.monthly_total_incl_gst)}/month incl. GST · {doc.agreement.lock_in_months}-month contract
            </p>
            <p className="mt-1 break-all font-mono text-[10px] text-muted">SHA-256 {doc.document_hash}</p>
          </div>
          <form
            className="mt-3 flex gap-2"
            onSubmit={async (e) => {
              e.preventDefault();
              try {
                await api.esignVerify(orderId, otp);
                setDone(true);
                onSigned();
              } catch (err) {
                setError(errMsg(err));
              }
            }}
          >
            <input
              value={otp}
              onChange={(e) => setOtp(e.target.value)}
              maxLength={6}
              inputMode="numeric"
              placeholder={`Aadhaar OTP (demo ${doc.demo_otp})`}
              className="min-w-0 flex-1 rounded-lg border border-border bg-background px-3 py-2 tracking-widest"
            />
            <button className="rounded-lg bg-brand px-4 font-semibold text-brand-ink">Sign</button>
          </form>
        </>
      )}
      {error && <p className="mt-2 text-sm text-bad">{error}</p>}
    </section>
  );
}
