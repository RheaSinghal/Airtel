"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

/** Chat screens fill the viewport; the footer would push the composer away. */
const HIDE_ON = ["/advisor", "/whatsapp"];

const COLS: [string, [string, string][]][] = [
  ["Explore", [["Advisor", "/advisor"], ["Quote", "/quote"], ["WhatsApp", "/whatsapp"]]],
  ["For business", [["Track order", "/#track"], ["Impact", "/impact"]]],
  ["Partners", [["Back-office", "/backoffice"], ["Partner mode", "/#partner"]]],
  ["Help", [["Privacy & your data", "/#privacy"], ["How it works", "/#how"]]],
];

export function Footer() {
  const path = usePathname();
  if (HIDE_ON.some((p) => path?.startsWith(p))) return null;
  return (
    <footer className="mt-auto bg-[#1f1d1a] text-[#f3ede2]">
      <div className="mx-auto grid max-w-5xl gap-8 px-4 py-12 sm:grid-cols-[1.4fr_repeat(4,1fr)] sm:px-6">
        <div>
          <p className="font-display text-2xl">
            Accel <span className="font-sans text-base font-semibold">Business</span>
            <span className="ml-1 inline-block h-2 w-2 rounded-full bg-[#f29a4a]" />
          </p>
          <p className="mt-3 text-sm text-[#ada597]">Your business online in one sitting.</p>
        </div>
        {COLS.map(([title, links]) => (
          <nav key={title} aria-label={title}>
            <p className="mb-3 text-xs font-semibold uppercase tracking-[0.08em] text-[#ada597]">{title}</p>
            <ul className="space-y-2 text-sm">
              {links.map(([label, href]) => (
                <li key={label}>
                  <Link href={href} className="hover:text-[#f29a4a]">
                    {label}
                  </Link>
                </li>
              ))}
            </ul>
          </nav>
        ))}
      </div>
      <div className="mx-auto max-w-5xl border-t border-white/10 px-4 py-5 text-xs text-[#ada597] sm:px-6">
        ©2026 Accel Business (fictional operator for the YTL Hackathon case). All data is synthetic.
      </div>
    </footer>
  );
}
