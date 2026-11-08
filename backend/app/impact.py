"""Impact simulator: what the digital journey does to the funnel, computed from smb_leads.csv.

Each lever recovers a share of the drops it addresses (by drop reason, at the stage they
happen). Recovered leads then face the baseline conversion of every later stage. Everything
else (costs, churn, bundle value, install times) comes from the data.
"""
from __future__ import annotations

from functools import lru_cache

import numpy as np

from .data import catalogue, leads

STAGES = ["Lead", "Contacted", "Needs assessed", "Quote accepted", "KYC complete", "Activated"]

# lever -> (stage where the drop happens, {drop_reason: share of the slider applied})
LEVERS = {
    "self_serve": {
        "label": "Self-serve sign-up (no callback needed)",
        "stage": "Lead",
        "reasons": {"Unreachable after 3 attempts": 1.0, "Wrong or invalid number": 1.0},
        "default": 0.25,
    },
    "advisor": {
        "label": "GenAI advisor replaces the sales visit",
        "stage": "Contacted",
        "reasons": {"Owner had no time for a visit": 1.0, "Visit not scheduled by sales": 1.0, "Only wanted a mobile plan": 0.8},
        "default": 0.35,
    },
    "instant_quote": {
        "label": "Instant, transparent quote",
        "stage": "Needs assessed",
        "reasons": {"Quote too complex to understand": 1.0, "Quote took too long to arrive": 1.0,
                    "Price too high": 0.3, "Competitor offered cheaper plan": 0.3, "Decided to wait": 0.3},
        "default": 0.35,
    },
    "smart_kyc": {
        "label": "Smart KYC + DigiLocker + e-sign",
        "stage": "Quote accepted",
        "reasons": {"Missing GST or Udyam document": 1.0, "Found paperwork too long": 1.0,
                    "Authorised signatory not available": 1.0, "Document details did not match": 1.0},
        "default": 0.4,
    },
    "fulfilment": {
        "label": "Tracker, AirFiber fallback, UPI retry",
        "stage": "KYC complete",
        "reasons": {"Site not feasible for fibre": 1.0, "First payment failed": 1.0,
                    "Installation delayed beyond 21 days": 0.5, "Customer cancelled before install": 0.5},
        "default": 0.3,
    },
}

DIGITAL_COST_PER_LEAD_SOURCE = "Website form"

PRESETS = {
    "conservative": {"levers": {"self_serve": 0.25, "advisor": 0.35, "instant_quote": 0.35, "smart_kyc": 0.4, "fulfilment": 0.3},
                     "digital_share": 0.3, "status_calls": 2.0},
    "expected": {"levers": {"self_serve": 0.4, "advisor": 0.5, "instant_quote": 0.5, "smart_kyc": 0.6, "fulfilment": 0.5},
                 "digital_share": 0.5, "status_calls": 1.5},
    "ambitious": {"levers": {"self_serve": 0.6, "advisor": 0.7, "instant_quote": 0.7, "smart_kyc": 0.8, "fulfilment": 0.7},
                  "digital_share": 0.7, "status_calls": 1.0},
}


@lru_cache
def baseline() -> dict:
    df = leads()
    rank = {s: i for i, s in enumerate(STAGES)}
    reached = df.stage_reached.map(rank)
    counts = [int((reached >= i).sum()) for i in range(len(STAGES))]
    dropped = df[df.outcome == "Dropped"]
    drops = {k: int(v) for k, v in dropped.groupby(["stage_reached", "drop_reason"]).size().items()}
    act = df[df.outcome == "Activated"]
    cost_by_source = df.groupby("lead_source").acquisition_cost_inr.mean().to_dict()
    calls = act.groupby("customer_follow_up_calls").churned_within_6_months.apply(lambda s: (s == "Y").mean()).to_dict()

    cat = catalogue()

    def bundle_days(b: str) -> int:
        ids = [x.split("x")[0] for x in str(b).split(";") if x]
        return max((cat[i].install_days for i in ids if i in cat), default=5)

    return {
        "counts": counts,
        "drops": drops,
        "total_cost": float(df.acquisition_cost_inr.sum()),
        "avg_cost_per_lead": float(df.acquisition_cost_inr.mean()),
        "digital_cost_per_lead": float(cost_by_source[DIGITAL_COST_PER_LEAD_SOURCE]),
        "mean_bundle": float(act.monthly_bundle_value_inr.mean()),
        "churn": float((act.churned_within_6_months == "Y").mean()),
        "churn_by_calls": {int(k): float(v) for k, v in calls.items()},
        "avg_calls": float(act.customer_follow_up_calls.mean()),
        "days": float(act.days_lead_to_activation.mean()),
        "days_digital": float(np.mean([bundle_days(b) for b in act.bundle_products]) + 1),  # install + same-day KYC/e-sign
    }


