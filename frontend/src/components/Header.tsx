"use client";

import Link from "next/link";
import { LANGS } from "@/lib/i18n";

export function Logo() {
  return (
    <Link href="/" className="flex items-center gap-2 font-bold tracking-tight">
      <span className="grid h-8 w-8 place-items-center rounded-lg bg-brand text-brand-ink text-sm">A</span>
      <span>
        Accel <span className="text-brand">Business</span>
      </span>
    </Link>
  );
}

export function Header({
  lang,
  setLang,
  title,
  backHref,
}: {
  lang: string;
  setLang?: (l: string) => void;
  title?: string;
  backHref?: string;
}) {
  return (
    <header className="sticky top-0 z-20 border-b border-border bg-surface/95 backdrop-blur">
      <div className="mx-auto flex h-14 max-w-3xl items-center justify-between gap-3 px-4">
        <div className="flex min-w-0 items-center gap-3">
          {backHref ? (
            <Link href={backHref} aria-label="Back" className="-ml-2 rounded-full p-2 hover:bg-surface-2">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M15 18l-6-6 6-6" />
              </svg>
            </Link>
          ) : (
            <Logo />
          )}
          {title && <h1 className="truncate font-semibold">{title}</h1>}
        </div>
        {setLang && (
          <select
            aria-label="Language"
            value={lang}
            onChange={(e) => setLang(e.target.value)}
            className="rounded-lg border border-border bg-surface px-2 py-1.5 text-sm"
          >
            {Object.entries(LANGS).map(([code, name]) => (
              <option key={code} value={code}>
                {name}
              </option>
            ))}
          </select>
        )}
      </div>
    </header>
  );
}
