"""Deterministic understanding of owner messages (English, Hindi, Hinglish).

This is the no-LLM baseline and also a safety net: whatever an LLM extracts is merged with
and validated against what these rules find.
"""
from __future__ import annotations

import re

from ..data import business_types, cities

# keyword -> canonical business type (from the leads data)
BUSINESS_KEYWORDS = [
    (r"kirana|grocery|general store|provision|किराना|परचून", "Kirana store"),
    (r"pharmacy chain|chemist chain|medical stores", "Pharmacy chain"),
    (r"pharmacy|chemist|medical store|दवा|फार्मेसी|मेडिकल", "Pharmacy"),
    (r"bakery chain", "Bakery chain"),
    (r"bakery|bake|बेकरी", "Bakery"),
    (r"sweet|mithai|halwai|मिठाई", "Sweet shop"),
    (r"salon|parlou?r|barber|सैलून|पार्लर", "Salon"),
    (r"optic|chashma|spectacle|चश्म", "Optician"),
    (r"stationery|स्टेशनरी", "Stationery shop"),
    (r"hardware|हार्डवेयर", "Hardware store"),
    (r"boutique|tailor|बुटीक|दर्ज़ी|दर्जी", "Boutique"),
    (r"mobile (repair|shop)|phone repair|मोबाइल (रिपेयर|शॉप|की दुकान)", "Mobile repair shop"),
    (r"dental|dentist|दांत|डेंटल", "Dental clinic"),
    (r"diagnostic|pathology|\blab\b|लैब", "Diagnostic lab"),
    (r"physio|फिजियो", "Physiotherapy clinic"),
    (r"clinic|doctor|hospital|क्लिनिक|डॉक्टर", "Dental clinic"),
    (r"real estate|property|प्रॉपर्टी", "Real estate agency"),
    (r"\blaw\b|lawyer|advocate|legal|वकील", "Law office"),
    (r"coaching|tuition|classes|institute|कोचिंग|ट्यूशन", "Coaching centre"),
    (r"\bca\b|chartered accountant|accountant|tax consult|सीए", "CA firm"),
    (r"architect|interior", "Architecture studio"),
    (r"travel|tour", "Travel agency"),
    (r"insurance|बीमा", "Insurance agency"),
    (r"restaurant|dhaba|cafe|café|hotel food|रेस्टोरेंट|ढाबा", "Restaurant chain"),
    (r"electronics|इलेक्ट्रॉनिक", "Electronics retail chain"),
    (r"apparel|clothing|garment|fashion|कपड़", "Apparel retail chain"),
    (r"pre-?school|play ?school|kindergarten", "Pre-school chain"),
    (r"hotel|lodge|guest ?house|होटल", "Budget hotel group"),
    (r"\bgym\b|fitness|जिम", "Gym chain"),
    (r"auto ?parts|automobile parts|spare parts", "Auto-parts unit"),
    (r"textile|weaving|power ?loom|कपड़ा मिल", "Textile unit"),
    (r"plastic|moulding|molding", "Plastic moulding unit"),
    (r"packaging|carton|पैकेजिंग", "Packaging unit"),
    (r"food processing|masala|pickle|snack factory", "Food processing unit"),
    (r"furniture|carpentry|wood|फर्नीचर", "Furniture workshop"),
    (r"print(ing)? press|printing|प्रिंटिंग", "Printing press"),
    (r"factory|manufactur|workshop|फैक्ट्री|कारखान", "Auto-parts unit"),
    (r"shop|store|dukaan|dukan|दुकान", "Kirana store"),
]