def _churn_for_calls(b: dict, calls: float) -> float:
    pts = sorted(b["churn_by_calls"].items())
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return float(np.interp(calls, xs, ys))


def _funnel(b: dict, levers: dict[str, float]) -> list[float]:
    counts = b["counts"]
    out = [float(counts[0])]
    for i in range(len(STAGES) - 1):
        stage = STAGES[i]
        moved = counts[i + 1]
        for key, cfg in LEVERS.items():
            if cfg["stage"] != stage:
                continue
            share = levers.get(key, 0.0)
            moved += sum(b["drops"].get((stage, reason), 0) * w * share for reason, w in cfg["reasons"].items())
        conv = moved / counts[i] if counts[i] else 0
        out.append(out[-1] * conv)
    return out


def simulate(levers: dict[str, float] | None = None, digital_share: float = 0.3, status_calls: float = 2.0) -> dict:
    b = baseline()
    lv = {k: float(np.clip((levers or {}).get(k, cfg["default"]), 0, 1)) for k, cfg in LEVERS.items()}
    base_f = [float(c) for c in b["counts"]]
    new_f = _funnel(b, lv)

    leads_n = base_f[0]
    base_act, new_act = base_f[-1], new_f[-1]
    non_digital_cost = b["avg_cost_per_lead"]  # today's blended cost per lead
    new_cost = leads_n * (digital_share * b["digital_cost_per_lead"] + (1 - digital_share) * non_digital_cost)
    base_cac = b["total_cost"] / base_act
    new_cac = new_cost / new_act

    new_churn = _churn_for_calls(b, status_calls)
    quarters = 4
    base_arr = base_act * quarters * b["mean_bundle"] * 12 * (1 - b["churn"])
    new_arr = new_act * quarters * b["mean_bundle"] * 12 * (1 - new_churn)

    contributions = []
    for key, cfg in LEVERS.items():
        solo = _funnel(b, {key: lv[key]})[-1]
        contributions.append({"lever": key, "label": cfg["label"], "extra_activations": round(solo - base_act)})

    def pack(f):
        return [{"stage": s, "count": round(c)} for s, c in zip(STAGES, f)]

    return {
        "levers": [{"key": k, "label": c["label"], "value": lv[k], "stage": c["stage"],
                    "addresses": list(c["reasons"])} for k, c in LEVERS.items()],
        "digital_share": digital_share, "status_calls": status_calls,
        "baseline": {"funnel": pack(base_f), "activations": round(base_act), "rate": round(base_act / leads_n, 4),
                     "cac": round(base_cac), "days": round(b["days"], 1), "churn_6m": round(b["churn"], 3),
                     "status_calls": round(b["avg_calls"], 1), "arr": round(base_arr)},
        "scenario": {"funnel": pack(new_f), "activations": round(new_act), "rate": round(new_act / leads_n, 4),
                     "cac": round(new_cac), "days": round(b["days_digital"], 1), "churn_6m": round(new_churn, 3),
                     "status_calls": status_calls, "arr": round(new_arr)},
        "contributions": contributions,
        "presets": PRESETS,
        "assumptions": [
            "One quarter of leads (Apr-Jun 2026, 5,000 leads); annual figures assume four similar quarters.",
            "Recovered leads convert at today's rates for every later stage.",
            f"Digital leads cost the same as today's website leads (₹{b['digital_cost_per_lead']:.0f} per lead); others keep today's blended cost.",
            f"Revenue uses the mean activated bundle (₹{b['mean_bundle']:,.0f}/month) and 6-month churn as the retention haircut.",
            "Churn for a given number of status calls is read from activated customers in the data.",
            "Days to activate = slowest product's install time in the bundle + 1 day (KYC and e-sign are same-day).",
        ],
    }
