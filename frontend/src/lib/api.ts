export type Chip = {
  label: string;
  payload: Record<string, unknown>;
  selected?: boolean;
  primary?: boolean;
};

export type QuoteLine = {
  product_id: string;
  name: string;
  category: string;
  unit: string;
  quantity: number;
  unit_price: number;
  monthly: number;
  setup: number;
  contract_months: number;
  install_days: number;
  optional?: boolean;
  why?: string;
  description?: string;
  need?: string | null;
};

export type Totals = {
  monthly_before_tax: number;
  monthly_gst: number;
  monthly_total: number;
  setup_before_tax: number;
  setup_gst: number;
  setup_total: number;
  first_bill: number;
  lock_in_months: number;
  ready_in_days: number;
  current_spend?: number;
  difference_vs_current?: number;
};

export type Tier = { label: string; lines: QuoteLine[]; totals: Totals; notes: string[] };

export type Offer = {
  tiers: Record<string, Tier>;
  default: string | null;
  addons: QuoteLine[];
  contract_months: number;
  why_not?: { product_id: string; name: string; reasons: string[] }[];
};

export type Message = {
  role: "assistant" | "user";
  text: string;
  chips?: Chip[];
  multi?: boolean;
  kind?: string;
  slot?: string;
  recommendation?: Offer;
  explanation?: string;
};

export type Profile = Record<string, unknown> & {
  business_type?: string;
  segment?: string;
  city?: string;
  employees?: number;
  sites?: number;
  has_gstin?: boolean;
  monthly_spend?: number;
  needs?: string[];
};

export type Session = {
  id: string;
  lang: string;
  stage: string;
  profile: Profile;
  messages: Message[];
  recommendation: Offer | null;
  order_id: string | null;
  partner_id: string | null;
};

export type Check = { id: string; status: "pass" | "warn" | "fail" | "info"; code: string; doc: string | null; message: string };

export type Stage = {
  stage: string;
  title: string;
  body: string;
  state: "done" | "current" | "next" | "upcoming" | "blocked";
  at?: string;
  expected?: string;
};

export type Order = {
  id: string;
  status: string;
  lang: string;
  created: string;
  profile: Profile;
  items: { product_id: string; quantity: number }[];
  contract_months: number;
  quote: { lines: QuoteLine[]; totals: Totals };
  consent: { accepted: boolean; at: string; withdrawn_at: string | null } | null;
  kyc: { verdict: string; checks: Check[]; gst_verified: boolean } | null;
  esign: Partial<ESign>;
  digilocker: boolean;
  documents: Record<string, { fields: Record<string, string>; quality: Record<string, unknown>; detected_type: string | null }>;
  tracker: {
    order_id: string;
    status: string;
    stages: Stage[];
    products: { product_id: string; name: string; ready_by: string }[];
    slot: string | null;
    notifications: { at: string; channel: string; title: string; body: string }[];
    eta: string;
  };
};

export const errMsg = (e: unknown, fallback = "Something went wrong") =>
  e instanceof ApiError && typeof e.detail === "string" ? e.detail : fallback;

export class ApiError extends Error {
  constructor(public status: number, public detail: unknown) {
    super(typeof detail === "string" ? detail : `Request failed (${status})`);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`/api${path}`, {
    ...init,
    headers: init?.body instanceof FormData ? init.headers : { "Content-Type": "application/json", ...init?.headers },
    cache: "no-store",
  });
  const body = await res.json().catch(() => null);
  if (!res.ok) throw new ApiError(res.status, body?.detail ?? body);
  return body as T;
}

const post = <T,>(path: string, data?: unknown) =>
  request<T>(path, { method: "POST", body: data instanceof FormData ? data : JSON.stringify(data ?? {}) });