CITY_ALIASES = {
    "दिल्ली": "Delhi", "new delhi": "Delhi", "मुंबई": "Mumbai", "bombay": "Mumbai", "पुणे": "Pune", "poona": "Pune",
    "बेंगलुरु": "Bengaluru", "bangalore": "Bengaluru", "चेन्नई": "Chennai", "madras": "Chennai",
    "हैदराबाद": "Hyderabad", "कोलकाता": "Kolkata", "calcutta": "Kolkata", "अहमदाबाद": "Ahmedabad",
    "जयपुर": "Jaipur", "इंदौर": "Indore", "भोपाल": "Bhopal", "लखनऊ": "Lucknow", "पटना": "Patna",
    "नागपुर": "Nagpur", "नासिक": "Nashik", "सूरत": "Surat", "वडोदरा": "Vadodara", "baroda": "Vadodara",
    "लुधियाना": "Ludhiana", "कोच्चि": "Kochi", "cochin": "Kochi", "मैसूर": "Mysuru", "mysore": "Mysuru",
    "कोयंबटूर": "Coimbatore", "विशाखापत्तनम": "Visakhapatnam", "vizag": "Visakhapatnam",
}
# Tier-1 metros outside the dataset, so the advisor still knows they are tier 1.
EXTRA_TIER1 = {"gurgaon": ("Gurugram", "Haryana"), "gurugram": ("Gurugram", "Haryana"), "noida": ("Noida", "Uttar Pradesh"),
               "ghaziabad": ("Ghaziabad", "Uttar Pradesh"), "thane": ("Thane", "Maharashtra"), "navi mumbai": ("Navi Mumbai", "Maharashtra")}

NEED_KEYWORDS = [
    (r"backup internet|failover|internet (goes|jata) (down|band)|net (chala|chal) jata|outage|downtime", "backup_internet"),
    (r"leased line|dedicated|sla|लीज़्ड", "dedicated_line"),
    (r"\bsims?\b|mobile (line|connection|plan|number)|postpaid|सिम|मोबाइल कनेक्शन", "mobile_lines"),
    (r"\bpos\b|billing|upi|payment|card machine|invoice|बिलिंग|पेमेंट", "payments"),
    (r"whats ?app|\bsms\b|message customers|promotion|marketing|व्हाट्सएप|मैसेज", "messaging"),
    (r"e-?mail|gmail|office suite|documents|ईमेल", "email"),
    (r"backup|data loss|डेटा बैकअप", "backup"),
    (r"antivirus|virus|ransomware|cyber|security|hack|साइबर|वायरस", "security"),
    (r"cctv|camera|surveillance|कैमरा|सीसीटीवी", "cctv"),
    (r"wi-?fi|guest network|वाईफाई|वाई-फाई", "wifi"),
    (r"website|domain|online presence|वेबसाइट", "website"),
    (r"ivr|call recording|phone lines?|telephony|landline|reception calls", "telephony"),
    (r"toll ?free|1800", "toll_free"),
    (r"static ip|fixed ip|remote access", "static_ip"),
    (r"sd-?wan|central(ly)? manage|all (branches|sites|stores)", "multi_site_mgmt"),
    (r"machine|iot|sensor|energy monitor|मशीन", "iot"),
    (r"fleet|vehicle|truck|delivery van|gps|गाड़ी|गाडी", "fleet"),
    (r"internet|broadband|wifi connection|fiber|fibre|net connection|इंटरनेट|ब्रॉडबैंड", "internet"),
]

INTERNET_KEYWORDS = [
    (r"hotspot|mobile data|phone (ka )?(net|internet)|हॉटस्पॉट", "Mobile hotspot"),
    (r"leased line", "Leased line"),
    (r"home broadband|home wifi|ghar (ka|wala)", "Home broadband"),
    (r"business broadband|office broadband|broadband|fiber|fibre|ब्रॉडबैंड", "Business broadband"),
    (r"mixed|different (isps?|providers?)|alag alag", "Mixed per site"),
    (r"local isp|cable (net|internet)", "Business broadband"),
    (r"no internet|nothing|kuch nahi|कुछ नहीं|none", "None"),
]
PROVIDERS = [(r"\bjio\b", "Competitor A"), (r"\bvi\b|vodafone|idea", "Competitor B"), (r"bsnl|local isp|cable", "Local ISP"),
             (r"\baccel\b|airtel", "Accel")]

