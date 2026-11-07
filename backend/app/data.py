"""Loads the synthetic data pack once and exposes typed lookups."""
from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache

import pandas as pd

from .config import DATA_DIR

SEGMENT_CODES = {
    "Micro retail & services": "micro",
    "Professional offices": "prof",
    "Small multi-site businesses": "multi",
    "Small manufacturers": "mfg",
}
SEGMENT_NAMES = {v: k for k, v in SEGMENT_CODES.items()}


@dataclass(frozen=True)
class Product:
    id: str
    category: str
    name: str
    description: str
    unit: str
    price_min: int
    price_max: int
    setup_fee: int
    min_contract_months: int
    city_tiers: tuple[int, ...]
    min_employees: int
    min_sites: int
    requires_gstin: bool
    requires_one_of: tuple[str, ...]
    install_days: int
    target_segments: tuple[str, ...] = field(default_factory=tuple)


def _split(value, sep=";") -> tuple[str, ...]:
    if pd.isna(value) or value == "":
        return ()
    return tuple(v.strip() for v in str(value).split(sep) if v.strip())


@lru_cache
def catalogue() -> dict[str, Product]:
    df = pd.read_csv(DATA_DIR / "product_catalogue.csv")
    products = {}
    for r in df.itertuples(index=False):
        products[r.product_id] = Product(
            id=r.product_id,
            category=r.category,
            name=r.product_name,
            description=r.description,
            unit=r.unit,
            price_min=int(r.price_min_inr_per_month),
            price_max=int(r.price_max_inr_per_month),
            setup_fee=int(r.one_time_setup_inr),
            min_contract_months=int(r.min_contract_months),
            city_tiers=tuple(int(t) for t in _split(r.available_city_tiers)),
            min_employees=int(r.min_employees),
            min_sites=int(r.min_sites),
            requires_gstin=str(r.requires_gstin).upper() == "Y",
            requires_one_of=_split(r.requires_one_of, "|"),
            install_days=int(r.typical_install_days),
            target_segments=_split(r.target_segments),
        )
    return products


@lru_cache
def gstin_registry() -> dict[str, dict]:
    df = pd.read_csv(DATA_DIR / "mock_gstin_registry.csv", dtype=str)
    return {r["gstin"]: r for r in df.to_dict("records")}


@lru_cache
def udyam_registry() -> dict[str, dict]:
    df = pd.read_csv(DATA_DIR / "mock_udyam_registry.csv", dtype=str)
    return {r["udyam_number"]: r for r in df.to_dict("records")}


@lru_cache
def leads() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "smb_leads.csv")


@lru_cache
def cities() -> dict[str, dict]:
    """City -> {tier, state}, derived from the leads data."""
    df = leads()[["city", "city_tier", "state"]].drop_duplicates("city")
    return {r.city: {"tier": int(r.city_tier), "state": r.state} for r in df.itertuples(index=False)}


@lru_cache
def business_types() -> dict[str, str]:
    """Business type -> segment code, derived from the leads data."""
    df = leads()[["business_type", "segment"]].drop_duplicates("business_type")
    return {r.business_type: SEGMENT_CODES[r.segment] for r in df.itertuples(index=False)}