export const api = {
  meta: () => request<{ languages: Record<string, string>; llm: boolean; cities: string[]; retention_days: number }>("/meta"),
  startSession: (lang: string, partner_id?: string | null) =>
    post<Session>("/advisor/sessions", { lang, channel: partner_id ? "partner" : "web", partner_id }),
  getSession: (id: string) => request<Session>(`/advisor/sessions/${id}`),
  send: (id: string, body: { text?: string; payload?: Record<string, unknown>; lang?: string }) =>
    post<{ messages: Message[]; stage: string; profile: Profile; recommendation: Offer | null }>(`/advisor/sessions/${id}/messages`, body),
  quote: (profile: Profile, items: { product_id: string; quantity: number }[], contract_months: number, lang: string) =>
    post<{ lines: QuoteLine[]; totals: Totals; problems: { product_id: string; code: string; message: string }[] }>("/quote", {
      profile,
      items,
      contract_months,
      lang,
    }),
  offer: (profile: Profile, contract_months: number, lang: string) =>
    post<Offer>("/offer", { profile, items: [], contract_months, lang }),
  createOrder: (data: {
    session_id?: string | null;
    profile: Profile;
    items: { product_id: string; quantity: number }[];
    contract_months: number;
    lang: string;
    contact?: Record<string, string>;
  }) => post<Order>("/orders", data),
  order: (id: string) => request<Order>(`/orders/${id}`),
  consentText: (lang: string) =>
    request<{ version: string; title: string; purpose: string; data: string[]; how: string; rights: string; share: string }>(
      `/kyc/consent-text?lang=${lang}`,
    ),
  consent: (id: string, accepted: boolean) => post(`/orders/${id}/consent`, { accepted }),
  withdraw: (id: string) => post<{ ok: boolean; message: string }>(`/orders/${id}/consent/withdraw`),
  upload: (id: string, slot: string, file: File) => {
    const fd = new FormData();
    fd.append("file", file);
    return post<DocResult>(`/orders/${id}/documents/${slot}`, fd);
  },
  uploadSample: (id: string, slot: string, applicant: string) =>
    post<DocResult>(`/orders/${id}/documents/${slot}/sample/${applicant}`),
  samples: () => request<string[]>("/kyc/samples"),
  verify: (id: string, has_udyam?: boolean | null) =>
    post<{ verdict: string; checks: Check[]; gst_verified: boolean; blocked_products: { message: string }[]; order: Order }>(
      `/orders/${id}/kyc/verify`,
      { has_udyam },
    ),
  slot: (id: string, slot: string) => post<Order>(`/orders/${id}/slot`, { slot }),
  dlStart: (id: string, mobile: string) => post<{ sent_to: string; demo_otp: string }>(`/orders/${id}/digilocker/start`, { mobile }),
  dlAuthorise: (id: string, otp: string) => post<{ available: string[] }>(`/orders/${id}/digilocker/authorise`, { otp }),
  dlFetch: (id: string, gstin: string) =>
    post<{ fetched: { slot: string; issuer: string }[]; still_needed: string[]; gstin_status: string }>(`/orders/${id}/digilocker/fetch`, { gstin }),
  esignRequest: (id: string) =>
    post<{ agreement: Agreement; document_hash: string; demo_otp: string }>(`/orders/${id}/esign/request`),
  esignVerify: (id: string, otp: string) => post<ESign>(`/orders/${id}/esign/verify`, { otp }),
  waSimulate: (phone: string, text: string) => post<{ replies: WaReply[] }>("/whatsapp/simulate", { phone, text }),
  gstin: (g: string) => request<Record<string, unknown>>(`/gstin/${encodeURIComponent(g)}`),
  // back-office
  queue: () => request<QueueItem[]>("/backoffice/queue"),
  callList: () => request<CallItem[]>("/backoffice/call-list?limit=40"),
  insights: () => request<Insights>("/backoffice/insights"),
  bill: (id: string) => request<Bill>(`/orders/${id}/bill`),
  tickets: (id: string) => request<Ticket[]>(`/orders/${id}/tickets`),
  newTicket: (id: string, text: string, category?: string) => post<Ticket>(`/orders/${id}/tickets`, { text, category }),
  supportCategories: () => request<Record<string, string>>("/support/categories"),
  scenarios: () => request<ScenarioRun>("/backoffice/scenarios"),
  impact: (body: { levers?: Record<string, number>; digital_share?: number; status_calls?: number }) => post<Impact>("/impact", body),
  boOrders: () =>
    request<{ id: string; status: string; created: string; business: string; city: string; monthly: number; kyc: string | null }[]>(
      "/backoffice/orders",
    ),
  advance: (id: string, to?: string) => post<Order>(`/backoffice/orders/${id}/advance`, { to }),
};