YES = r"^(yes|y|yeah|yup|haan|ha|han|ji|ji haan|hai|हाँ|हां|जी|है|sure|ok|okay)\b"
NO = r"^(no|n|nope|nahi|nahin|na|नहीं|नही|ना|none|don'?t have|nai)\b"

GSTIN_IN_TEXT = re.compile(r"\b(\d{2}[A-Z0-9]{10}[0-9A-Z]Z[0-9A-Z])\b", re.I)
UDYAM_IN_TEXT = re.compile(r"UDYAM-?[A-Z]{2}-?\d{2}-?\d{7}", re.I)
NUM = r"(\d{1,6}(?:,\d{3})*(?:\.\d+)?)\s*(k|हज़ार|hazar|hazaar|thousand)?"


def _num(m: re.Match) -> int:
    v = float(m.group(1).replace(",", ""))
    if m.group(2):
        v *= 1000
    return int(v)


def find_business_type(text: str) -> str | None:
    t = text.lower()
    for bt in business_types():  # exact names first
        if bt.lower() in t:
            return bt
    for pattern, bt in BUSINESS_KEYWORDS:
        if re.search(pattern, t):
            return bt
    return None


def find_city(text: str) -> tuple[str, int, str | None] | None:
    t = text.lower()
    for c, info in cities().items():
        if re.search(rf"\b{re.escape(c.lower())}\b", t):
            return c, info["tier"], info["state"]
    for alias, c in CITY_ALIASES.items():
        if alias in t:
            return c, cities()[c]["tier"], cities()[c]["state"]
    for alias, (c, state) in EXTRA_TIER1.items():
        if alias in t:
            return c, 1, state
    return None


def find_needs(text: str) -> list[str]:
    t = text.lower()
    return [need for pattern, need in NEED_KEYWORDS if re.search(pattern, t)]


