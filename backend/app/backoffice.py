"""Back-office: propensity score, the 'advisor could not close' queue, and funnel insights."""
from __future__ import annotations

from functools import lru_cache

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from . import store
from .data import SEGMENT_CODES, SEGMENT_NAMES, gstin_registry, leads

CAT = ["segment", "lead_source", "city_tier", "has_gstin", "has_udyam", "annual_turnover_band", "current_internet"]
NUMERIC = ["log_employees", "num_sites", "log_spend", "n_interest"]

# Who should work a lead the advisor could not close.
OWNER_RULES = [
    (lambda p: p.get("segment") == "mfg" or (p.get("sites") or 1) >= 6, "field_sales"),
    (lambda p: p.get("segment") == "multi", "field_sales"),
    (lambda p: p.get("segment") == "micro", "channel_partner"),
    (lambda p: True, "telesales"),
]


def _features(df: pd.DataFrame) -> pd.DataFrame:
    """Only facts known when the lead is created (no stage/outcome leakage)."""
    x = pd.DataFrame({
        "segment": df["segment"].astype(str),
        "lead_source": df["lead_source"].fillna("Advisor").astype(str),
        "city_tier": df["city_tier"].astype(str),
        "has_gstin": df["has_gstin"].astype(str),
        "has_udyam": df["has_udyam"].astype(str),
        "annual_turnover_band": df["annual_turnover_band"].fillna("unknown").astype(str),
        "current_internet": df["current_internet"].fillna("None").astype(str),
        "log_employees": np.log1p(df["employee_count"].astype(float)),
        "num_sites": df["num_sites"].astype(float).clip(upper=20),
        "log_spend": np.log1p(df["monthly_telecom_spend_inr"].fillna(0).astype(float)),
        "n_interest": df["products_of_interest"].fillna("").astype(str).str.count(";") + 1,
    })
    return x


@lru_cache
def model() -> dict:
    df = leads()
    y = (df["outcome"] == "Activated").astype(int)
    X = _features(df)
    pipe = Pipeline([
        ("prep", ColumnTransformer([
            ("cat", OneHotEncoder(handle_unknown="ignore"), CAT),
            ("num", StandardScaler(), NUMERIC),
        ])),
        ("clf", LogisticRegression(max_iter=2000, class_weight="balanced", C=0.5)),
    ])
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.25, random_state=7, stratify=y)
    pipe.fit(Xtr, ytr)
    auc = roc_auc_score(yte, pipe.predict_proba(Xte)[:, 1])
    pipe.fit(X, y)  # final model on all data
    # Calibrate the balanced-weights score back to a real activation probability via deciles.
    raw = pipe.predict_proba(X)[:, 1]
    deciles = pd.qcut(raw, 10, labels=False, duplicates="drop")
    rate_by_decile = pd.Series(y.values).groupby(deciles).mean().to_dict()
    edges = np.quantile(raw, np.linspace(0, 1, 11))
    # top drivers (absolute coefficient)
    names = pipe.named_steps["prep"].get_feature_names_out()
    coefs = pipe.named_steps["clf"].coef_[0]
    drivers = sorted(zip(names, coefs), key=lambda t: -abs(t[1]))[:10]
    return {"pipe": pipe, "auc": round(float(auc), 3), "edges": edges, "rates": rate_by_decile,
            "drivers": [{"feature": n.split("__", 1)[-1], "weight": round(float(c), 2)} for n, c in drivers]}


def score_frame(df: pd.DataFrame) -> pd.DataFrame:
    m = model()
    raw = m["pipe"].predict_proba(_features(df))[:, 1]
    dec = np.clip(np.searchsorted(m["edges"], raw, side="right") - 1, 0, 9)
    out = df.copy()
    out["score"] = (raw * 100).round().astype(int)
    out["decile"] = dec + 1
    out["expected_activation"] = [round(float(m["rates"].get(int(d), 0)), 3) for d in dec]
    return out


def profile_to_lead_row(p: dict, source: str = "Website form") -> dict:
    turnover = None
    emp = p.get("employees") or 1
    turnover = "< 40 lakh" if emp <= 3 else "40 lakh - 1.5 cr" if emp <= 10 else "1.5 - 5 cr" if emp <= 30 else "5 - 25 cr"
    return {
        "segment": SEGMENT_NAMES.get(p.get("segment") or "micro"),
        "lead_source": source,
        "city_tier": p.get("city_tier") or 2,
        "has_gstin": "Y" if p.get("has_gstin") else "N",
        "has_udyam": "Y" if p.get("has_udyam") else "N",
        "annual_turnover_band": turnover,
        "current_internet": p.get("current_internet") or "Mobile hotspot",
        "employee_count": emp,
        "num_sites": p.get("sites") or 1,
        "monthly_telecom_spend_inr": p.get("monthly_spend") or 0,
        "products_of_interest": ";".join(p.get("needs") or ["internet"]),
    }


def score_profile(p: dict, source: str = "Website form") -> dict:
    row = score_frame(pd.DataFrame([profile_to_lead_row(p, source)])).iloc[0]
    return {"score": int(row.score), "decile": int(row.decile), "expected_activation": float(row.expected_activation)}


def suggested_owner(p: dict) -> str:
    return next(owner for rule, owner in OWNER_RULES if rule(p))