export type ESign = { signed: boolean; signed_at?: string; method?: string; document_hash: string; requested_at: string };

export type Agreement = {
  order_id: string;
  business: string;
  city: string;
  lines: { product: string; qty: number; monthly: number; setup: number; contract_months: number }[];
  monthly_total_incl_gst: number;
  setup_total_incl_gst: number;
  lock_in_months: number;
  terms_version: string;
};

export type WaReply = { text: string; buttons?: { id: string; title: string }[]; list?: { id: string; title: string }[] };

export type DocResult = {
  slot: string;
  detected_type: string | null;
  quality: { blur_score: number; rotation_deg: number; confidence: number; unreadable: boolean; source: string };
  fields: Record<string, string>;
};

export type QueueItem = {
  kind: "session" | "order";
  id: string;
  updated: string;
  stage: string;
  reason: string;
  business?: string;
  city?: string;
  segment?: string;
  employees?: number;
  sites?: number;
  offer_monthly?: number;
  owner: string;
  partner_id?: string;
  score: number;
  decile: number;
  expected_activation: number;
  kyc_issues?: string[];
};

export type CallItem = {
  lead_id: string;
  business: string;
  business_type: string;
  segment: string;
  city: string;
  source: string;
  drop_reason: string;
  score: number;
  expected_activation: number;
  owner: string;
};

export type Bill = {
  order_id: string;
  period: string;
  due_date: string;
  lines: { name: string; category: string; quantity: number; amount: number }[];
  subtotal: number;
  gst: number;
  total: number;
  upi_link: string;
  separate_bills_before: number;
  categories: string[];
};

export type Ticket = {
  id: string;
  created: string;
  category: string;
  text: string;
  status: string;
  detail: { label: string; team: string; priority: string; resolve_by: string; diagnostics: { line_test: string; action: string } | null };
};

export type ImpactSide = {
  funnel: { stage: string; count: number }[];
  activations: number;
  rate: number;
  cac: number;
  days: number;
  churn_6m: number;
  status_calls: number;
  arr: number;
};

export type Impact = {
  levers: { key: string; label: string; value: number; stage: string; addresses: string[] }[];
  digital_share: number;
  status_calls: number;
  baseline: ImpactSide;
  scenario: ImpactSide;
  contributions: { lever: string; label: string; extra_activations: number }[];
  presets: Record<string, { levers: Record<string, number>; digital_share: number; status_calls: number }>;
  assumptions: string[];
};

export type ScenarioRun = {
  passed: number;
  total: number;
  avg_turns: number;
  results: {
    id: string;
    title: string;
    input: string;
    lang: string;
    passed: boolean;
    failures: string[];
    questions: string[];
    turns: number;
    segment: string;
    bundle: { product_id: string; name: string; qty: number }[];
    monthly_total: number;
    excluded: string[];
  }[];
};

export type Insights = {
  funnel: { stage: string; count: number }[];
  activation_rate: number;
  avg_days_to_activate: number;
  avg_follow_up_calls: number;
  cac_per_activation: number;
  segments: { segment: string; name: string; leads: number; conversion: number; cac_per_activation: number; median_monthly: number; churn_6m: number }[];
  drop_reasons: { reason: string; count: number }[];
  follow_up_vs_churn: { calls: number; customers: number; churn_6m: number; nps: number }[];
  activated_on_inactive_gstin: number;
  model: { auc: number; drivers: { feature: string; weight: number }[] };
};

export const inr = (n: number | undefined | null) =>
  n == null ? "–" : "₹" + Math.round(n).toLocaleString("en-IN");
