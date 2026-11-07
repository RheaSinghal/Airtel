"""Product eligibility. Pure functions over the catalogue: no model output is ever trusted here."""
from __future__ import annotations

from dataclasses import dataclass

from ..data import Product, catalogue
from .profile import BusinessProfile


@dataclass(frozen=True)
class Block:
    code: str
    detail: dict

    def as_dict(self) -> dict:
        return {"code": self.code, **self.detail}


def blocks(product: Product, p: BusinessProfile) -> list[Block]:
    """Why `product` cannot be sold to profile `p` (empty list = eligible).

    Bundle-level dependencies (`requires_one_of`) are checked by the bundler, not here.
    """
    out: list[Block] = []
    if p.city_tier is not None and p.city_tier not in product.city_tiers:
        out.append(Block("city_tier", {"tiers": list(product.city_tiers), "tier": p.city_tier}))
    if p.employees is not None and p.employees < product.min_employees:
        out.append(Block("min_employees", {"min": product.min_employees, "have": p.employees}))
    if p.sites is not None and p.sites < product.min_sites:
        out.append(Block("min_sites", {"min": product.min_sites, "have": p.sites}))
    if product.requires_gstin and not p.gst_ok:
        if p.has_gstin and p.gstin_status not in (None, "Active"):
            out.append(Block("gstin_inactive", {"status": p.gstin_status}))
        else:
            out.append(Block("needs_gstin", {}))
    return out


def is_eligible(product_id: str, p: BusinessProfile) -> bool:
    return not blocks(catalogue()[product_id], p)


def dependency_missing(product: Product, bundle_ids: set[str]) -> bool:
    return bool(product.requires_one_of) and not (set(product.requires_one_of) & bundle_ids)


def check_bundle(items: list[tuple[str, int]], p: BusinessProfile) -> list[dict]:
    """Validate an arbitrary bundle (used when the customer edits the quote). Returns problems."""
    cat = catalogue()
    ids = {pid for pid, _ in items}
    problems = []
    for pid, qty in items:
        prod = cat.get(pid)
        if prod is None:
            problems.append({"product_id": pid, "code": "unknown_product"})
            continue
        for b in blocks(prod, p):
            problems.append({"product_id": pid, **b.as_dict()})
        if dependency_missing(prod, ids):
            problems.append({"product_id": pid, "code": "needs_one_of", "options": list(prod.requires_one_of)})
        if qty < 1:
            problems.append({"product_id": pid, "code": "bad_quantity"})
    return problems
