"""Builds Kernel_TIET.pptx on the official SYNC template (see deck/STORYBOARD.md).

Run from the repo root:  python deck/build_deck.py
Numbers come from the prototype (/api/backoffice/insights, /api/impact, the rules engine).
"""
from __future__ import annotations

from pathlib import Path

from lxml import etree
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "Submission Template_Sync.pptx"
ASSETS = ROOT / "deck" / "assets"
OUT = ROOT / "Kernel_TIET.pptx"

CHAR, CREAM, SAND, SAFF, DEEP, MUTED, GREEN, WHITE = (
    "1F1D1A", "F6F1E7", "EDE6D6", "F29A4A", "C2410C", "6B655B", "2F6B3F", "FFFFFF")
HEAD, BODY = "Georgia", "Segoe UI"


def rgb(h: str) -> RGBColor:
    return RGBColor.from_string(h)


class Slide:
    """Thin helper: every shape added is registered in an animation group."""

    def __init__(self, slide):
        self.s = slide
        self.anim: list[tuple[int, object]] = []

    def box(self, x, y, w, h, fill=CREAM, line=None, radius=0.08, group=1, shape=MSO_SHAPE.ROUNDED_RECTANGLE):
        sh = self.s.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
        if shape == MSO_SHAPE.ROUNDED_RECTANGLE:
            sh.adjustments[0] = min(radius / min(w, h), 0.5)
        sh.fill.solid()
        sh.fill.fore_color.rgb = rgb(fill)
        if line:
            sh.line.color.rgb = rgb(line)
            sh.line.width = Pt(0.75)
        else:
            sh.line.fill.background()
        sh.shadow.inherit = False
        sh.text_frame.text = ""
        self.anim.append((group, sh))
        return sh

    def text(self, x, y, w, h, paras, size=11, color=CHAR, font=BODY, bold=False, align=PP_ALIGN.LEFT,
             anchor=MSO_ANCHOR.TOP, group=1, spacing=None, italic=False):
        """paras: str | list of (str | list of run dicts)."""
        tb = self.s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        tf.vertical_anchor = anchor
        if isinstance(paras, str):
            paras = [paras]
        for i, para in enumerate(paras):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.alignment = align
            if spacing:
                p.space_after = Pt(spacing)
            runs = para if isinstance(para, list) else [{"t": para}]
            for r in runs:
                run = p.add_run()
                run.text = r["t"]
                f = run.font
                f.name = r.get("font", font)
                f.size = Pt(r.get("size", size))
                f.bold = r.get("bold", bold)
                f.italic = r.get("italic", italic)
                f.color.rgb = rgb(r.get("color", color))
        self.anim.append((group, tb))
        return tb

    def title(self, text, group=0):
        return self.text(0.45, 0.80, 9.1, 0.5, text, size=20, font=HEAD, group=group, anchor=MSO_ANCHOR.MIDDLE)

    def image(self, path, x, y, h=None, w=None, group=1):
        pic = self.s.shapes.add_picture(str(path), Inches(x), Inches(y), height=Inches(h) if h else None,
                                        width=Inches(w) if w else None)
        self.anim.append((group, pic))
        return pic

    def arrow(self, x1, y1, x2, y2, group=1, color=MUTED):
        c = self.s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
        c.line.color.rgb = rgb(color)
        c.line.width = Pt(1.25)
        ln = c.line._get_or_add_ln()
        tail = etree.SubElement(ln, qn("a:tailEnd"))
        tail.set("type", "triangle")
        self.anim.append((group, c))
        return c


# ---------------------------------------------------------------- motion

