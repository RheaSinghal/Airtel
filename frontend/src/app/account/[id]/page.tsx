"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { Suspense, useCallback, useEffect, useState } from "react";
import { Header } from "@/components/Header";
import { api, inr, type Bill, type Order, type Ticket } from "@/lib/api";
import { useLang } from "@/lib/i18n";

const fmt = (iso: string) => new Date(iso).toLocaleString("en-IN", { day: "numeric", month: "short", hour: "numeric", minute: "2-digit" });

function Account() {
  const { id } = useParams<{ id: string }>();
  const [lang, setLang] = useLang();
  const [order, setOrder] = useState<Order | null>(null);
  const [bill, setBill] = useState<Bill | null>(null);
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [cats, setCats] = useState<Record<string, string>>({});
  const [cat, setCat] = useState<string | undefined>();
  const [text, setText] = useState("");
  const [paid, setPaid] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadTickets = useCallback(() => api.tickets(id).then(setTickets).catch(() => {}), [id]);

  useEffect(() => {
    Promise.all([api.order(id), api.bill(id)])
      .then(([o, b]) => {
        setOrder(o);
        setBill(b);
      })
      .catch(() => setError("Account not found."));
    api.supportCategories().then(setCats).catch(() => {});
    loadTickets();
  }, [id, loadTickets]);

  if (error) return <p className="p-6">{error}</p>;
  if (!order || !bill) return <p className="p-6 text-muted">…</p>;
  const live = order.status === "activated";

  return (
    <>
      <Header lang={lang} setLang={setLang} title="My business account" backHref={`/order/${id}`} />
      <main className="mx-auto w-full max-w-2xl flex-1 space-y-4 px-4 py-4 pb-16">
        <section className="rounded-[20px] border border-border bg-surface p-4">
          <p className="text-sm text-muted">
            {order.profile.business_type} · {order.profile.city}
          </p>
          <p className="mt-1 text-lg font-semibold">
            {bill.lines.length} services · 1 bill · 1 support number
          </p>
          <p className="text-sm text-muted">Before: about {bill.separate_bills_before} separate bills and vendors ({bill.categories.join(", ")}).</p>
          <ul className="mt-3 grid grid-cols-1 gap-1.5 text-sm sm:grid-cols-2">
            {bill.lines.map((l) => (
              <li key={l.name} className="flex items-center gap-2">
                <span className={`h-2 w-2 rounded-full ${live ? "bg-ok" : "bg-warn"}`} aria-hidden />
                {l.name}
                {l.quantity > 1 && <span className="text-muted">× {l.quantity}</span>}
                <span className={`ml-auto text-xs ${live ? "text-ok" : "text-warn"}`}>{live ? "Active" : "Installing"}</span>
              </li>
            ))}
          </ul>
        </section>

        <section className="rounded-[20px] border border-border bg-surface p-4">
          <div className="flex items-baseline justify-between">
            <h2 className="text-[22px]">Bill · {bill.period}</h2>
            <span className="text-xs text-muted">due {new Date(bill.due_date).toLocaleDateString("en-IN", { day: "numeric", month: "short" })}</span>
          </div>
          <ul className="mt-2 divide-y divide-border text-sm">
            {bill.lines.map((l) => (
              <li key={l.name} className="flex justify-between py-1.5">
                <span>
                  {l.name}
                  {l.quantity > 1 && ` × ${l.quantity}`}
                </span>
                <span className="tabular">{inr(l.amount)}</span>
              </li>
            ))}
            <li className="flex justify-between py-1.5 text-muted">
              <span>GST (18%)</span>
              <span className="tabular">{inr(bill.gst)}</span>
            </li>
          </ul>
          <div className="mt-2 flex items-center justify-between gap-3">
            <p className="text-2xl font-bold tabular">{inr(bill.total)}</p>
            {paid ? (
              <span className="rounded-xl bg-ok-soft px-4 py-2.5 text-sm font-semibold text-ok">✓ Paid via UPI</span>
            ) : (
              <a href={bill.upi_link} onClick={() => setPaid(true)} className="rounded-full bg-foreground px-5 py-2.5 font-semibold text-background">
                Pay with UPI
              </a>
            )}
          </div>
          <p className="mt-1 text-xs text-muted">GST invoice for input tax credit is emailed with every bill. UPI AutoPay available.</p>
        </section>

        <section className="rounded-[20px] border border-border bg-surface p-4">
          <h2 className="text-[22px]">Need help?</h2>
          <p className="text-sm text-muted">One place for every service. Describe it in your own words; we route it to the right team.</p>
          <div className="mt-3 flex flex-wrap gap-2">
            {Object.entries(cats).map(([k, label]) => (
              <button
                key={k}
                onClick={() => setCat(cat === k ? undefined : k)}
                className={`rounded-full border px-3 py-1.5 text-xs ${cat === k ? "border-foreground bg-foreground text-background" : "border-border"}`}
              >
                {label}
              </button>
            ))}
          </div>
          <form
            className="mt-3 flex gap-2"
            onSubmit={async (e) => {
              e.preventDefault();
              if (text.trim().length < 3) return;
              await api.newTicket(id, text, cat);
              setText("");
              setCat(undefined);
              loadTickets();
            }}
          >
            <input
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="e.g. internet band hai since morning"
              className="min-w-0 flex-1 rounded-lg border border-border bg-background px-3 py-2"
            />
            <button className="rounded-lg bg-foreground px-4 text-background">Send</button>
          </form>
          <ul className="mt-3 space-y-2">
            {tickets.map((tk) => (
              <li key={tk.id} className="rounded-xl bg-surface-2 p-3 text-sm">
                <div className="flex flex-wrap items-baseline justify-between gap-2">
                  <p className="font-medium">
                    {tk.detail.label}
                    <span
                      className={`ml-2 rounded-full px-2 py-0.5 text-xs ${
                        tk.detail.priority === "high" ? "bg-bad-soft text-bad" : tk.detail.priority === "medium" ? "bg-warn-soft text-warn" : "bg-surface text-muted"
                      }`}
                    >
                      {tk.detail.priority}
                    </span>
                  </p>
                  <span className="text-xs text-muted">{tk.id}</span>
                </div>
                <p className="text-muted">&ldquo;{tk.text}&rdquo;</p>
                <p className="mt-1 text-xs">
                  {tk.detail.team} · resolve by {fmt(tk.detail.resolve_by)}
                </p>
                {tk.detail.diagnostics && (
                  <p className="mt-1 rounded-lg bg-ok-soft p-2 text-xs text-ok">
                    🔧 {tk.detail.diagnostics.line_test}. {tk.detail.diagnostics.action}
                  </p>
                )}
              </li>
            ))}
          </ul>
        </section>
        <p className="text-center text-sm">
          <Link href={`/order/${id}`} className="text-muted underline">
            Order tracker
          </Link>
        </p>
      </main>
    </>
  );
}

export default function AccountPage() {
  return (
    <Suspense fallback={<p className="p-6 text-muted">…</p>}>
      <Account />
    </Suspense>
  );
}