def parse(text: str, expecting: str | None = None) -> dict:
    """Extract whatever facts the message contains. `expecting` = the slot we last asked about."""
    t = text.strip()
    low = t.lower()
    out: dict = {}

    bt = find_business_type(t)
    if bt:
        out["business_type"] = bt
    c = find_city(t)
    if c:
        out["city"], out["city_tier"], out["state"] = c

    g = GSTIN_IN_TEXT.search(t.upper())
    if g:
        out["has_gstin"], out["gstin"] = True, g.group(1).upper()
    elif re.search(r"(no|nahi|नहीं|without|don'?t have).{0,12}gst|gst.{0,12}(nahi|नहीं|no\b|not)", low):
        out["has_gstin"] = False
    elif re.search(r"(have|hai|है).{0,10}gst|gst.{0,10}(hai|है|registered|yes|haan|हाँ)", low):
        out["has_gstin"] = True
    if UDYAM_IN_TEXT.search(t.upper()):
        out["has_udyam"] = True

    m = re.search(NUM + r"\s*(employees|employee|staff|people|log|लोग|कर्मचारी|workers|members)", low)
    if m:
        out["employees"] = _num(m)
    m = re.search(NUM + r"\s*(shops|shop|branches|branch|outlets|outlet|stores|store|sites|site|locations|location|offices|office|centres|centre|clinics|factories|factory|units|unit|labs|lab|दुकानें|दुकान|ब्रांच)", low)
    if m:
        out["sites"] = _num(m)
    if "sites" not in out:
        # "3 bakeries", "3 बेकरी", "two clinics": a count right before a business noun is a site count
        for m in re.finditer(NUM + r"\s+([^\s,।]+(?:\s+[^\s,।]+)?)", low):
            noun = m.group(3)
            if any(re.search(p, noun) for p, _ in BUSINESS_KEYWORDS) and not re.search(r"staff|employee|people|log|लोग", noun):
                out["sites"] = _num(m)
                break
    m = re.search(r"(budget|बजट)\D{0,12}" + NUM, low)
    if m:
        out["budget"] = int(float(m.group(2).replace(",", "")) * (1000 if m.group(3) else 1))
    m = re.search(r"(₹|rs\.?|inr)\s*" + NUM + "|" + NUM + r"\s*(rupees|rs|₹|रुपये|रुपए)", low)
    if m:
        groups = [g for g in m.groups()]
        val = next((x for x in groups if x and re.match(r"^\d", x)), None)
        mult = 1000 if any(x in ("k", "हज़ार", "hazar", "hazaar", "thousand") for x in groups if x) else 1
        if val:
            amount = int(float(val.replace(",", "")) * mult)
            if expecting == "budget":
                out["budget"] = amount
            elif amount != out.get("budget"):
                out["monthly_spend"] = amount
    m = re.search(NUM + r"\s*(cameras|camera|कैमरे|कैमरा)", low)
    if m:
        out["cameras"] = _num(m)
    m = re.search(NUM + r"\s*(sims|sim|lines|connections|सिम)", low)
    if m:
        out["mobile_lines"] = _num(m)
    m = re.search(NUM + r"\s*(vehicles|trucks|vans|gaadi|गाड़ियाँ)", low)
    if m:
        out["vehicles"] = _num(m)
    m = re.search(NUM + r"\s*(machines|मशीन)", low)
    if m:
        out["machines"] = _num(m)

    for pattern, value in INTERNET_KEYWORDS:
        if re.search(pattern, low):
            out["current_internet"] = value
            break
    for pattern, value in PROVIDERS:
        if re.search(pattern, low):
            out["current_provider"] = value
            break
    if re.search(r"no fib(er|re)|fib(er|re) (not|nahi)|fibre unavailable", low):
        out["fibre_available"] = False
    if re.search(r"\b(only|just|sirf)\b.{0,20}\b(sims?|sim cards?|mobile (lines?|plans?|connections?))\b|सिर्फ़?\s.{0,12}(सिम|मोबाइल)", low):
        out["only_mobile"] = True
        out["needs"] = ["mobile_lines"]

    needs = find_needs(t)
    if needs and "needs" not in out:
        out["needs"] = needs

    # Bare answers to the last question ("5", "haan", "Pune")
    bare = re.fullmatch(r"\s*" + NUM + r"\s*\+?\s*", low)
    if bare and expecting in ("employees", "sites", "monthly_spend", "budget", "mobile_lines", "cameras"):
        out[expecting] = _num(bare)
    if expecting == "has_gstin" and "has_gstin" not in out:
        if re.match(YES, low):
            out["has_gstin"] = True
        elif re.match(NO, low):
            out["has_gstin"] = False
    if expecting == "current_internet" and re.match(NO, low):
        out["current_internet"] = "None"
    if (expecting == "city" and "city" not in out and re.fullmatch(r"[A-Za-zऀ-ॿ .'-]{2,40}", t)
            and not re.match(YES, low) and not re.match(NO, low)):
        out["city"], out["city_tier"] = t.title(), 2  # unknown smaller town -> tier-2 catalogue (conservative)
    if expecting == "business_type" and "business_type" not in out and len(t) < 60:
        out["business_type_raw"] = t
    return out


def is_question(text: str) -> bool:
    low = text.lower().strip()
    return low.endswith("?") or bool(re.match(r"^(what|why|how|which|can|does|is|kya|kaise|kyun|kitna|क्या|कैसे|क्यों|कितना)\b", low))


def wants_human(text: str) -> bool:
    return bool(re.search(r"(talk|speak|call).{0,15}(person|human|agent|executive|someone|expert)|call me|"
                          r"baat karni|call karo|executive|insaan|इंसान|कॉल करें|बात करनी", text.lower()))
