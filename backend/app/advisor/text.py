"""Advisor questions and canned replies (English + Hindi). Other languages go through the LLM."""

Q = {
    "en": {
        "greeting": "Namaste! I'm the Accel Business advisor. In about 2 minutes I'll suggest the right internet, "
                    "SIM and digital tools for your business, with one clear monthly price. What kind of business do you run?",
        "business_type": "What kind of business do you run?",
        "business_type_retry": "Sorry, I didn't catch that. Is it a shop, a clinic or office, a chain of outlets, or a factory/unit?",
        "city": "Which city is your business in?",
        "employees": "How many people work in your business, including you?",
        "sites": "How many shops, branches or locations do you have?",
        "current_internet": "What do you use for internet today?",
        "monthly_spend": "Roughly how much do you spend each month on phone and internet together? (Optional: this lets me compare.)",
        "has_gstin": "Does your business have a GSTIN? If yes, you can type it and I'll fill in your details automatically.",
        "needs": "What would help your business most? Pick all that apply, then tap Done.",
        "gstin_found": "Found it: {name}, {state}. GST status: {status}.",
        "gstin_inactive": "Note: this GSTIN is {status} in the GST registry. I'll only suggest products that don't need GST, "
                          "and you can update your GST registration later.",
        "gstin_bad": "That GSTIN doesn't look right (it fails the check-digit test). Could you check it? You can also say \"skip\".",
        "recommend_intro": "Here is what I recommend for your {business} in {city}.",
        "recommend_price": "{tier}: ₹{monthly:,}/month all-inclusive (incl. GST), ready in about {days} days.",
        "compare_save": "That's about ₹{diff:,} less than the ₹{spend:,} you pay today.",
        "compare_more": "That's ₹{diff:,} more than today's ₹{spend:,}, but it covers {count} services on one bill.",
        "next_steps": "You can change add-ons on the next screen, or ask me anything.",
        "handoff": "Sure. A specialist will call you within 2 working hours. Your answers are saved, so you won't need to repeat anything.",
        "handoff_offer": "Businesses with {sites} sites usually like a quick site survey. Would you like a specialist visit? "
                         "You can also continue online.",
        "fallback": "I can help you pick internet, SIMs, billing, CCTV, cloud email and more. Could you tell me a bit more?",
        "question_fallback": "{answer}",
        "done": "Done",
        "skip": "Skip",
        "talk_to_expert": "Talk to an expert",
        "see_quote": "See price & checkout",
    },
    "hi": {
        "greeting": "नमस्ते! मैं Accel Business सलाहकार हूँ। लगभग 2 मिनट में मैं आपके बिज़नेस के लिए सही इंटरनेट, सिम और "
                    "डिजिटल टूल सुझाऊँगा, एक साफ़ मासिक कीमत के साथ। आपका बिज़नेस क्या है?",
        "business_type": "आपका बिज़नेस क्या है?",
        "business_type_retry": "माफ़ कीजिए, समझ नहीं पाया। क्या यह दुकान है, क्लिनिक/ऑफ़िस है, कई आउटलेट हैं, या फ़ैक्ट्री/यूनिट है?",
        "city": "आपका बिज़नेस किस शहर में है?",
        "employees": "आपके बिज़नेस में आपको मिलाकर कितने लोग काम करते हैं?",
        "sites": "आपकी कितनी दुकानें, ब्रांच या लोकेशन हैं?",
        "current_internet": "अभी आप इंटरनेट के लिए क्या इस्तेमाल करते हैं?",
        "monthly_spend": "फ़ोन और इंटरनेट पर हर महीने लगभग कितना ख़र्च होता है? (ज़रूरी नहीं, पर इससे तुलना कर पाऊँगा।)",
        "has_gstin": "क्या आपके बिज़नेस का GSTIN है? हाँ तो नंबर लिख दीजिए, मैं आपकी जानकारी अपने-आप भर दूँगा।",
        "needs": "आपके बिज़नेस को सबसे ज़्यादा किस चीज़ से मदद मिलेगी? जितने चाहें चुनें, फिर 'हो गया' दबाएँ।",
        "gstin_found": "मिल गया: {name}, {state}। GST स्टेटस: {status}।",
        "gstin_inactive": "ध्यान दें: GST रजिस्ट्री में यह GSTIN {status} है। मैं सिर्फ़ वही प्रोडक्ट सुझाऊँगा जिनके लिए GST ज़रूरी नहीं, "
                          "और आप बाद में GST अपडेट कर सकते हैं।",
        "gstin_bad": "यह GSTIN सही नहीं लग रहा (चेक-डिजिट मेल नहीं खाता)। कृपया एक बार जाँच लें, या \"skip\" लिखें।",
        "recommend_intro": "{city} में आपके {business} के लिए मेरा सुझाव यह है।",
        "recommend_price": "{tier}: ₹{monthly:,}/महीना सब कुछ मिलाकर (GST सहित), लगभग {days} दिन में चालू।",
        "compare_save": "यह आपके अभी के ₹{spend:,} से लगभग ₹{diff:,} कम है।",
        "compare_more": "यह अभी के ₹{spend:,} से ₹{diff:,} ज़्यादा है, लेकिन इसमें {count} सेवाएँ एक ही बिल में हैं।",
        "next_steps": "अगली स्क्रीन पर आप ऐड-ऑन बदल सकते हैं, या मुझसे कुछ भी पूछ सकते हैं।",
        "handoff": "ज़रूर। एक विशेषज्ञ 2 कामकाजी घंटों में आपको कॉल करेंगे। आपके जवाब सेव हैं, कुछ दोहराना नहीं पड़ेगा।",
        "handoff_offer": "{sites} लोकेशन वाले बिज़नेस अक्सर साइट सर्वे पसंद करते हैं। क्या आप विशेषज्ञ की विज़िट चाहेंगे? "
                         "आप ऑनलाइन भी आगे बढ़ सकते हैं।",
        "fallback": "मैं इंटरनेट, सिम, बिलिंग, CCTV, क्लाउड ईमेल वगैरह चुनने में मदद कर सकता हूँ। थोड़ा और बताइए?",
        "question_fallback": "{answer}",
        "done": "हो गया",
        "skip": "छोड़ें",
        "talk_to_expert": "विशेषज्ञ से बात करें",
        "see_quote": "कीमत देखें और आगे बढ़ें",
    },
}

