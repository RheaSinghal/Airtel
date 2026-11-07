"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useCallback, useEffect, useRef, useState, useSyncExternalStore } from "react";
import { Header } from "@/components/Header";
import { OfferCard } from "@/components/OfferCard";
import { api, type Chip, type Message } from "@/lib/api";
import { t, useLang } from "@/lib/i18n";
import { listen, speak, speechSupported } from "@/lib/speech";

const SESSION_KEY = "udyam.session";
const noopSubscribe = () => () => {};

function Advisor() {
  const [lang, setLang] = useLang();
  const router = useRouter();
  const params = useSearchParams();
  const partner = params.get("partner");
  const [sid, setSid] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [listening, setListening] = useState(false);
  const [voiceOut, setVoiceOut] = useState(false);
  const [needsEdit, setNeedsEdit] = useState<{ at: number; set: Set<string> } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const canSpeak = useSyncExternalStore(noopSubscribe, speechSupported, () => false);
  const bottom = useRef<HTMLDivElement>(null);
  const started = useRef(false);

  // Start or resume a session
  useEffect(() => {
    if (started.current) return;
    started.current = true;
    const resume = params.get("session") ?? (partner ? null : sessionStorage.getItem(SESSION_KEY));
    (async () => {
      try {
        if (resume && !params.get("new")) {
          const s = await api.getSession(resume).catch(() => null);
          if (s && s.stage !== "ordered") {
            setSid(s.id);
            setMessages(s.messages);
            return;
          }
        }
        const stored = localStorage.getItem("udyam.lang") ?? "en";
        const s = await api.startSession(stored, partner);
        sessionStorage.setItem(SESSION_KEY, s.id);
        setSid(s.id);
        setMessages(s.messages);
      } catch {
        setError("Could not reach the server. Is the backend running?");
      }
    })();
  }, [params, partner]);

  useEffect(() => {
    bottom.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, busy]);

  // Multi-select state for the latest needs question: server pre-selection until the owner edits it
  const lastIdx = messages.length - 1;
  const last = messages[lastIdx];
  const needs: Set<string> =
    needsEdit && needsEdit.at === lastIdx
      ? needsEdit.set
      : new Set((last?.chips ?? []).filter((c) => c.selected && c.payload.toggle_need).map((c) => String(c.payload.toggle_need)));

  const send = useCallback(
    async (body: { text?: string; payload?: Record<string, unknown> }, echo?: string) => {
      if (!sid || busy) return;
      setBusy(true);
      setError(null);
      if (echo) setMessages((m) => [...m, { role: "user", text: echo }]);
      try {
        const r = await api.send(sid, { ...body, lang });
        const visible = r.messages.filter((m) => m.kind !== "chips_update");
        setMessages((m) => [...m, ...visible]);
        if (voiceOut) speak(visible.map((m) => m.text).join(" "), lang);
      } catch {
        setError("Something went wrong. Please try again.");
      } finally {
        setBusy(false);
      }
    },
    [sid, busy, lang, voiceOut],
  );

  const onChip = (chip: Chip, msg: Message) => {
    const p = chip.payload;
    if (p.action === "quote") {
      router.push(`/quote?session=${sid}`);
      return;
    }
    if (msg.multi && p.toggle_need) {
      const n = String(p.toggle_need);
      const next = new Set(needs);
      if (next.has(n)) next.delete(n);
      else next.add(n);
      setNeedsEdit({ at: lastIdx, set: next });
      return;
    }
    if (msg.multi && p.needs_done) {
      const labels = msg.chips?.filter((c) => needs.has(String(c.payload.toggle_need))).map((c) => c.label);
      send({ payload: { set_needs: [...needs] } }, labels?.join(", ") || chip.label);
      return;
    }
    send({ payload: p }, chip.label);
  };

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    const text = input.trim();
    if (!text) return;
    setInput("");
    send({ text }, text);
  };

  const mic = () => {
    if (listening) return;
    setListening(true);
    listen(
      lang,
      (text) => {
        setInput("");
        send({ text }, text);
      },
      () => setListening(false),
    );
  };

  const changeLang = (l: string) => {
    setLang(l);
  };

  return (
    <>
      <Header lang={lang} setLang={changeLang} title={t(lang, "advisor")} backHref="/" />
      {partner && (
        <div className="bg-warn-soft px-4 py-1.5 text-center text-xs text-warn">Partner-assisted session · {partner}</div>
      )}
      <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col px-4">
        <div className="flex-1 space-y-3 py-4" aria-live="polite">
          {messages.map((m, i) => {
            const isLast = i === lastIdx;
            if (m.role === "user") {
              return (
                <div key={i} className="flex justify-end">
                  <p className="max-w-[85%] rounded-2xl rounded-br-sm bg-chat-user px-4 py-2.5 text-background">{m.text}</p>
                </div>
              );
            }
            return (
              <div key={i} className="space-y-2">
                {m.text && (
                  <p className="max-w-[90%] whitespace-pre-line rounded-2xl rounded-bl-sm border border-border bg-surface px-4 py-2.5">
                    {m.text}
                  </p>
                )}
                {m.recommendation && (
                  <OfferCard
                    offer={m.recommendation}
                    lang={lang}
                    explanation={m.explanation}
                    onCheckout={(tier) => router.push(`/quote?session=${sid}&tier=${tier}`)}
                  />
                )}
                {m.chips && isLast && (
                  <div className="flex flex-wrap gap-2">
                    {m.chips.map((c) => {
                      const selected = m.multi && c.payload.toggle_need ? needs.has(String(c.payload.toggle_need)) : false;
                      return (
                        <button
                          key={c.label}
                          disabled={busy}
                          onClick={() => onChip(c, m)}
                          aria-pressed={m.multi ? selected : undefined}
                          className={`rounded-full border px-3.5 py-2 text-sm transition ${
                            c.primary
                              ? "border-brand bg-brand font-semibold text-brand-ink"
                              : selected
                                ? "border-foreground bg-foreground text-background"
                                : "border-border bg-surface hover:border-foreground"
                          }`}
                        >
                          {m.multi && c.payload.toggle_need ? (selected ? "✓ " : "+ ") : ""}
                          {c.label}
                        </button>
                      );
                    })}
                  </div>
                )}
              </div>
            );
          })}
          {busy && (
            <div className="flex gap-1 px-2 py-3" aria-label="Advisor is typing">
              {[0, 1, 2].map((d) => (
                <span key={d} className="h-2 w-2 animate-bounce rounded-full bg-muted" style={{ animationDelay: `${d * 120}ms` }} />
              ))}
            </div>
          )}
          {error && <p className="rounded-lg bg-bad-soft p-3 text-sm text-bad">{error}</p>}
          <div ref={bottom} />
        </div>

        <form onSubmit={submit} className="sticky bottom-0 -mx-4 border-t border-border bg-background/95 px-4 py-3 backdrop-blur">
          <div className="flex items-center gap-2">
            {canSpeak && (
              <button
                type="button"
                onClick={mic}
                aria-label="Speak"
                className={`grid h-11 w-11 shrink-0 place-items-center rounded-full border ${
                  listening ? "animate-pulse border-brand bg-brand text-brand-ink" : "border-border bg-surface"
                }`}
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <rect x="9" y="3" width="6" height="11" rx="3" />
                  <path d="M5 11a7 7 0 0014 0M12 18v3" />
                </svg>
              </button>
            )}
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={listening ? t(lang, "listening") : t(lang, "typeMessage")}
              className="h-11 min-w-0 flex-1 rounded-full border border-border bg-surface px-4"
              aria-label={t(lang, "typeMessage")}
            />
            <button disabled={busy || !input.trim()} className="h-11 rounded-full bg-brand px-5 font-semibold text-brand-ink disabled:opacity-40">
              {t(lang, "send")}
            </button>
          </div>
          <label className="mt-2 flex items-center gap-2 text-xs text-muted">
            <input type="checkbox" checked={voiceOut} onChange={(e) => setVoiceOut(e.target.checked)} />
            {t(lang, "speak")}
          </label>
        </form>
      </main>
    </>
  );
}

export default function AdvisorPage() {
  return (
    <Suspense>
      <Advisor />
    </Suspense>
  );
}
