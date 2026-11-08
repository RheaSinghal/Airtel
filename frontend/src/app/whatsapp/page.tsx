"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { api, type WaReply } from "@/lib/api";

type Bubble = { from: "me" | "biz"; text: string; buttons?: WaReply["buttons"]; list?: WaReply["list"]; at: string };

const now = () => new Date().toLocaleTimeString("en-IN", { hour: "numeric", minute: "2-digit" });

/** Format WhatsApp markup: *bold*, _italic_, and links. */
function WaText({ text }: { text: string }) {
  const parts = text.split(/(\*[^*\n]+\*|_[^_\n]+_|https?:\/\/\S+)/g);
  return (
    <>
      {parts.map((p, i) => {
        if (/^\*[^*]+\*$/.test(p)) return <b key={i}>{p.slice(1, -1)}</b>;
        if (/^_[^_]+_$/.test(p)) return <i key={i}>{p.slice(1, -1)}</i>;
        if (/^https?:\/\//.test(p)) {
          const path = p.replace(/^https?:\/\/[^/]+/, "");
          return (
            <Link key={i} href={path} target="_blank" className="break-all text-[#027eb5] underline">
              {p}
            </Link>
          );
        }
        return <span key={i}>{p}</span>;
      })}
    </>
  );
}

export default function WhatsAppSim() {
  const [phone, setPhone] = useState("919800000001");
  const [chat, setChat] = useState<Bubble[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [openList, setOpenList] = useState<number | null>(null);
  const bottom = useRef<HTMLDivElement>(null);

  useEffect(() => bottom.current?.scrollIntoView({ behavior: "smooth" }), [chat, busy]);

  const send = async (text: string, shown?: string) => {
    if (!text.trim() || busy) return;
    setOpenList(null);
    setChat((c) => [...c, { from: "me", text: shown ?? text, at: now() }]);
    setBusy(true);
    try {
      const r = await api.waSimulate(phone, text);
      setChat((c) => [...c, ...r.replies.map((m) => ({ from: "biz" as const, ...m, at: now() }))]);
    } catch {
      setChat((c) => [...c, { from: "biz", text: "⚠ Backend not reachable", at: now() }]);
    } finally {
      setBusy(false);
    }
  };

  return (
    <main className="flex min-h-screen flex-col items-center gap-4 bg-[#0b141a] px-4 py-6 text-white lg:flex-row lg:items-start lg:justify-center lg:gap-10">
      <aside className="max-w-sm space-y-3 text-sm text-white/80 lg:pt-10">
        <Link href="/" className="text-white/60 underline">
          ← Accel Business
        </Link>
        <h1 className="text-2xl font-bold text-white">WhatsApp channel</h1>
        <p>
          The same advisor, rules engine and pricing, on the app small businesses already use every day. This simulator calls the exact
          handler behind the WhatsApp Cloud API webhook (<code className="text-white">/api/whatsapp/webhook</code>).
        </p>
        <ul className="list-inside list-disc space-y-1">
          <li>Say &quot;hi&quot; or &quot;namaste&quot; to start (Hindi is detected automatically)</li>
          <li>Type freely, or tap buttons / reply with numbers</li>
          <li>Pick several needs at once: &quot;1,3,4&quot;</li>
          <li>Checkout and KYC open as a link</li>
        </ul>
        <label className="block pt-2">
          Customer phone (each number = separate chat)
          <select value={phone} onChange={(e) => { setPhone(e.target.value); setChat([]); }} className="mt-1 block w-full rounded-lg bg-white/10 px-2 py-1.5">
            <option value="919800000001">+91 98000 00001</option>
            <option value="919800000002">+91 98000 00002</option>
            <option value="919800000003">+91 98000 00003</option>
          </select>
        </label>
      </aside>

      <div className="flex h-[760px] max-h-[88vh] w-full max-w-[390px] flex-col overflow-hidden rounded-[2.2rem] border-[10px] border-[#1f2c33] bg-[#efeae2] text-[#111b21] shadow-2xl">
        <header className="flex items-center gap-3 bg-[#008069] px-3 py-2.5 text-white">
          <span className="grid h-9 w-9 place-items-center rounded-full bg-white text-sm font-bold text-[#d6001c]">A</span>
          <div className="min-w-0 flex-1">
            <p className="flex items-center gap-1 font-semibold leading-tight">
              Accel Business
              <svg width="14" height="14" viewBox="0 0 24 24" aria-label="Verified business">
                <circle cx="12" cy="12" r="10" fill="#25d366" />
                <path d="M7 12.5l3 3 7-7" stroke="#fff" strokeWidth="2.2" fill="none" />
              </svg>
            </p>
            <p className="text-xs text-white/80">{busy ? "typing…" : "Official business account"}</p>
          </div>
        </header>

        <div className="flex-1 space-y-2 overflow-y-auto px-3 py-3">
          {chat.length === 0 && (
            <p className="mx-auto mt-6 w-fit rounded-lg bg-[#fff5c4] px-3 py-1.5 text-center text-xs">Send &quot;hi&quot; to start</p>
          )}
          {chat.map((b, i) => (
            <div key={i} className={`flex flex-col ${b.from === "me" ? "items-end" : "items-start"}`}>
              <div
                className={`max-w-[85%] whitespace-pre-line rounded-lg px-2.5 py-1.5 text-[14px] leading-snug shadow-sm ${
                  b.from === "me" ? "rounded-tr-none bg-[#d9fdd3]" : "rounded-tl-none bg-white"
                }`}
              >
                <WaText text={b.text} />
                <span className="float-right ml-2 mt-1 text-[10px] text-[#667781]">
                  {b.at}
                  {b.from === "me" && " ✓✓"}
                </span>
              </div>
              {b.buttons && i === chat.length - 1 && (
                <div className="mt-1 flex w-[85%] flex-col gap-1">
                  {b.buttons.map((btn) => (
                    <button key={btn.id} onClick={() => send(btn.id, btn.title)} className="rounded-lg bg-white py-2 text-sm font-medium text-[#027eb5] shadow-sm">
                      {btn.title}
                    </button>
                  ))}
                </div>
              )}
              {b.list && i === chat.length - 1 && (
                <div className="mt-1 w-[85%]">
                  <button onClick={() => setOpenList(openList === i ? null : i)} className="w-full rounded-lg bg-white py-2 text-sm font-medium text-[#027eb5] shadow-sm">
                    ☰ Choose an option
                  </button>
                  {openList === i && (
                    <ul className="mt-1 overflow-hidden rounded-lg bg-white shadow">
                      {b.list.map((row) => (
                        <li key={row.id}>
                          <button onClick={() => send(row.id, row.title)} className="w-full border-b border-black/5 px-3 py-2 text-left text-sm">
                            {row.title}
                          </button>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              )}
            </div>
          ))}
          <div ref={bottom} />
        </div>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            const t = input;
            setInput("");
            send(t);
          }}
          className="flex items-center gap-2 bg-[#f0f2f5] px-2 py-2"
        >
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Message"
            className="min-w-0 flex-1 rounded-full bg-white px-4 py-2.5 text-[15px] outline-none"
          />
          <button aria-label="Send" className="grid h-10 w-10 place-items-center rounded-full bg-[#008069] text-white">
            ➤
          </button>
        </form>
      </div>
    </main>
  );
}