CHIPS = {
    "business_type": {
        "en": ["Kirana / retail shop", "Clinic", "CA / law office", "Coaching centre", "Salon", "Restaurant",
               "Retail chain (3+ stores)", "Factory / manufacturing unit"],
        "hi": ["किराना / दुकान", "क्लिनिक", "CA / वकील ऑफ़िस", "कोचिंग सेंटर", "सैलून", "रेस्टोरेंट",
               "रिटेल चेन (3+ दुकानें)", "फ़ैक्ट्री / यूनिट"],
    },
    "city": {"en": ["Delhi", "Mumbai", "Bengaluru", "Pune", "Jaipur", "Indore", "Lucknow", "Kochi"]},
    "employees": {"en": ["1-2", "3-9", "10-24", "25-50", "50+"]},
    "sites": {"en": ["1", "2", "3-5", "6-10", "10+"]},
    "current_internet": {
        "en": ["Mobile hotspot", "Home broadband", "Business broadband", "Leased line", "No internet"],
        "hi": ["मोबाइल हॉटस्पॉट", "घर का ब्रॉडबैंड", "बिज़नेस ब्रॉडबैंड", "लीज़्ड लाइन", "इंटरनेट नहीं"],
    },
    "monthly_spend": {"en": ["₹1,000", "₹3,000", "₹6,000", "₹10,000", "₹25,000+"]},
    "has_gstin": {"en": ["Yes", "No"], "hi": ["हाँ", "नहीं"]},
}

# Chip label -> structured payload (so taps never depend on text understanding)
CHIP_PAYLOAD = {
    "business_type": ["Kirana store", "Dental clinic", "CA firm", "Coaching centre", "Salon", "Restaurant chain",
                      "Apparel retail chain", "Auto-parts unit"],
    "employees": [2, 5, 15, 35, 60],
    "sites": [1, 2, 4, 8, 12],
    "current_internet": ["Mobile hotspot", "Home broadband", "Business broadband", "Leased line", "None"],
    "monthly_spend": [1000, 3000, 6000, 10000, 25000],
    "has_gstin": [True, False],
}

NEED_LABELS = {
    "en": {
        "internet": "Fast, reliable internet", "backup_internet": "Internet that never goes down",
        "mobile_lines": "Business SIMs", "payments": "Billing & UPI/card payments", "messaging": "WhatsApp/SMS to customers",
        "email": "Business email & documents", "backup": "Data backup", "security": "Virus & cyber protection",
        "cctv": "CCTV cameras", "wifi": "Wi-Fi for customers", "website": "A website", "telephony": "Office phone lines / IVR",
        "toll_free": "Toll-free number", "static_ip": "Static IP", "multi_site_mgmt": "Manage all branches centrally",
        "iot": "Machine monitoring", "fleet": "Vehicle tracking", "dedicated_line": "Dedicated leased line",
    },
    "hi": {
        "internet": "तेज़, भरोसेमंद इंटरनेट", "backup_internet": "कभी न रुकने वाला इंटरनेट",
        "mobile_lines": "बिज़नेस सिम", "payments": "बिलिंग और UPI/कार्ड पेमेंट", "messaging": "ग्राहकों को WhatsApp/SMS",
        "email": "बिज़नेस ईमेल और डॉक्यूमेंट", "backup": "डेटा बैकअप", "security": "वायरस और साइबर सुरक्षा",
        "cctv": "CCTV कैमरे", "wifi": "ग्राहकों के लिए Wi-Fi", "website": "वेबसाइट", "telephony": "ऑफ़िस फ़ोन लाइन / IVR",
        "toll_free": "टोल-फ़्री नंबर", "static_ip": "स्टैटिक IP", "multi_site_mgmt": "सभी ब्रांच एक जगह से मैनेज",
        "iot": "मशीन मॉनिटरिंग", "fleet": "गाड़ियों की ट्रैकिंग", "dedicated_line": "डेडिकेटेड लीज़्ड लाइन",
    },
}

# Which needs to offer as chips, by segment (most relevant first)
NEED_CHIPS = {
    "micro": ["internet", "payments", "messaging", "mobile_lines", "cctv", "wifi", "website", "security"],
    "prof": ["internet", "email", "backup", "security", "telephony", "mobile_lines", "messaging", "backup_internet", "website", "static_ip"],
    "multi": ["internet", "backup_internet", "payments", "cctv", "multi_site_mgmt", "mobile_lines", "wifi", "security", "messaging", "fleet"],
    "mfg": ["dedicated_line", "internet", "iot", "security", "mobile_lines", "cctv", "backup", "fleet", "backup_internet"],
}
