"""Plain-language strings in English and Hindi.

These templates are the deterministic baseline: the app is fully usable without an LLM.
When an LLM is configured it may rephrase or translate them into other Indian languages,
but it is always given these facts, never asked to invent them.
"""
from __future__ import annotations

from .data import catalogue

LANGS = {
    "en": "English", "hi": "हिन्दी", "mr": "मराठी", "ta": "தமிழ்", "te": "తెలుగు",
    "kn": "ಕನ್ನಡ", "bn": "বাংলা", "gu": "ગુજરાતી", "ml": "മലയാളം", "pa": "ਪੰਜਾਬੀ",
}
TEMPLATE_LANGS = ("en", "hi")

REASONS = {
    "en": {
        "internet_micro": "Reliable broadband so UPI payments, card machines and your WhatsApp catalogue never stall.",
        "internet_prof": "Fast, stable internet for appointment software, video calls and cloud files.",
        "internet_multi": "One broadband connection at each of your {sites} sites, all on a single bill.",
        "internet_mfg": "Dedicated bandwidth for ERP, machine data and supplier systems.",
        "dependency": "Needed to run the other services in your bundle.",
        "mobile_lines": "Business SIMs for you and your staff, billed together with everything else.",
        "payments": "Billing, stock and UPI/card acceptance on a tablet, GST-ready invoices.",
        "messaging": "Reach customers on WhatsApp/SMS with offers, reminders and order updates.",
        "email": "Professional email on your own domain, shared documents and video meetings.",
        "backup": "Automatic backup so patient, client or billing records are never lost.",
        "security": "Protects your computers and phones from viruses and ransomware.",
        "firewall": "A managed firewall that blocks attacks before they reach your network.",
        "cctv": "Cameras with 30-day cloud recording you can view on your phone.",
        "wifi": "Separate, safe Wi-Fi for customers so your business network stays private.",
        "website": "A simple website with your own domain so customers can find you online.",
        "telephony": "Business phone lines with IVR and call recording, over your internet.",
        "toll_free": "A 1800 number customers can call free of charge.",
        "static_ip": "A fixed IP so cameras, servers or remote access work reliably.",
        "multi_site_mgmt": "Manage the internet at all sites from one place and prioritise billing apps.",
        "iot": "Track machine uptime and energy use live from your phone.",
        "fleet": "Live GPS tracking of your vehicles.",
        "backup_internet": "Automatic switch to 4G/5G when the main line goes down, so billing never stops.",
        "addon": "Popular with businesses like yours.",
    },
    "hi": {
        "internet_micro": "भरोसेमंद ब्रॉडबैंड, ताकि UPI पेमेंट, कार्ड मशीन और WhatsApp कैटलॉग कभी न रुकें।",
        "internet_prof": "अपॉइंटमेंट सॉफ़्टवेयर, वीडियो कॉल और क्लाउड फ़ाइलों के लिए तेज़ और स्थिर इंटरनेट।",
        "internet_multi": "आपकी सभी {sites} जगहों पर ब्रॉडबैंड, एक ही बिल में।",
        "internet_mfg": "ERP, मशीन डेटा और सप्लायर सिस्टम के लिए डेडिकेटेड बैंडविड्थ।",
        "dependency": "आपके बंडल की बाकी सेवाएँ चलाने के लिए ज़रूरी।",
        "mobile_lines": "आपके और स्टाफ़ के लिए बिज़नेस सिम, बाकी सब के साथ एक बिल में।",
        "payments": "टैबलेट पर बिलिंग, स्टॉक और UPI/कार्ड पेमेंट, GST-रेडी इनवॉइस।",
        "messaging": "WhatsApp/SMS से ग्राहकों को ऑफ़र, रिमाइंडर और ऑर्डर अपडेट भेजें।",
        "email": "अपने डोमेन पर प्रोफ़ेशनल ईमेल, शेयर्ड डॉक्यूमेंट और वीडियो मीटिंग।",
        "backup": "ऑटोमैटिक बैकअप, ताकि मरीज़, क्लाइंट या बिलिंग रिकॉर्ड कभी न खोएँ।",
        "security": "आपके कंप्यूटर और फ़ोन को वायरस और रैनसमवेयर से बचाता है।",
        "firewall": "मैनेज्ड फ़ायरवॉल जो हमलों को नेटवर्क तक पहुँचने से पहले रोकता है।",
        "cctv": "30 दिन की क्लाउड रिकॉर्डिंग वाले कैमरे, जिन्हें आप फ़ोन पर देख सकते हैं।",
        "wifi": "ग्राहकों के लिए अलग, सुरक्षित Wi-Fi, ताकि आपका बिज़नेस नेटवर्क निजी रहे।",
        "website": "आपके अपने डोमेन के साथ एक आसान वेबसाइट, ताकि ग्राहक आपको ऑनलाइन ढूँढ सकें।",
        "telephony": "IVR और कॉल रिकॉर्डिंग वाली बिज़नेस फ़ोन लाइनें, इंटरनेट पर।",
        "toll_free": "1800 नंबर, जिस पर ग्राहक मुफ़्त में कॉल कर सकें।",
        "static_ip": "फ़िक्स्ड IP, ताकि कैमरे, सर्वर या रिमोट एक्सेस ठीक से चलें।",
        "multi_site_mgmt": "सभी जगहों का इंटरनेट एक जगह से मैनेज करें और बिलिंग ऐप को प्राथमिकता दें।",
        "iot": "मशीनों का अपटाइम और बिजली खपत फ़ोन पर लाइव देखें।",
        "fleet": "आपकी गाड़ियों की लाइव GPS ट्रैकिंग।",
        "backup_internet": "मेन लाइन बंद होने पर अपने-आप 4G/5G पर स्विच, ताकि बिलिंग कभी न रुके।",
        "addon": "आपके जैसे बिज़नेस में लोकप्रिय।",
    },
}

