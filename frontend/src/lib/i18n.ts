"use client";

import { useSyncExternalStore } from "react";

export const LANGS: Record<string, string> = {
  en: "English",
  hi: "हिन्दी",
  mr: "मराठी",
  ta: "தமிழ்",
  te: "తెలుగు",
  kn: "ಕನ್ನಡ",
  bn: "বাংলা",
  gu: "ગુજરાતી",
  ml: "മലയാളം",
  pa: "ਪੰਜਾਬੀ",
};

// BCP-47 tags for browser speech recognition / synthesis
export const SPEECH_TAGS: Record<string, string> = {
  en: "en-IN", hi: "hi-IN", mr: "mr-IN", ta: "ta-IN", te: "te-IN", kn: "kn-IN", bn: "bn-IN", gu: "gu-IN", ml: "ml-IN", pa: "pa-IN",
};

const UI = {
  en: {
    tagline: "Internet, SIMs and digital tools for your business, in one sitting.",
    sub: "Answer a few questions and get one clear monthly price. Pay, upload documents and track installation on your phone, with no visits and no paperwork.",
    start: "Start with the advisor",
    language: "Language",
    track: "Track an order",
    trackPlaceholder: "Order ID, e.g. ORD-1A2B3C4D",
    partnerMode: "Partner-assisted mode",
    howItWorks: "How it works",
    step1: "Tell us about your business",
    step1b: "2 minutes, chat or voice",
    step2: "See one monthly price",
    step2b: "Toggle add-ons, no hidden fees",
    step3: "Upload documents",
    step3b: "Checked instantly",
    step4: "Track installation",
    step4b: "Updates on WhatsApp",
    typeMessage: "Type your answer…",
    send: "Send",
    listening: "Listening…",
    speak: "Read replies aloud",
    advisor: "Business advisor",
    perMonth: "/month",
    inclGst: "incl. GST",
    readyIn: "Ready in about {d} days",
    oneTime: "One-time setup",
    lockIn: "Contract",
    months: "months",
    whyThis: "Why this?",
    seeQuote: "See price & checkout",
    yourBundle: "Your bundle",
    addons: "Add-ons",
    contract: "Commit longer, pay less",
    total: "Monthly total",
    gst: "GST (18%)",
    subtotal: "Subtotal",
    firstBill: "First bill",
    vsToday: "vs today",
    placeOrder: "Place order",
    contactName: "Your name",
    contactPhone: "Mobile number",
    placing: "Placing order…",
    consentTitle: "Before we check your documents",
    agree: "I agree, continue",
    decline: "Not now",
    documents: "Your documents",
    upload: "Take photo / upload",
    useSample: "Use a specimen",
    verify: "Verify documents",
    verifying: "Checking…",
    trackOrder: "Track my order",
    orderPlaced: "Order placed",
    eta: "Expected live by",
    chooseSlot: "Choose an installation slot",
    updates: "Updates",
    deleteData: "Withdraw consent & delete my documents",
    back: "Back",
    help: "Need help? Talk to an expert",
  },
  hi: {
    tagline: "आपके बिज़नेस के लिए इंटरनेट, सिम और डिजिटल टूल, एक ही बार में।",
    sub: "कुछ सवालों के जवाब दें और एक साफ़ मासिक कीमत पाएँ। फ़ोन पर ही पेमेंट करें, डॉक्यूमेंट अपलोड करें और इंस्टॉलेशन ट्रैक करें, बिना विज़िट और बिना कागज़ के।",
    start: "सलाहकार से शुरू करें",
    language: "भाषा",
    track: "ऑर्डर ट्रैक करें",
    trackPlaceholder: "ऑर्डर ID, जैसे ORD-1A2B3C4D",
    partnerMode: "पार्टनर-सहायता मोड",
    howItWorks: "कैसे काम करता है",
    step1: "अपने बिज़नेस के बारे में बताएँ",
    step1b: "2 मिनट, चैट या आवाज़",
    step2: "एक मासिक कीमत देखें",
    step2b: "ऐड-ऑन चुनें, कोई छुपा चार्ज नहीं",
    step3: "डॉक्यूमेंट अपलोड करें",
    step3b: "तुरंत जाँच",
    step4: "इंस्टॉलेशन ट्रैक करें",
    step4b: "WhatsApp पर अपडेट",
    typeMessage: "अपना जवाब लिखें…",
    send: "भेजें",
    listening: "सुन रहा हूँ…",
    speak: "जवाब पढ़कर सुनाएँ",
    advisor: "बिज़नेस सलाहकार",
    perMonth: "/महीना",
    inclGst: "GST सहित",
    readyIn: "लगभग {d} दिन में चालू",
    oneTime: "एक बार का सेटअप",
    lockIn: "कॉन्ट्रैक्ट",
    months: "महीने",
    whyThis: "यह क्यों?",
    seeQuote: "कीमत देखें और आगे बढ़ें",
    yourBundle: "आपका बंडल",
    addons: "ऐड-ऑन",
    contract: "लंबा कमिटमेंट, कम कीमत",
    total: "मासिक कुल",
    gst: "GST (18%)",
    subtotal: "सबटोटल",
    firstBill: "पहला बिल",
    vsToday: "अभी के मुकाबले",
    placeOrder: "ऑर्डर करें",
    contactName: "आपका नाम",
    contactPhone: "मोबाइल नंबर",
    placing: "ऑर्डर हो रहा है…",
    consentTitle: "डॉक्यूमेंट जाँचने से पहले",
    agree: "मैं सहमत हूँ, आगे बढ़ें",
    decline: "अभी नहीं",
    documents: "आपके डॉक्यूमेंट",
    upload: "फ़ोटो लें / अपलोड करें",
    useSample: "नमूना इस्तेमाल करें",
    verify: "डॉक्यूमेंट वेरिफ़ाई करें",
    verifying: "जाँच हो रही है…",
    trackOrder: "मेरा ऑर्डर ट्रैक करें",
    orderPlaced: "ऑर्डर हो गया",
    eta: "चालू होने की संभावित तारीख",
    chooseSlot: "इंस्टॉलेशन का समय चुनें",
    updates: "अपडेट",
    deleteData: "सहमति वापस लें और मेरे डॉक्यूमेंट डिलीट करें",
    back: "वापस",
    help: "मदद चाहिए? विशेषज्ञ से बात करें",
  },
} as const;

export type UIKey = keyof (typeof UI)["en"];

export function t(lang: string, key: UIKey, vars?: Record<string, string | number>): string {
  const table = (UI as Record<string, Record<string, string>>)[lang] ?? UI.en;
  let s = table[key] ?? UI.en[key];
  for (const [k, v] of Object.entries(vars ?? {})) s = s.replace(`{${k}}`, String(v));
  return s;
}

const KEY = "udyam.lang";
const EVENT = "udyam-lang";

function readLang(): string {
  try {
    const saved = localStorage.getItem(KEY);
    return saved && LANGS[saved] ? saved : "en";
  } catch {
    return "en"; // storage unavailable
  }
}

function subscribe(cb: () => void) {
  window.addEventListener("storage", cb);
  window.addEventListener(EVENT, cb);
  return () => {
    window.removeEventListener("storage", cb);
    window.removeEventListener(EVENT, cb);
  };
}

export function setStoredLang(l: string) {
  try {
    localStorage.setItem(KEY, l);
  } catch {
    /* ignore */
  }
  window.dispatchEvent(new Event(EVENT));
}

export function useLang(): [string, (l: string) => void] {
  const lang = useSyncExternalStore(subscribe, readLang, () => "en");
  return [lang, setStoredLang];
}