def add_motion(slide: Slide, stagger_ms: int = 120):
    """Fade transition + auto-playing staggered fade-in by group (no clicks needed)."""
    sld = slide.s._element
    groups: dict[int, list[int]] = {}
    for g, sh in slide.anim:
        groups.setdefault(g, []).append(sh.shape_id)
    P = "http://schemas.openxmlformats.org/presentationml/2006/main"
    ids = iter(range(3, 10_000))
    effects = []
    t = 0
    for g in sorted(groups):
        for spid in groups[g]:
            a, b, c = next(ids), next(ids), next(ids)
            effects.append(f'''
<p:par><p:cTn id="{a}" presetID="10" presetClass="entr" presetSubtype="0" fill="hold" nodeType="withEffect">
 <p:stCondLst><p:cond delay="{t}"/></p:stCondLst><p:childTnLst>
  <p:set><p:cBhvr><p:cTn id="{b}" dur="1" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst></p:cTn>
   <p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl><p:attrNameLst><p:attrName>style.visibility</p:attrName></p:attrNameLst></p:cBhvr>
   <p:to><p:strVal val="visible"/></p:to></p:set>
  <p:animEffect transition="in" filter="fade"><p:cBhvr><p:cTn id="{c}" dur="400"/><p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl></p:cBhvr></p:animEffect>
 </p:childTnLst></p:cTn></p:par>''')
        t += stagger_ms
    inner = next(ids)
    xml = f'''<p:timing xmlns:p="{P}"><p:tnLst><p:par><p:cTn id="1" dur="indefinite" restart="never" nodeType="tmRoot"><p:childTnLst>
<p:seq concurrent="1" nextAc="seek"><p:cTn id="2" dur="indefinite" nodeType="mainSeq"><p:childTnLst>
 <p:par><p:cTn id="{inner}" fill="hold"><p:stCondLst><p:cond delay="indefinite"/><p:cond evt="onBegin" delay="0"><p:tn val="2"/></p:cond></p:stCondLst><p:childTnLst>
  <p:par><p:cTn id="{inner + 5000}" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst><p:childTnLst>{''.join(effects)}
  </p:childTnLst></p:cTn></p:par>
 </p:childTnLst></p:cTn></p:par>
</p:childTnLst></p:cTn>
<p:prevCondLst><p:cond evt="onPrev" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:prevCondLst>
<p:nextCondLst><p:cond evt="onNext" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:nextCondLst></p:seq>
</p:childTnLst></p:cTn></p:par></p:tnLst></p:timing>'''
    for old in sld.findall(qn("p:timing")) + sld.findall(qn("p:transition")):
        sld.remove(old)
    trans = etree.fromstring(f'<p:transition xmlns:p="{P}" spd="med"><p:fade/></p:transition>')
    clr = sld.find(qn("p:clrMapOvr"))
    idx = list(sld).index(clr) + 1 if clr is not None else len(sld)
    sld.insert(idx, trans)
    sld.insert(idx + 1, etree.fromstring(xml))


# ---------------------------------------------------------------- slides

def new_content_slide(prs, bg_path):
    layout = prs.slides[1].slide_layout
    s = prs.slides.add_slide(layout)
    for ph in list(s.placeholders):
        ph._element.getparent().remove(ph._element)
    pic = s.shapes.add_picture(str(bg_path), 0, 0, prs.slide_width, prs.slide_height)
    tree = s.shapes._spTree
    tree.remove(pic._element)
    tree.insert(2, pic._element)
    return Slide(s)


def cover(prs):
    s = Slide(prs.slides[0])
    s.text(0.45, 2.66, 4.2, 0.22, "AIRTEL SYNC 2026  ·  TRACK A  ·  PROJECT UDYAM DIGITAL",
           size=8.5, color="E9DFCF", bold=True, group=0)
    s.text(0.45, 2.92, 4.0, 1.15, [[{"t": "Your business online, "},
                                     {"t": "in one sitting.", "italic": True, "color": SAFF}]],
           size=30, font=HEAD, color=WHITE, group=1)
    s.text(0.45, 4.06, 4.0, 0.5, "A phone-first advisor, one transparent price, 30-second KYC and a live "
                                  "tracker for India's MSMEs, in their own language.", size=10, color="E9DFCF", group=2)
    s.text(0.45, 4.7, 3.9, 0.45, [[{"t": "Team Kernel", "bold": True, "color": WHITE, "size": 12}],
                                     "Thapar Institute of Engineering & Technology (TIET)"],
           size=9.5, color="E9DFCF", group=3)
    return s


