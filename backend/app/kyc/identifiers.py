"""GSTIN and Udyam number validation, OCR-error correction and masking."""
from __future__ import annotations

import re
from itertools import product as cartesian

ALNUM = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

GST_STATE_CODES = {
    "01": "Jammu and Kashmir", "02": "Himachal Pradesh", "03": "Punjab", "04": "Chandigarh",
    "05": "Uttarakhand", "06": "Haryana", "07": "Delhi", "08": "Rajasthan", "09": "Uttar Pradesh",
    "10": "Bihar", "11": "Sikkim", "12": "Arunachal Pradesh", "13": "Nagaland", "14": "Manipur",
    "15": "Mizoram", "16": "Tripura", "17": "Meghalaya", "18": "Assam", "19": "West Bengal",
    "20": "Jharkhand", "21": "Odisha", "22": "Chhattisgarh", "23": "Madhya Pradesh", "24": "Gujarat",
    "27": "Maharashtra", "29": "Karnataka", "30": "Goa", "32": "Kerala", "33": "Tamil Nadu",
    "34": "Puducherry", "36": "Telangana", "37": "Andhra Pradesh",
}
UDYAM_STATE_CODES = {
    "AP": "Andhra Pradesh", "BR": "Bihar", "DL": "Delhi", "GJ": "Gujarat", "KL": "Kerala",
    "KR": "Karnataka", "KA": "Karnataka", "MH": "Maharashtra", "MP": "Madhya Pradesh", "PB": "Punjab",
    "RJ": "Rajasthan", "TN": "Tamil Nadu", "TS": "Telangana", "UP": "Uttar Pradesh", "WB": "West Bengal",
}

# Structure: 2 digits state | 5 letters PAN | 4 digits PAN | 1 letter PAN | entity no. | 'Z' | checksum
_GST_SLOTS = ["d", "d"] + ["a"] * 5 + ["d"] * 4 + ["a", "x", "Z", "x"]
_TO_LETTER = {"0": "O", "1": "I", "2": "Z", "5": "S", "6": "G", "8": "B"}
_TO_DIGIT = {"O": "0", "Q": "0", "D": "0", "I": "1", "L": "1", "Z": "2", "S": "5", "G": "6", "B": "8"}
GSTIN_RE = re.compile(r"^\d{2}[A-Z]{5}\d{4}[A-Z][1-9A-Z]Z[0-9A-Z]$")


def gstin_checksum(first14: str) -> str:
    total = 0
    for i, ch in enumerate(first14):
        v = ALNUM.index(ch) * (2 if i % 2 else 1)
        total += v // 36 + v % 36
    return ALNUM[(36 - total % 36) % 36]


def _clean(s: str) -> str:
    return re.sub(r"[^0-9A-Za-z]", "", s or "").upper()


def validate_gstin(raw: str) -> dict:
    """Format + checksum check, repairing typical OCR confusions (O/0, I/1, S/5 ...) by position.

    A repair is only accepted if it makes the checksum valid, so a genuinely wrong GSTIN
    (e.g. one digit changed) is still rejected.
    """
    s = _clean(raw)
    out = {"input": raw, "gstin": s, "format_ok": False, "checksum_ok": False, "corrected": False, "state": None}
    if len(s) != 15:
        out["error"] = "length"
        return out

    options = []
    for ch, slot in zip(s, _GST_SLOTS):
        if slot == "d":
            options.append([_TO_DIGIT.get(ch, ch)])
        elif slot == "a":
            options.append([_TO_LETTER.get(ch, ch)])
        elif slot == "Z":
            options.append(["Z"] if ch in "Z2" else [ch])
        else:  # ambiguous alnum slots: try both readings
            alts = {ch, _TO_LETTER.get(ch, ch), _TO_DIGIT.get(ch, ch)}
            options.append(sorted(alts, key=lambda c: c != ch))

    fixed_format = None
    for combo in cartesian(*options):
        cand = "".join(combo)
        if not GSTIN_RE.match(cand):
            continue
        fixed_format = fixed_format or cand
        if gstin_checksum(cand[:14]) == cand[14]:
            out.update(gstin=cand, format_ok=True, checksum_ok=True, corrected=cand != s)
            break
    else:
        if fixed_format:
            out.update(gstin=fixed_format, format_ok=True, corrected=fixed_format != s, error="checksum")
        else:
            out["error"] = "format"
    if out["format_ok"]:
        out["state"] = GST_STATE_CODES.get(out["gstin"][:2])
        out["pan"] = out["gstin"][2:12]
    return out


UDYAM_RE = re.compile(r"^UDYAM-([A-Z]{2})-(\d{2})-(\d{7})$")


def validate_udyam(raw: str) -> dict:
    s = re.sub(r"\s+", "", (raw or "").upper())
    s = s.replace("UDYAM", "UDYAM-", 1).replace("--", "-") if not s.startswith("UDYAM-") else s
    m = UDYAM_RE.match(s)
    out = {"input": raw, "udyam_number": s, "format_ok": bool(m), "state": None}
    if m:
        out["state"] = UDYAM_STATE_CODES.get(m.group(1))
        out["district_code"] = m.group(2)
    else:
        out["error"] = "format" if s else "missing"
    return out


def mask_gstin(g: str | None) -> str:
    if not g or len(g) < 15:
        return g or ""
    return g[:2] + g[2:4] + "•" * 6 + g[10:]


def mask_udyam(u: str | None) -> str:
    if not u or len(u) < 10:
        return u or ""
    return u[:12] + "•" * 4 + u[-3:]


def mask_id(v: str | None) -> str:
    if not v:
        return ""
    return "•" * max(len(v) - 4, 0) + v[-4:]