BLOCKS = {
    "en": {
        "city_tier": "it is only available in Tier-{tiers} cities",
        "min_employees": "it needs at least {min} employees (you have {have})",
        "min_sites": "it needs at least {min} sites (you have {have})",
        "needs_gstin": "it needs a valid GSTIN",
        "gstin_inactive": "your GSTIN is {status} in the GST registry",
        "needs_one_of": "it needs a broadband or leased line in the same bundle",
    },
    "hi": {
        "city_tier": "यह सिर्फ़ टियर-{tiers} शहरों में उपलब्ध है",
        "min_employees": "इसके लिए कम से कम {min} कर्मचारी चाहिए (आपके पास {have} हैं)",
        "min_sites": "इसके लिए कम से कम {min} जगहें चाहिए (आपके पास {have} हैं)",
        "needs_gstin": "इसके लिए वैध GSTIN चाहिए",
        "gstin_inactive": "GST रजिस्ट्री में आपका GSTIN {status} है",
        "needs_one_of": "इसके लिए उसी बंडल में ब्रॉडबैंड या लीज़्ड लाइन चाहिए",
    },
}

NOTES = {
    "en": {
        "swapped": "We chose {product} instead of {instead}, because {why}.",
        "excluded": "We left out {product}, because {why}.",
        "added_dependency": "We added {product} because {instead} needs an internet connection.",
    },
    "hi": {
        "swapped": "हमने {instead} की जगह {product} चुना, क्योंकि {why}।",
        "excluded": "हमने {product} शामिल नहीं किया, क्योंकि {why}।",
        "added_dependency": "हमने {product} जोड़ा, क्योंकि {instead} को इंटरनेट कनेक्शन चाहिए।",
    },
}

TIER_NAMES = {
    "en": {"essential": "Essential", "recommended": "Recommended", "pro": "Pro"},
    "hi": {"essential": "ज़रूरी", "recommended": "सुझाया गया", "pro": "प्रो"},
}


def _lang(lang: str) -> str:
    return lang if lang in TEMPLATE_LANGS else "en"


def reason_text(code: str, lang: str = "en", **kw) -> str:
    t = REASONS[_lang(lang)].get(code) or REASONS["en"].get(code, "")
    try:
        return t.format(**kw)
    except KeyError:
        return t


def block_text(block: dict, lang: str = "en") -> str:
    t = BLOCKS[_lang(lang)].get(block.get("code"), block.get("code", ""))
    kw = dict(block)
    if isinstance(kw.get("tiers"), list):
        kw["tiers"] = "/".join(str(x) for x in kw["tiers"])
    try:
        return t.format(**kw)
    except KeyError:
        return t


def note_text(note: dict, lang: str = "en") -> str:
    cat = catalogue()
    name = lambda pid: cat[pid].name if pid in cat else (pid or "")
    why = "; ".join(block_text(b, lang) for b in note.get("blocks", [])) or ""
    t = NOTES[_lang(lang)].get(note["code"], "")
    return t.format(product=name(note.get("product_id")), instead=name(note.get("instead_of")), why=why)