def problem(prs, bg):
    s = new_content_slide(prs, bg)
    s.title([[{"t": "Only 7.4% activate: the funnel leaks "}, {"t": "at the quote", "italic": True, "color": DEEP},
              {"t": " and at the door"}]])
    # funnel
    stages = [("Leads", 5000, ""), ("Contacted", 3406, "68%"), ("Needs assessed", 1974, "58%"),
              ("Quote accepted", 861, "44%"), ("KYC complete", 588, "68%"), ("Activated", 368, "63%")]
    x0, y0, full = 1.55, 1.42, 2.55
    s.text(0.45, y0 - 0.02, 4.4, 0.2, "FUNNEL, APR–JUN 2026  ·  % OF PREVIOUS STAGE", size=8, color=MUTED, bold=True, group=1)
    for i, (name, n, pct) in enumerate(stages):
        y = y0 + 0.24 + i * 0.29
        hi = name == "Quote accepted"
        s.text(0.45, y, 1.05, 0.26, name, size=9.5, bold=hi, color=CHAR, align=PP_ALIGN.RIGHT, anchor=MSO_ANCHOR.MIDDLE, group=2)
        w = max(full * n / 5000, 0.06)
        s.box(x0, y + 0.03, w, 0.2, fill=SAFF if hi else SAND, radius=0.03, group=2)
        s.text(x0 + w + 0.06, y, 0.9, 0.26, [[{"t": f"{n:,}", "bold": hi},
                                               {"t": f"  {pct}" if pct else "", "color": DEEP if hi else MUTED, "bold": hi}]],
               size=9.5, anchor=MSO_ANCHOR.MIDDLE, group=2)
    s.text(0.45, 3.52, 4.45, 0.55, [
        [{"t": "Quote-stage drops: ", "bold": True}, {"t": "price too high 414 · competitor cheaper 207 · too complex 206 · too slow 179."}],
        [{"t": "GSTIN matters: ", "bold": True}, {"t": "9.6% activate with one vs 2.0% without."}]],
        size=9, color=CHAR, group=3)
    # stat cards 2x2
    stats = [("17.6 days", "lead → activation; install alone takes 10–14 days", CHAR),
             ("₹20k vs ₹2.5k", "cost to win a micro shop vs its monthly bundle: field sales loses money", CHAR),
             ("6% → 28%", "6-month churn at 1 vs 5 “where is my order?” calls (3 on average)", CHAR),
             ("68 of 368", "past activations broke a catalogue or GST rule (22 on cancelled GSTINs)", DEEP)]
    for i, (big, small, col) in enumerate(stats):
        x = 5.1 + (i % 2) * 2.25
        y = 1.42 + (i // 2) * 1.27
        s.box(x, y, 2.15, 1.17, fill=CREAM, group=4 + i)
        s.text(x + 0.15, y + 0.12, 1.9, 0.42, big, size=21, font=HEAD, color=col, group=4 + i)
        s.text(x + 0.15, y + 0.57, 1.9, 0.55, small, size=9, color=MUTED, group=4 + i)
    # today's journey strip
    s.text(0.45, 4.12, 1.2, 0.2, "TODAY'S JOURNEY", size=8, color=MUTED, bold=True, group=8)
    steps = ["Rep visits, pitches this month's target", "3–5 days for a PDF of product codes",
             "KYC on paper or email", "10–14 day install, 3–4 chase calls", "Separate bills and helplines per product"]
    for i, st in enumerate(steps):
        x = 0.45 + i * 1.84
        s.box(x, 4.36, 1.74, 0.62, fill=WHITE, line=SAND, group=9)
        s.text(x + 0.1, 4.36, 1.56, 0.62, st, size=9, anchor=MSO_ANCHOR.MIDDLE, group=9)
        if i < 4:
            s.text(x + 1.74, 4.52, 0.1, 0.3, "›", size=11, color=MUTED, align=PP_ALIGN.CENTER, group=9)
    return s


def segments(prs, bg):
    s = new_content_slide(prs, bg)
    s.title([[{"t": "Lead with professional offices; serve micro shops "}, {"t": "without a visit", "italic": True, "color": DEEP}]])
    segs = [
        ("1 · BEACHHEAD", "Professional offices", "25% of base · clinics, CA firms", "11.1% conversion · ₹10.7k CAC",
         "100% self-serve", ["Biz Fibre 300", "Cloud Email ×5 + Backup 1 TB", "Endpoint Security ×5"], "₹4,712", "₹4,198 on 24 mo · ready in 5 days", True),
        ("2 · VOLUME", "Micro retail & services", "55% of base · kirana, salon", "4.1% conversion · ₹20.0k CAC",
         "Self-serve + partner assist", ["Biz Fibre 100 + Postpaid 299", "Cloud POS + WhatsApp Starter", "No GSTIN: Fibre 100 + POS, ₹2,476"], "₹4,440", "₹3,791 on 24 mo · ready in 5 days", False),
        ("3 · VALUE", "Small multi-site", "15% of base · 3–10 outlets", "11.0% conv. · ₹28k median bill",
         "Advisor → field sales", ["Per site: Fibre 300 + failover", "SD-WAN + CCTV + POS", "One bill for 4 outlets"], "₹34,904", "₹32,780 on 24 mo · 24-mo term", False),
        ("4 · ASSISTED", "Small manufacturers", "5% of base · auto-parts, textile", "12.8% conversion · 8.1% churn",
         "Advisor → field / partner", ["Leased Line 100", "Postpaid ×6 + Machine IoT ×5", "Endpoint Security"], "₹49,357", "₹48,384 on 24 mo · 24-mo term", False),
    ]
    for i, (eb, name, share, kpi, chan, items, price, sub, dark) in enumerate(segs):
        x = 0.45 + i * 2.32
        fg, mut = (CREAM, "D8CFBF") if dark else (CHAR, MUTED)
        g = 1 + i
        s.box(x, 1.36, 2.2, 2.86, fill=CHAR if dark else CREAM, group=g)
        s.text(x + 0.16, 1.45, 1.9, 0.2, eb, size=8, bold=True, color=SAFF if dark else DEEP, group=g)
        s.text(x + 0.16, 1.64, 1.95, 0.3, name, size=13.5, font=HEAD, color=fg, group=g)
        s.text(x + 0.16, 1.95, 1.95, 0.4, [share, [{"t": kpi, "bold": True}]], size=8.5, color=mut, group=g)
        s.text(x + 0.16, 2.36, 1.95, 0.22, [[{"t": "Channel: ", "bold": True}, {"t": chan}]], size=8.5, color=fg, group=g)
        s.text(x + 0.16, 2.6, 1.95, 0.62, items, size=8.5, color=fg, group=g)
        s.text(x + 0.16, 3.2, 1.95, 0.42, [[{"t": price, "size": 20, "font": HEAD}, {"t": " /mo incl. GST", "size": 8.5}]],
               color=SAFF if dark else CHAR, group=g)
        s.text(x + 0.16, 3.62, 1.95, 0.5, ["12-month price from the rules engine", sub], size=7.5, color=mut, group=g)
    # competitive analysis (C6, C8): why owners would switch
    s.text(0.45, 4.3, 9.1, 0.2, "VS. THE ALTERNATIVES AN OWNER HAS TODAY", size=8, bold=True, color=MUTED, group=6)
    comp = [("Local reseller", "Cheap, nearby; one product each, no single bill or support number"),
            ("Single-product digital sign-up", "Instant, but one product, no advice, no bundle or GST-aware KYC"),
            ("Accel field sales (today)", "Advice, but 17.6 days, ₹15k per activation, 3 chase calls"),
            ("Udyam Digital", "Advice + bundle + one bill, priced instantly on a phone, in 10 languages")]
    for i, (who, what) in enumerate(comp):
        x = 0.45 + i * 2.32
        us = who == "Udyam Digital"
        s.box(x, 4.52, 2.2, 0.56, fill="FBE7D3" if us else WHITE, line=None if us else SAND, group=7)
        s.text(x + 0.12, 4.55, 1.98, 0.52, [[{"t": who, "bold": True, "color": DEEP if us else CHAR}], what],
               size=7.5, color=CHAR, anchor=MSO_ANCHOR.MIDDLE, group=7)
    return s


def journey(prs, bg):
    s = new_content_slide(prs, bg)
    s.title([[{"t": "One sitting on a phone: "}, {"t": "advise, price, verify, track", "italic": True, "color": DEEP}]])
    shots = [("advisor.png", "01  Advise", "10 languages, voice and WhatsApp. Asks only what's missing (3 turns on average); the rules engine picks the bundle."),
             ("quote.png", "02  Price", "One GST-inclusive monthly price. Toggle add-ons and 12/24/36 months; re-priced live, re-validated on order."),
             ("consent.png", "03  Verify", "DPDP consent read aloud, then a receipt. GSTIN lookup, OCR, DigiLocker and e-Sign; 12 of 12 specimen verdicts right."),
             ("tracker.png", "04  Track", "Dated stages from install times, a self-booked slot and WhatsApp updates instead of chase calls. One bill after.")]
    for i, (img, head, fact) in enumerate(shots):
        cx = 0.45 + i * 2.3 + 1.1
        h = 2.95
        from PIL import Image
        iw, ih = Image.open(ASSETS / img).size
        w = h * iw / ih
        s.box(cx - w / 2 - 0.06, 1.36, w + 0.12, h + 0.12, fill=CHAR, radius=0.14, group=1 + i)
        s.image(ASSETS / img, cx - w / 2, 1.42, h=h, group=1 + i)
        s.text(cx - 1.08, 4.47, 2.16, 0.22, head, size=11, font=HEAD, bold=False, color=DEEP, group=1 + i)
        s.text(cx - 1.08, 4.68, 2.16, 0.45, fact, size=8, color=CHAR, group=1 + i)
    return s


def novelty(prs, bg):
    s = new_content_slide(prs, bg)
    s.title([[{"t": "The LLM talks, code decides, and the field gets "}, {"t": "a better brief", "italic": True, "color": DEEP}]])
    cards = [
        ("N1", "Fact guard", "Every LLM sentence is checked against the engine's output. An untraced ₹ amount, product or “discount” falls back to the template, so the 15 live judge scenarios can't see a made-up price.",
         "After MEGHA (Harvard AI for Good 2025, 1st) and Padhai Check (MumbaiHacks 2025): answers checked against a source of truth."),
        ("N2", "Data passbook", "Consent receipt with a SHA-256 of the exact notice, listen-aloud consent, and a log of every access to the owner's KYC data. Zero photos stored; one tap withdraws.",
         "After Sahamati's multilingual consent bot and Skippers (Gen AI Exchange 2025): privacy you can see."),
        ("N3", "Recovery playbook", "Each lost lead gets an engine-priced offer and a call brief in the owner's language: 36-month re-quote for price drops, DigiLocker for KYC drops, AirFiber where fibre can't reach.",
         "After DreamOps (Warpspeed 2025, grand prize) and PitchLense (Gen AI Exchange 2025): the agent prepares, a human closes."),
    ]
    for i, (tag, name, body, src) in enumerate(cards):
        x = 0.45 + i * 3.07
        g = 1 + i
        s.box(x, 1.38, 2.95, 2.2, fill=CREAM, group=g)
        s.text(x + 0.16, 1.48, 0.6, 0.36, tag, size=20, font=HEAD, color=SAFF, group=g)
        s.text(x + 0.72, 1.52, 2.1, 0.3, name, size=13, font=HEAD, color=CHAR, anchor=MSO_ANCHOR.MIDDLE, group=g)
        s.text(x + 0.16, 1.9, 2.65, 1.0, body, size=9.5, color=CHAR, group=g)
        s.text(x + 0.16, 2.95, 2.65, 0.55, src, size=7.5, italic=True, color=MUTED, group=g)
    # field force strip
    s.box(0.45, 3.72, 5.55, 1.33, fill=CHAR, group=4)
    s.text(0.62, 3.8, 5.2, 0.25, "FIELD FORCE AND PARTNERS: DIGITAL FEEDS THEM, NOT REPLACES THEM", size=8, bold=True, color=SAFF, group=4)
    s.text(0.62, 4.06, 5.25, 0.95, [
        [{"t": "Field sales: ", "bold": True}, {"t": "multi-site (6+ outlets) and manufacturers, with the advisor's profile and brief."}],
        [{"t": "Channel partners: ", "bold": True}, {"t": "micro shops via partner mode on the owner's phone; partner keeps credit."}],
        [{"t": "Telesales: ", "bold": True}, {"t": "everyone else, ranked by a propensity model (hold-out AUC 0.73)."}],
        [{"t": "Self-serve absorbs ~1,950 leads lost to unreachable numbers and unscheduled visits.", "color": "D8CFBF"}]],
        size=8.5, color=CREAM, spacing=1.5, group=4)
    s.box(6.12, 3.72, 3.43, 1.33, fill=WHITE, line=SAND, group=5)
    s.text(6.27, 3.8, 3.15, 0.25, "A REAL BRIEF FROM THE BACK-OFFICE", size=8, bold=True, color=DEEP, group=5)
    s.text(6.27, 4.05, 3.15, 0.95, [
        [{"t": "CA firm, Pune · saw offer, didn't buy · score 62", "bold": True}],
        "Re-quote on a 36-month contract: same bundle at ₹3,679/month incl. GST, ₹1,033 less than the 12-month quote.",
        [{"t": "Priced by the engine, so a rep can't promise a price the rules wouldn't give.", "color": MUTED, "italic": True}]],
        size=8.5, color=CHAR, spacing=2, group=5)
    return s


def architecture(prs, bg):
    s = new_content_slide(prs, bg)
    s.title([[{"t": "Architecture and privacy, "}, {"t": "by design", "italic": True, "color": DEEP}]])
    s.box(0.45, 1.36, 6.0, 0.34, fill=CHAR, radius=0.17, group=1)
    s.text(0.45, 1.36, 6.0, 0.34, [[{"t": "Principle: ", "bold": True, "color": SAFF}, {"t": "the LLM talks, deterministic code decides price, eligibility and KYC verdicts"}]],
           size=9, color=CREAM, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, group=1)
    cols = [
        (0.45, 1.55, "CHANNELS", ["Phone PWA (Next.js)", "WhatsApp Cloud API", "Partner mode", "Back-office"]),
        (2.32, 2.25, "FASTAPI CORE", ["Advisor dialogue + NLU", "N1 Fact guard", "Rules & pricing engine", "Smart KYC · DigiLocker · e-Sign", "Orders & tracker · coverage", "Propensity · N3 recovery · audit"]),
        (4.9, 1.55, "DATA & SERVICES", ["product_catalogue.csv", "smb_leads.csv", "GSTIN / Udyam registry (mock)", "LLM, optional (OpenAI-compatible)", "SQLite: fields only, masked log"]),
    ]
    for ci, (x, w, head, items) in enumerate(cols):
        g = 2 + ci
        s.text(x, 1.82, w, 0.2, head, size=8, bold=True, color=MUTED, group=g)
        n = len(items)
        gap = 0.07
        hh = (3.0 - gap * (n - 1)) / n
        for j, it in enumerate(items):
            y = 2.05 + j * (hh + gap)
            core = ci == 1 and it.startswith(("Rules", "N1"))
            s.box(x, y, w, hh, fill=SAFF if it.startswith("Rules") else (CREAM if not core else "FBE7D3"), group=g)
            s.text(x + 0.08, y, w - 0.16, hh, it, size=8.5, color=CHAR, bold=core, anchor=MSO_ANCHOR.MIDDLE, group=g)
    s.arrow(2.03, 3.55, 2.29, 3.55, group=3)
    s.arrow(4.6, 3.55, 4.87, 3.55, group=4)
    # privacy column
    s.box(6.65, 1.36, 2.9, 3.69, fill=CREAM, group=5)
    s.text(6.8, 1.46, 2.6, 0.3, "DPDP Act 2023, built in", size=13, font=HEAD, group=5)
    s.text(6.8, 1.82, 2.62, 3.15, [
        [{"t": "Consent you can prove: ", "bold": True}, {"t": "receipt with notice hash, purpose, retention date."}],
        [{"t": "Purpose-limited: ", "bold": True}, {"t": "KYC only; never shared with partners or used for marketing."}],
        [{"t": "Minimised: ", "bold": True}, {"t": "GSTIN pre-fill and DigiLocker; raw images never stored."}],
        [{"t": "Masked: ", "bold": True}, {"t": "GSTIN, Udyam and ID numbers in UI, API and logs."}],
        [{"t": "Transparent: ", "bold": True}, {"t": "owner sees every access; one tap withdraws and deletes."}],
        [{"t": "Accurate: ", "bold": True}, {"t": "checksum, registry status, cross-document and 90-day checks."}],
        [{"t": "AI-safe: ", "bold": True}, {"t": "the LLM never sets price or eligibility; the fact guard logs every blocked reply."}]],
        size=8.5, color=CHAR, spacing=4.5, group=5)
    return s


def business(prs, bg):
    s = new_content_slide(prs, bg)
    s.title([[{"t": "Conservatively, activations double and cost per activation "}, {"t": "falls 64%", "italic": True, "color": DEEP}]])
    rows = [("Metric", "Today", "Simulated*", "Target"),
            ("Lead → activation", "7.4%", "15.6%", "≥ 12%"),
            ("Cost per activation", "₹15,053", "₹5,499", "≤ ₹6,000"),
            ("Days to activate", "17.6", "8.6", "≤ 9"),
            ("Status chases / customer", "3.0", "2.0", "≤ 1"),
            ("6-month churn", "15.2%", "14.3%", "≤ 10%")]
    tbl = s.s.shapes.add_table(len(rows), 4, Inches(0.45), Inches(1.4), Inches(5.35), Inches(2.4)).table
    widths = [2.15, 1.0, 1.1, 1.1]
    for i, w in enumerate(widths):
        tbl.columns[i].width = Inches(w)
    for r, row in enumerate(rows):
        tbl.rows[r].height = Inches(0.4)
        for c, val in enumerate(row):
            cell = tbl.cell(r, c)
            cell.fill.solid()
            cell.fill.fore_color.rgb = rgb(CHAR if r == 0 else (CREAM if r % 2 else WHITE))
            cell.margin_left = cell.margin_right = Inches(0.1)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            tf = cell.text_frame
            tf.text = ""
            p = tf.paragraphs[0]
            p.alignment = PP_ALIGN.LEFT if c == 0 else PP_ALIGN.RIGHT
            run = p.add_run()
            run.text = val
            f = run.font
            f.name = HEAD if (r > 0 and c > 0) else BODY
            f.size = Pt(8.5 if r == 0 else (13 if c > 0 else 10))
            f.bold = r == 0 or c == 3
            f.color.rgb = rgb(CREAM if r == 0 else (GREEN if c == 2 else (DEEP if c == 3 else CHAR)))
    s.anim.append((1, tbl._graphic_frame))
    s.text(0.45, 3.9, 5.35, 0.5, "*Impact simulator, conservative preset: each fix recovers a share of the exact drop reasons in "
                                  "smb_leads.csv; recovered leads then convert at today's later-stage rates. Cohort ARR ₹18.5 cr → ₹39.6 cr per quarter of leads.",
           size=8, color=MUTED, group=2)
    s.box(0.45, 4.48, 5.35, 0.57, fill=CHAR, group=3)
    s.text(0.6, 4.48, 5.1, 0.57, [[{"t": "Ask: ", "bold": True, "color": SAFF},
                                   {"t": "a 3-month pilot with professional offices in Pune and Bengaluru, gated on ≥ 12% conversion and ≤ ₹6k CAC."}]],
           size=9.5, color=CREAM, anchor=MSO_ANCHOR.MIDDLE, group=3)
    # rollout + risks
    s.text(6.05, 1.38, 3.5, 0.3, "Rollout", size=13, font=HEAD, group=4)
    phases = [("0–3 mo", "Pilot: professional offices, 2 tier-1 cities, web + WhatsApp, real GSTN via a GSP, DigiLocker."),
              ("3–9 mo", "Scale: micro via 200 channel partners on partner mode; Hindi + 4 regional languages; UPI AutoPay."),
              ("6–12 mo", "Assist: multi-site and manufacturers; advisor qualifies, field closes with the brief.")]
    for i, (when, what) in enumerate(phases):
        y = 1.72 + i * 0.58
        s.text(6.05, y, 0.8, 0.5, when, size=10, font=HEAD, color=DEEP, group=5 + i)
        s.text(6.85, y, 2.7, 0.55, what, size=8.5, group=5 + i)
    s.text(6.05, 3.5, 3.5, 0.3, "Risks we designed for", size=13, font=HEAD, group=8)
    s.text(6.05, 3.82, 3.5, 1.25, [
        [{"t": "Wrong price live → ", "bold": True}, {"t": "engine decides; fact guard; 16 QA scenarios in CI."}],
        [{"t": "KYC fraud → ", "bold": True}, {"t": "DigiLocker first; checksum, registry status, cross-document checks."}],
        [{"t": "Channel conflict → ", "bold": True}, {"t": "partner attribution; human-only segments; briefs feed the field."}],
        [{"t": "No fibre → ", "bold": True}, {"t": "PIN check re-plans to 5G AirFiber (2-day install)."}]],
        size=8.5, spacing=2, group=8)
    return s


def main():
    prs = Presentation(str(TEMPLATE))
    bg = ROOT / "deck" / "build" / "tpl2.jpg"
    if not bg.exists():
        bg.parent.mkdir(parents=True, exist_ok=True)
        bg.write_bytes(prs.slides[1].shapes[0].image.blob)
    slides = [cover(prs)]
    slides += [problem(prs, bg), segments(prs, bg), journey(prs, bg), novelty(prs, bg), architecture(prs, bg), business(prs, bg)]
    # drop the template's empty slide 2 (its layout and background are reused by every content slide)
    sldIdLst = prs.slides._sldIdLst
    first_content = sldIdLst[1]
    rId = first_content.get(qn("r:id"))
    prs.part.drop_rel(rId)
    sldIdLst.remove(first_content)
    for s in slides:
        add_motion(s)
    notes = [
        "Cover. Team Kernel, TIET.",
        "Problem and data: C1–C8, D1–D4.",
        "Segments and bundles: Q1, D2, D3.",
        "Journey and prototype: Q2, Q3, B1–B4, S1.",
        "Novelty and field force: N1–N3, Q4, S2, S3, D5.",
        "Architecture and privacy: E2, E4.",
        "Business case and metrics: Q5, E3.",
    ]
    for s, n in zip(slides, notes):
        s.s.notes_slide.notes_text_frame.text = "Traces to docs/PROBLEMS.md: " + n
    prs.save(str(OUT))
    print("saved", OUT, len(prs.slides), "slides")


if __name__ == "__main__":
    main()
