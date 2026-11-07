"use client";

import { SPEECH_TAGS } from "./i18n";

/* eslint-disable @typescript-eslint/no-explicit-any */
type Recognition = any;

export function speechSupported(): boolean {
  return typeof window !== "undefined" && !!((window as any).SpeechRecognition || (window as any).webkitSpeechRecognition);
}

/** Starts one-shot speech recognition. Returns a stop function. */
export function listen(lang: string, onText: (text: string) => void, onEnd: () => void): () => void {
  const Ctor = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
  if (!Ctor) {
    onEnd();
    return () => {};
  }
  const rec: Recognition = new Ctor();
  rec.lang = SPEECH_TAGS[lang] ?? "en-IN";
  rec.interimResults = false;
  rec.maxAlternatives = 1;
  rec.onresult = (e: any) => onText(e.results[0][0].transcript);
  rec.onend = onEnd;
  rec.onerror = onEnd;
  rec.start();
  return () => rec.stop();
}

export function speak(text: string, lang: string) {
  if (typeof window === "undefined" || !window.speechSynthesis || !text) return;
  window.speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(text.replace(/[•→▲▼]/g, ""));
  u.lang = SPEECH_TAGS[lang] ?? "en-IN";
  window.speechSynthesis.speak(u);
}
