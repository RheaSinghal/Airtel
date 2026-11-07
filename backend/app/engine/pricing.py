"""Transparent pricing.

The catalogue gives each product a monthly price *range*. We place the price inside that range by
commitment: the product's minimum contract gets the top of the range, and every extra month of
commitment moves the price linearly towards the bottom, reaching it at minimum + 24 months.
One rule, easy to explain to an owner: "commit longer, pay less".
"""
from __future__ import annotations

from dataclasses import asdict, dataclass

from ..config import GST_RATE
from ..data import Product, catalogue

CONTRACT_OPTIONS = (12, 24, 36)


def effective_contract(product: Product, chosen_months: int) -> int:
    return max(chosen_months, product.min_contract_months)


def unit_price(product: Product, chosen_months: int) -> int:
    months = effective_contract(product, chosen_months)
    frac = min(max(months - product.min_contract_months, 0) / 24, 1.0)
    return round(product.price_max - (product.price_max - product.price_min) * frac)


@dataclass
class QuoteLine:
    product_id: str
    name: str
    category: str
    unit: str
    quantity: int
    unit_price: int
    monthly: int
    setup: int
    contract_months: int
    install_days: int
    optional: bool = False
    reason: str = ""


def build_lines(items: list[dict], chosen_months: int) -> list[QuoteLine]:
    cat = catalogue()
    lines = []
    for it in items:
        prod = cat[it["product_id"]]
        qty = int(it.get("quantity", 1))
        price = unit_price(prod, chosen_months)
        lines.append(
            QuoteLine(
                product_id=prod.id,
                name=prod.name,
                category=prod.category,
                unit=prod.unit,
                quantity=qty,
                unit_price=price,
                monthly=price * qty,
                setup=prod.setup_fee * qty,
                contract_months=effective_contract(prod, chosen_months),
                install_days=prod.install_days,
                optional=bool(it.get("optional", False)),
                reason=it.get("reason", ""),
            )
        )
    return lines


def totals(lines: list[QuoteLine], current_spend: int | None = None) -> dict:
    monthly = sum(l.monthly for l in lines)
    setup = sum(l.setup for l in lines)
    monthly_gst = round(monthly * GST_RATE)
    setup_gst = round(setup * GST_RATE)
    out = {
        "monthly_before_tax": monthly,
        "monthly_gst": monthly_gst,
        "monthly_total": monthly + monthly_gst,
        "setup_before_tax": setup,
        "setup_gst": setup_gst,
        "setup_total": setup + setup_gst,
        "first_bill": monthly + monthly_gst + setup + setup_gst,
        "lock_in_months": max((l.contract_months for l in lines), default=0),
        "ready_in_days": max((l.install_days for l in lines), default=0),
    }
    if current_spend:
        out["current_spend"] = current_spend
        out["difference_vs_current"] = monthly - current_spend
    return out


def quote(items: list[dict], chosen_months: int = 12, current_spend: int | None = None) -> dict:
    lines = build_lines(items, chosen_months)
    return {
        "contract_months": chosen_months,
        "contract_options": list(CONTRACT_OPTIONS),
        "lines": [asdict(l) for l in lines],
        "totals": totals(lines, current_spend),
    }
