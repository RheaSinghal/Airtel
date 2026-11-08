import type { Metadata, Viewport } from "next";
import { Suspense } from "react";
import { DM_Sans, Instrument_Serif, Noto_Sans_Devanagari } from "next/font/google";
import { Footer } from "@/components/Footer";
import "./globals.css";

const dm = DM_Sans({ variable: "--font-dm", subsets: ["latin"] });
const instrument = Instrument_Serif({ variable: "--font-instrument", subsets: ["latin"], weight: "400", style: ["normal", "italic"] });
const notoDeva = Noto_Sans_Devanagari({ variable: "--font-noto-deva", subsets: ["devanagari"], weight: ["400", "600", "700"] });

export const metadata: Metadata = {
  title: "Accel Business · Udyam Digital",
  description: "Get the right internet, SIMs and digital tools for your business in one sitting.",
  manifest: "/manifest.webmanifest",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#f6f1e7",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${dm.variable} ${instrument.variable} ${notoDeva.variable} h-full antialiased`}>
      <body className="min-h-full flex flex-col">
        {children}
        <Suspense fallback={null}>
          <Footer />
        </Suspense>
      </body>
    </html>
  );
}
