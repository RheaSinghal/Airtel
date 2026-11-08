"use client";

import { useEffect, useState } from "react";
import { api, type Passbook as PB } from "@/lib/api";

const when = (iso: string) =>
  new Date(iso).toLocaleString("en-IN", { day: "numeric", month: "short", hour: "numeric", minute: "2-digit" });

/** N2 Data passbook: the owner's consent receipt and every access to their KYC data (DPDP Act 2023). */
export function Passbook({ orderId, refreshKey }: { orderId: string; refreshKey?: string }) {
  const [pb, setPb] = useState<PB | null>(null);
  useEffect(() => {
    api.passbook(orderId).then(setPb).catch(() => {});
  }, [orderId, refreshKey]);
  if (!pb || pb.status === "none") return null;
  const r = pb.receipt;
  return (
    <section className="rounded-[20px] border border-border bg-surface p-5">
      <div className="flex items-baseline justify-between gap-2">
        <h2 className="text-[22px]">Your data passbook</h2>
        <span
          className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${
            pb.status === "active" ? "bg-ok-soft text-ok" : "bg-surface-2 text-muted"
          }`}
        >
          {pb.status === "active" ? "Consent active" : "Consent withdrawn"}
        </span>
      </div>
      {r && (
        <dl className="mt-3 grid grid-cols-[auto_1fr] gap-x-4 gap-y-1 text-sm">
          <dt className="text-muted">Receipt</dt>
          <dd className="font-medium tabular">{r.receipt_id}</dd>
          <dt className="text-muted">Purpose</dt>
          <dd>Verify your business identity and address, nothing else</dd>
          <dt className="text-muted">Kept until</dt>
          <dd className="tabular">{r.retained_until}</dd>
          <dt className="text-muted">Notice hash</dt>
          <dd className="truncate font-mono text-xs" title={r.notice_sha256}>
            {r.notice_sha256.slice(0, 16)}…
          </dd>
        </dl>
      )}
      <p className="mt-3 text-sm">
        <span className="font-semibold">0 photos stored.</span>{" "}
        {pb.fields_stored.length ? `Kept: ${pb.fields_stored.length} verified details (masked).` : "No details kept."}
      </p>
      <p className="eyebrow mt-4 mb-2">Who used your data</p>
      <ol className="space-y-2 border-l-2 border-border pl-4 text-sm">
        {pb.access_log.map((e, i) => (
          <li key={i}>
            <p>
              <span className="font-medium">{e.who}</span> · {e.what}
            </p>
            <p className="text-xs text-muted tabular">{when(e.at)}</p>
          </li>
        ))}
      </ol>
    </section>
  );
}