def queue() -> list[dict]:
    """Leads the digital journey could not close, ranked by propensity, with a suggested owner."""
    items = []
    for s in store.select("sessions", "stage IN ('handoff', 'collecting', 'recommended')", order="updated DESC"):
        p = s.get("profile") or {}
        if not p.get("business_type") and s["stage"] != "handoff":
            continue  # nothing useful collected yet
        sc = score_profile(p, "Advisor")
        rec = (s.get("recommendation") or {})
        tier = (rec.get("tiers") or {}).get(rec.get("default") or "", {})
        items.append({
            "kind": "session", "id": s["id"], "updated": s["updated"], "stage": s["stage"],
            "reason": (s.get("meta") or {}).get("handoff_reason") or {"handoff": "asked_for_human", "collecting": "abandoned_mid_chat",
                                                                   "recommended": "saw_offer_did_not_buy"}[s["stage"]],
            "business": p.get("business_type"), "city": p.get("city"), "segment": p.get("segment"),
            "employees": p.get("employees"), "sites": p.get("sites"),
            "offer_monthly": (tier.get("totals") or {}).get("monthly_total"),
            "owner": suggested_owner(p), "partner_id": s.get("partner_id"), **sc,
        })
    for o in store.select("orders", "status = 'kyc_action_needed'", order="updated DESC"):
        p = o.get("profile") or {}
        sc = score_profile(p, "Advisor")
        items.append({
            "kind": "order", "id": o["id"], "updated": o["updated"], "stage": o["status"], "reason": "kyc_failed",
            "business": p.get("business_type"), "city": p.get("city"), "segment": p.get("segment"),
            "employees": p.get("employees"), "sites": p.get("sites"),
            "offer_monthly": o["quote"]["totals"]["monthly_total"], "owner": "telesales",
            "kyc_issues": [c["message"] for c in (o.get("kyc") or {}).get("checks", []) if c["status"] == "fail"], **sc,
        })
    return sorted(items, key=lambda i: -i["score"])


def historical_call_list(limit: int = 50) -> list[dict]:
    """Dropped historical leads worth a call back, ranked by score (for field sales / partners)."""
    df = leads()
    dropped = df[(df.outcome == "Dropped") & df.drop_reason.isin([
        "Unreachable after 3 attempts", "Owner had no time for a visit", "Visit not scheduled by sales",
        "Quote took too long to arrive", "Quote too complex to understand", "Found paperwork too long", "Decided to wait"])]
    s = score_frame(dropped).sort_values("score", ascending=False).head(limit)
    return [{"lead_id": r.lead_id, "business": r.business_name, "business_type": r.business_type,
             "segment": SEGMENT_CODES[r.segment], "city": r.city, "source": r.lead_source,
             "drop_reason": r.drop_reason, "score": int(r.score), "expected_activation": r.expected_activation,
             "owner": suggested_owner({"segment": SEGMENT_CODES[r.segment], "sites": r.num_sites})}
            for r in s.itertuples(index=False)]


@lru_cache
def insights() -> dict:
    df = leads()
    act = df[df.outcome == "Activated"]
    order = ["Lead", "Contacted", "Needs assessed", "Quote accepted", "KYC complete", "Activated"]
    rank = {s: i for i, s in enumerate(order)}
    reached = df.stage_reached.map(rank)
    funnel = [{"stage": s, "count": int((reached >= i).sum())} for i, s in enumerate(order)]
    seg = []
    for name, g in df.groupby("segment"):
        a = g[g.outcome == "Activated"]
        seg.append({
            "segment": SEGMENT_CODES[name], "name": name, "leads": len(g),
            "conversion": round(len(a) / len(g), 3),
            "cac_per_activation": round(g.acquisition_cost_inr.sum() / max(len(a), 1)),
            "median_monthly": int(a.monthly_bundle_value_inr.median()) if len(a) else 0,
            "churn_6m": round((a.churned_within_6_months == "Y").mean(), 3) if len(a) else None,
        })
    drops = df[df.outcome == "Dropped"].drop_reason.value_counts().head(12)
    calls = act.groupby("customer_follow_up_calls").agg(n=("lead_id", "size"),
                                                         churn=("churned_within_6_months", lambda s: (s == "Y").mean()),
                                                         nps=("nps_score", "mean")).reset_index()
    gst_bad = df[df.outcome == "Activated"].merge(
        pd.DataFrame([{"gstin": k, "status": v["status"]} for k, v in gstin_registry().items()]),
        on="gstin", how="left")
    return {
        "funnel": funnel,
        "activation_rate": round(len(act) / len(df), 3),
        "avg_days_to_activate": round(float(act.days_lead_to_activation.mean()), 1),
        "avg_follow_up_calls": round(float(act.customer_follow_up_calls.mean()), 1),
        "cac_per_activation": round(df.acquisition_cost_inr.sum() / len(act)),
        "segments": seg,
        "drop_reasons": [{"reason": k, "count": int(v)} for k, v in drops.items()],
        "follow_up_vs_churn": [{"calls": int(r.customer_follow_up_calls), "customers": int(r.n),
                                "churn_6m": round(float(r.churn), 3), "nps": round(float(r.nps), 1)} for r in calls.itertuples()],
        "activated_on_inactive_gstin": int(gst_bad.status.isin(["Cancelled", "Suspended"]).sum()),
        "model": {"auc": model()["auc"], "drivers": model()["drivers"]},
    }
