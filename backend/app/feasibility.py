"""Mock coverage check by PIN code (stands in for the network inventory / GIS API).

Deterministic per PIN so demos are repeatable. Fibre reaches more PINs in tier-1 cities;
5G AirFiber (FWA) is available everywhere the catalogue sells it.
"""
from __future__ import annotations

import hashlib
import re

FIBRE_SHARE = {1: 85, 2: 65}


def check(pin: str, city_tier: int | None = None) -> dict:
    pin = re.sub(r"\D", "", pin or "")
    if len(pin) != 6 or pin[0] == "0":
        return {"pin": pin, "valid": False}
    tier = city_tier if city_tier in FIBRE_SHARE else 2
    bucket = int(hashlib.sha256(pin.encode()).hexdigest(), 16) % 100
    fibre = bucket < FIBRE_SHARE[tier]
    return {
        "pin": pin, "valid": True, "fibre": fibre, "airfiber_5g": True,
        "fibre_install_days": 5 if fibre else None, "airfiber_install_days": 2,
        "message": ("Fibre is available at your address." if fibre else
                    "Fibre hasn't reached this PIN yet, so we've switched you to 5G AirFiber: same plan style, installed in about 2 days."),
    }
