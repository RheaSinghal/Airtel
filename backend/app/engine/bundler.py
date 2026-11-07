"""Turns a business profile into three bundle tiers (Essential / Recommended / Pro).

Deterministic: same profile -> same bundle. Every product that is swapped or left out is recorded
with a reason code so the advisor can explain it in plain language.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from ..data import catalogue
from .profile import BusinessProfile
from .rules import blocks, dependency_missing

# Cheapest-first fallbacks used to satisfy `requires_one_of` dependencies.
CONNECTIVITY_FALLBACK = ["P04", "P01", "P02", "P03", "P05", "P06"]


@dataclass
class Item:
    product_id: str
    quantity: int
    reason: str            # reason code -> plain-language text in i18n
    need: str | None = None
    optional: bool = False

    def as_dict(self) -> dict:
        return {
            "product_id": self.product_id,
            "quantity": self.quantity,
            "reason": self.reason,
            "need": self.need,
            "optional": self.optional,
        }


@dataclass
class Note:
    code: str              # swapped | excluded | added_dependency | budget
    product_id: str | None = None
    instead_of: str | None = None
    blocks: list[dict] = field(default_factory=list)
    need: str | None = None

    def as_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if v not in (None, [])}


# ---------------------------------------------------------------- candidates per need

def _internet_candidates(p: BusinessProfile) -> list[str]:
    seg = p.segment
    emp = p.employees or 1
    wants_dedicated = "dedicated_line" in p.needs
    if seg == "mfg" or wants_dedicated:
        if emp >= 25 and wants_dedicated:
            return ["P06", "P05", "P03", "P02", "P01"]
        if emp >= 10:
            return ["P05", "P03", "P02", "P01"]
        return ["P03", "P02", "P01", "P04"]
    if p.fibre_available is False:
        return ["P04"]
    if seg == "prof":
        if emp >= 15 and p.city_tier == 1:
            return ["P03", "P02", "P01", "P04"]
        return ["P02", "P01", "P04"]
    if seg == "multi":
        return ["P02", "P01", "P04"]
    return ["P01", "P04"]  # micro and unknown


def _mobile_product(p: BusinessProfile) -> list[str]:
    return ["P08", "P07"] if p.segment in ("multi", "mfg") else ["P07", "P08"]


def _desk_users(p: BusinessProfile) -> int:
    """People who need a mailbox / protected device; not every employee sits at a computer."""
    emp = p.employees or 1
    sites = p.sites or 1
    share = {"micro": 0.5, "prof": 0.6, "multi": 0.25, "mfg": 0.3}.get(p.segment or "micro", 0.5)
    users = max(1, math.ceil(emp * share))
    if p.segment == "multi":
        users = max(users, sites)
    return min(users, 50)


def _qty(p: BusinessProfile, need: str) -> int:
    emp = p.employees or 1
    sites = p.sites or 1
    seg = p.segment
    if need == "mobile_lines":
        if p.mobile_lines:
            return p.mobile_lines
        return 1 if seg == "micro" else min(max(1, math.ceil(emp * 0.2)), 20)
    if need in ("email", "security"):
        if need == "security" and p.devices:
            return p.devices
        return _desk_users(p)
    if need == "cctv":
        return p.cameras or (4 if seg == "mfg" else 2) * sites
    if need == "telephony":
        return max(2, sites) if seg != "prof" else 2
    if need == "iot":
        return p.machines or 5
    if need == "fleet":
        return p.vehicles or 3
    if need in ("payments", "internet", "backup_internet", "wifi", "multi_site_mgmt"):
        return sites
    return 1


NEED_PRODUCTS: dict[str, list[str]] = {
    "backup_internet": ["P09"],
    "payments": ["P19"],
    "messaging": ["P15", "P14"],
    "email": ["P16"],
    "backup": ["P17"],
    "security": ["P20"],
    "cctv": ["P23"],
    "wifi": ["P22"],
    "website": ["P18"],
    "telephony": ["P12"],
    "toll_free": ["P13"],
    "static_ip": ["P11"],
    "multi_site_mgmt": ["P10"],
    "iot": ["P24"],
    "fleet": ["P25"],
}

# Needs that make it into the cheapest tier, per segment.
ESSENTIAL_NEEDS = {
    "micro": {"payments"},
    "prof": {"email"},
    "multi": {"payments", "backup_internet"},
    "mfg": {"security"},
}

# Upgrades added in Pro when eligible.
PRO_UPGRADES = {
    "micro": ["wifi", "cctv", "security"],
    "prof": ["backup_internet", "security", "backup", "static_ip"],
    "multi": ["backup_internet", "cctv", "wifi", "security", "firewall", "multi_site_mgmt"],
    "mfg": ["backup_internet", "firewall", "backup", "iot"],
}


class _Builder:
    def __init__(self, p: BusinessProfile):
        self.p = p
        self.cat = catalogue()
        self.items: list[Item] = []
        self.notes: list[Note] = []

    @property
    def ids(self) -> set[str]:
        return {i.product_id for i in self.items}

    def try_add(self, candidates: list[str], qty: int, reason: str, need: str | None, optional=False) -> bool:
        """Add the first eligible candidate; record swaps/exclusions. Returns True if something was added."""
        first = candidates[0]
        first_blocks = []
        for pid in candidates:
            if pid in self.ids:
                return True
            b = blocks(self.cat[pid], self.p)
            if not b:
                if pid != first:
                    self.notes.append(Note("swapped", product_id=pid, instead_of=first, blocks=first_blocks, need=need))
                self.items.append(Item(pid, qty, reason, need, optional))
                return True
            if pid == first:
                first_blocks = [x.as_dict() for x in b]
        self.notes.append(Note("excluded", product_id=first, blocks=first_blocks, need=need))
        return False

    def add_need(self, need: str, optional=False):
        p = self.p
        if need == "internet" or need == "dedicated_line":
            self.try_add(_internet_candidates(p), p.sites or 1, "internet_" + (p.segment or "micro"), "internet", optional)
        elif need == "mobile_lines":
            self.try_add(_mobile_product(p), _qty(p, need), "mobile_lines", need, optional)
        elif need == "firewall":
            self.try_add(["P21"], p.sites or 1, "firewall", "security", optional)
        elif need in NEED_PRODUCTS:
            self.try_add(NEED_PRODUCTS[need], _qty(p, need), need, need, optional)

    def fix_dependencies(self):
        """Every product with requires_one_of gets a connectivity product, or is dropped with a reason."""
        for item in list(self.items):
            prod = self.cat[item.product_id]
            if not dependency_missing(prod, self.ids):
                continue
            preferred = [c for c in _internet_candidates(self.p) if c in prod.requires_one_of]
            options = preferred + [c for c in CONNECTIVITY_FALLBACK if c in prod.requires_one_of and c not in preferred]
            for pid in options:
                if not blocks(self.cat[pid], self.p):
                    self.items.insert(0, Item(pid, self.p.sites or 1, "dependency", "internet"))
                    self.notes.append(Note("added_dependency", product_id=pid, instead_of=item.product_id))
                    break
            else:
                self.items.remove(item)
                self.notes.append(Note("excluded", product_id=item.product_id, blocks=[{"code": "needs_one_of", "options": list(prod.requires_one_of)}], need=item.need))


def _build(p: BusinessProfile, needs: list[str], extra: list[str] = ()) -> _Builder:
    b = _Builder(p)
    if not p.only_mobile:
        b.add_need("dedicated_line" if "dedicated_line" in needs else "internet")
    if p.only_mobile or "mobile_lines" in needs:
        b.add_need("mobile_lines")
    for n in needs:
        if n not in ("internet", "dedicated_line", "mobile_lines"):
            b.add_need(n)
    for n in extra:
        b.add_need(n, optional=True)
    b.fix_dependencies()
    return b


def recommend(p: BusinessProfile) -> dict:
    """Three tiers. 'recommended' covers everything the owner asked for."""
    seg = p.segment or "micro"
    asked = list(dict.fromkeys(p.needs))  # de-dupe, keep order

    essential_needs = [n for n in asked if n in ESSENTIAL_NEEDS.get(seg, set()) or n == "mobile_lines"]
    essential = _build(p, essential_needs)
    recommended = _build(p, asked)
    pro_extra = [] if p.only_mobile else [n for n in PRO_UPGRADES.get(seg, []) if n not in asked]
    pro = _build(p, asked, extra=pro_extra)

    def pack(b: _Builder) -> dict:
        return {"items": [i.as_dict() for i in b.items], "notes": [n.as_dict() for n in b.notes]}

    tiers = {"essential": pack(essential), "recommended": pack(recommended), "pro": pack(pro)}
    # Drop tiers identical to 'recommended' (or empty) so the owner never sees two identical options.
    def key(t):
        return tuple(sorted((i["product_id"], i["quantity"]) for i in t["items"]))

    rec_key = key(tiers["recommended"])
    out = {
        name: t
        for name, t in tiers.items()
        if t["items"] and (name == "recommended" or key(t) != rec_key)
    }
    return {"tiers": out, "default": "recommended" if "recommended" in out else next(iter(out), None)}


def addon_suggestions(p: BusinessProfile, bundle_ids: set[str]) -> list[dict]:
    """Eligible products not in the bundle that the owner can toggle on in the quote screen."""
    cat = catalogue()
    seg = p.segment or "micro"
    out = []
    for pid, prod in cat.items():
        if pid in bundle_ids or seg not in prod.target_segments:
            continue
        if prod.category == "Connectivity" and pid not in ("P09", "P11", "P07", "P08"):
            continue  # don't offer a second primary line as an add-on
        if blocks(prod, p):
            continue
        if prod.requires_one_of and not (set(prod.requires_one_of) & bundle_ids):
            continue
        need = next((n for n, ids in NEED_PRODUCTS.items() if pid in ids), None)
        qty = _qty(p, need) if need else (_qty(p, "mobile_lines") if pid in ("P07", "P08") else 1)
        out.append({"product_id": pid, "quantity": qty, "reason": need or "addon", "need": need, "optional": True})
    return out
