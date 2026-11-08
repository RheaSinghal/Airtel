"use client";

import Link from "next/link";
import { useState } from "react";
import { LANGS } from "@/lib/i18n";

export const NAV: [string, string][] = [
  ["Advisor", "/advisor"],
  ["Quote", "/quote"],
  ["Track order", "/#track"],
  ["Partners", "/backoffice"],
  ["Impact", "/impact"],
];

export function Logo() {
  return (
    <Link href="/" className="flex items-baseline gap-1.5 whitespace-nowrap" aria-label="Accel Business home">
      <span className="font-display text-[22px] leading-none">Accel</span>
      <span className="text-sm font-semibold">Business</span>
      <span className="h-1.5 w-1.5 rounded-full bg-saffron" />
    </Link>
  );
}

export function Header({
  lang,
  setLang,
  title,
  backHref,
  full,
}: {
  lang: string;
  setLang?: (l: string) => void;
  title?: string;
  backHref?: string;
  /** Full navigation (landing page). Journey screens keep a compact header so the task stays on screen. */
  full?: boolean;
}) {
  const [open, setOpen] = useState(false);
  return (
    <header className="sticky top-0 z-20 border-b border-border bg-background/90 backdrop-blur">
      <div className={`mx-auto flex h-14 items-center justify-between gap-3 px-4 sm:px-6 ${full ? "max-w-5xl" : "max-w-3xl"}`}>
        <div className="flex min-w-0 items-center gap-3">
          {backHref ? (
            <Link href={backHref} aria-label="Back" className="-ml-2 grid h-11 w-11 place-items-center rounded-full hover:bg-surface-2">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75">
                <path d="M15 18l-6-6 6-6" />
              </svg>
            </Link>
          ) : (
            <Logo />
          )}
          {title && <h1 className="truncate text-[22px]">{title}</h1>}
        </div>
        {full && (
          <nav aria-label="Main" className="hidden items-center gap-6 text-sm font-medium md:flex">
            {NAV.map(([label, href]) => (
              <Link key={href} href={href} className="hover:text-brand">
                {label}
              </Link>
            ))}
          </nav>
        )}
        <div className="flex items-center gap-2">
          {setLang && (
            <select
              aria-label="Language"
              value={lang}
              onChange={(e) => setLang(e.target.value)}
              className="h-10 rounded-full border border-border bg-surface px-3 text-sm"
            >
              {Object.entries(LANGS).map(([code, name]) => (
                <option key={code} value={code}>
                  {name}
                </option>
              ))}
            </select>
          )}
          {full && (
            <button
              onClick={() => setOpen(!open)}
              aria-expanded={open}
              className="h-10 rounded-full border border-foreground px-4 text-sm font-medium md:hidden"
            >
              Menu
            </button>
          )}
        </div>
      </div>
      {full && open && (
        <nav aria-label="Main mobile" className="border-t border-border bg-background px-4 py-2 md:hidden">
          {NAV.map(([label, href]) => (
            <Link key={href} href={href} onClick={() => setOpen(false)} className="block py-3 text-base font-medium">
              {label}
            </Link>
          ))}
        </nav>
      )}
    </header>
  );
}
