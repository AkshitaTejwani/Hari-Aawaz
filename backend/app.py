"""Hari Aawaz backend: multilingual RAG + Gemini, served by Flask.

Deployed on Hugging Face Spaces (Docker). Set GEMINI_API_KEY as a Space secret.
"""
import os
import json
import time
from datetime import datetime, timezone, timedelta

import chromadb
from chromadb.utils import embedding_functions
from flask import Flask, request, jsonify
from flask_cors import CORS
from google import genai
from google.genai import types

# ----------------------------------------------------------------------------
# 1. Verified knowledge base (9 entries, compiled from official Rajasthan pages)
# ----------------------------------------------------------------------------
documents = [
    "Issue: Garbage dumping and uncollected municipal solid waste (Keywords: kachra, kooda, solid waste, overflowing dustbin, street litter, safai, garbage pile). Authority: Nagar Nigam Jaipur (Jaipur Municipal Corporation) - Deputy Commissioner (Health) & Executive Engineer (Solid Waste Management). Submit via: JMC Call Centre / Public Grievance Helpline 0141-2747400 (08:00 AM to 10:00 PM, 7 days), 'Jaipur Samadhan' Android mobile app, or online at http://jaipurmc.org (About Us -> Online Services -> Register Your Complaint). Rule: Solid Waste Management Rules, 2026 & Rajasthan Municipalities Act, 2009 (Section 226). Escalate to: Commissioner JMC (0141-2740510, commissioner.jmc@rajasthan.gov.in) or JMC Control Room (0141-2742900). Source: http://jaipurmc.org/Presentation/PublicNotice/FAQs.aspx (Verified: 23-11-2026).",
    "Issue: Construction and demolition waste dumping or malba accumulation (Keywords: C&D waste, malba, construction debris, building waste, rubble, patthar, mitti). Authority: Rajasthan State Pollution Control Board (RSPCB). Submit via: Rajasthan Sampark Portal (https://sampark.rajasthan.gov.in) under Public Grievance with location, nature of pollution, and photos/videos. Rule: Construction and Demolition Waste Management Rules, 2016. Escalate to: Rajasthan Sampark Helpline 181 or Department of Public Grievances (0141-2922825, ds.rpg@rajasthan.gov.in). Source: https://environment.rajasthan.gov.in/content/environment/en/rajasthan-state-pollution-control-board/ComplaintPage.html (Verified: 23-11-2026).",
    "Issue: Waste and open garbage burning (Keywords: kachra jalana, kooda jalana, patte jalana, dry leaves burning, plastic burning, garbage burning, smoke, dhuan, aag lagana). Authority: Rajasthan State Pollution Control Board (RSPCB). Submit via: Rajasthan Sampark Portal (https://sampark.rajasthan.gov.in) under Public Grievance with location, nature of pollution, and photos/videos. Rule: Solid Waste Management Rules, 2026 (Rule 5(1)(f) - no burning of waste on streets or open public spaces; Rule 17 - Environmental Compensation, polluter pays principle) & Air (Prevention and Control of Pollution) Act, 1981. Escalate to: Rajasthan Sampark Toll-Free Helpline 181 (0141-2922272, 2921646) or Department of Public Grievances (ds.rpg@rajasthan.gov.in). Source: https://environment.rajasthan.gov.in/content/environment/en/rajasthan-state-pollution-control-board/ComplaintPage.html (Verified: 23-11-2026).",
    "Issue: Drinking water supply leakage, pipeline burst, or water wastage (Keywords: paani leak, pipeline burst, broken water pipe, water wastage, nal ka paani behna, drinking water supply, jal). Authority: Public Health Engineering Department (PHED), Government of Rajasthan - Jaipur District Control Room. Submit via: Jaipur District Control Room Phone 0141-2706624 or PHED State Control Room 0141-2222585. Rule: not available. Escalate to: Chief Engineer (Urban & NRW), PHED Jaipur (0141-2222053, rj_cehq@nic.in) or Rajasthan Sampark Helpline 181. Source: https://sampark.rajasthan.gov.in (Verified: 24-11-2026).",
    "Issue: Sewer overflow, choked drains, and dirty water stagnation (Keywords: naali jaam, sewer overflow, gatar, drainage blockage, dirty water stagnation, sewage leak). Authority: Nagar Nigam Jaipur (Jaipur Municipal Corporation) - Superintending Engineer (Sewer Project) / Executive Engineer (Liquid Waste Management). Submit via: JMC Call Centre 0141-2747400 (08:00 AM to 10:00 PM), 'Jaipur Samadhan' app, or http://jaipurmc.org (Online Services -> Register Your Complaint). Rule: Rajasthan Municipalities Act, 2009 (Chapter XI - Drainage and Sewerage) & Water (Prevention and Control of Pollution) Act, 1974. Escalate to: JMC Control Room (0141-2742900) or Commissioner JMC (commissioner.jmc@rajasthan.gov.in). Source: http://jaipurmc.org/Presentation/Others/ConctactUs.aspx (Verified: 23-11-2026).",
    "Issue: Illegal tree cutting, felling, or damage to forest trees (Keywords: ped katna, tree cutting, illegal tree felling, branch cutting, jungle, forest destruction). Authority: Forest Department, Government of Rajasthan. Submit via: Rajasthan Sampark Portal (https://rajasthan.gov.in -> Parivad Panjikaran) or Toll-Free Helpline 181 (0141-2922272, 2921646). Rule: The Rajasthan Forest Act, 1953 and Rajasthan Forest Policy 2023. Escalate to: Department of Public Grievances, Secretariat Jaipur (0141-2922825, 0141-2385077, ds.rpg@rajasthan.gov.in). Source: https://sampark.rajasthan.gov.in (Verified: 24-11-2026).",
    "Issue: Destruction of local biodiversity, heritage sites, sacred groves, or wildlife habitats (Keywords: biodiversity damage, sacred grove, heritage trees, flora fauna harm, wildlife disturbance). Authority: Rajasthan State Biodiversity Board, Jaipur (Member Secretary / Chief Manager Technical). Submit via: Phone 0141-2362188, 0141-2362088 or Email rajsbb@rajasthan.gov.in / rajasthansbb@gmail.com (Address: Arawali Bhawan, First Floor, Jhalana Institutional Area, Jaipur 302004). Rule: Biological Diversity Act, 2002 and Rajasthan Biological Diversity Rules, 2010. Escalate to: Rajasthan Sampark Portal (https://rajasthan.gov.in) or Helpline 181. Source: https://sampark.rajasthan.gov.in (Verified: 24-11-2026).",
    "Issue: Noise pollution and industrial or vehicular air pollution (Keywords: tez awaaz, shor, loudspeaker, DJ noise, late night music, generator noise, factory smoke, dhuan, air pollution, dust). Authority: Rajasthan State Pollution Control Board (RSPCB). Submit via: Rajasthan Sampark Portal (https://sampark.rajasthan.gov.in) under Public Grievance with location, nature of pollution, and photos/videos. Rule: Noise Pollution (Regulation and Control) Rules, 2000 (Rule 5) & Air (Prevention and Control of Pollution) Act, 1981. Escalate to: Rajasthan Sampark Toll-Free Helpline 181 (0141-2922272, 2921646) or Department of Public Grievances (ds.rpg@rajasthan.gov.in). Source: https://rajasthan.gov.in (Verified: 23-11-2026).",
    "Issue: General civic or environmental grievance escalation when no action is taken (Keywords: unresolved complaint, no action, sunwai nahi hui, escalation, shikayat, pending complaint, parivad panjikaran). Authority: Department of Public Grievances, Government of Rajasthan (Rajasthan Sampark). Submit via: Rajasthan Sampark Portal (https://rajasthan.gov.in -> Parivad Panjikaran), Toll-Free Helpline 181, Call Center (0141-2922272, 2921646), Tech Helpdesk (0141-2922293), or Email rajsampark@rajasthan.gov.in. Rule: not available. Escalate to: Director of Public Grievances & Ex-Officio Special Secretary - Room No. 7220, Food Building, 2nd Floor, Secretariat, Jaipur (0141-2922825, 0141-2385077, ds.rpg@rajasthan.gov.in). Source: https://rajasthan.gov.in/ContactUs (Verified: 24-11-2026).",
]

ids = [f"complaint_{i}" for i in range(1, len(documents) + 1)]

# Source-link / rule corrections (same as notebook cell 3)
S = "https://sampark.rajasthan.gov.in"
RSPCB = "https://environment.rajasthan.gov.in/content/environment/en/rajasthan-state-pollution-control-board/ComplaintPage.html"
common = [
    ("(https://rajasthan.gov.in)", f"({S})"),
    ("https://rajasthan.gov.in -> Parivad", f"{S} -> Parivad"),
    ("https://rajasthan.gov.in/ContactUs", f"{S}/ContactUs"),
    ("Rajasthan Municipalities Act, 2009 (Section 226)", "Rajasthan Municipalities Act, 2009"),
    ("Rajasthan Municipalities Act, 2009 (Chapter XI - Drainage and Sewerage)", "Rajasthan Municipalities Act, 2009"),
]
specific = {
    3: [("Source: https://sampark.rajasthan.gov.in", "Source: https://phedwater.rajasthan.gov.in/content/raj/water/public-health-engineering-department/en/citizencorner/phed-control-room-no-.html")],
    6: [("Source: https://sampark.rajasthan.gov.in", "Source: https://environment.rajasthan.gov.in/content/environment/en/rajasthan-state-biodiversity-board/background/Grievance.html")],
    7: [("Source: https://rajasthan.gov.in", f"Source: {RSPCB}")],
}
for i in range(len(documents)):
    for old, new in common + specific.get(i, []):
        documents[i] = documents[i].replace(old, new)

# ----------------------------------------------------------------------------
# 2. Short multilingual search texts (what is embedded and searched)
# ----------------------------------------------------------------------------
search_texts = [
    "Garbage dumping, overflowing dustbin, uncollected municipal solid waste, street litter, garbage piled up in lane causing mosquitoes. कचरा, कूड़ा, कूड़ेदान खाली नहीं हुआ, गंदगी, सफाई, कचरे का ढेर, मच्छर. kachra, kooda, kuda pada hai, gali mein kachra, safai nahi ho rahi, dustbin overflow, machhar, mosquitos.",
    "Construction and demolition waste dumping, malba accumulation, rubble, building debris on road. मलबा, निर्माण कचरा, पत्थर, मिट्टी. malba sadak par daal diya, ghar tod kar malba, C&D waste, patthar mitti.",
    "Waste and open garbage burning, smoke, burning dry leaves or plastic in park or street. कचरा जलाना, धुआँ, आग लगाना. kachra jalate hain, kooda jalana, patte jalana, dhuan ghar tak aata hai.",
    "Drinking water supply leakage, burst water pipeline, clean water wastage on road. पानी लीक, पाइपलाइन फट गई, पानी बह रहा है, पानी बर्बाद. pipeline phat gayi, paani leak, nal ka paani beh raha hai.",
    "Sewer overflow, choked drains, blocked naali, dirty sewage water stagnation and bad smell. सीवर ओवरफ्लो, नाली जाम, गटर, गंदा पानी भर गया, बदबू. sewer ka paani, naali jaam, gatar overflow, badbu aa rahi hai.",
    "Illegal tree cutting, felling trees without permission, cutting branches in colony or park. पेड़ कटाई, पेड़ काटना, बिना अनुमति पेड़ काट रहे हैं. colony ke bahar kuch log bina permission ke purane ped kaat rahe hain, ped katna.",
    "Destruction of local biodiversity, heritage sites, sacred groves, wildlife habitat harm. जैव विविधता, धरोहर वृक्ष, वन्यजीव नुकसान. biodiversity damage, sacred grove, heritage trees.",
    "Noise pollution, loud speaker, DJ noise at night, late night music disturbing sleep. ध्वनि प्रदूषण, शोर, लाउडस्पीकर, डीजे, रात को तेज़ आवाज़. raat ko 12 baje tak speaker bajte hain, neend nahi aati, tez awaaz, DJ shor.",
    "General civic or environmental grievance escalation when no action is taken on pending complaint. शिकायत पर कोई सुनवाई नहीं हुई, लंबित शिकायत. complaint par koi sunwai nahi hui, no action taken, unresolved complaint escalation.",
]

# ----------------------------------------------------------------------------
# 3. Vector store (built in memory at startup)
# ----------------------------------------------------------------------------
multilingual_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="paraphrase-multilingual-MiniLM-L12-v2"
)
chroma_client = chromadb.Client()
try:
    chroma_client.delete_collection("civic_complaints")
except Exception:
    pass
collection = chroma_client.create_collection(
    name="civic_complaints", embedding_function=multilingual_ef
)
collection.upsert(
    documents=search_texts,
    metadatas=[{"full_entry": d} for d in documents],
    ids=ids,
)

# ----------------------------------------------------------------------------
# 4. Gemini client with retry + fallback
# ----------------------------------------------------------------------------
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
MODELS = ["gemini-3.5-flash-lite", "gemini-3.8-flash"]


def safe_generate(contents, config=None, retries=3):
    for model_name in MODELS:
        for attempt in range(retries):
            try:
                return client.models.generate_content(
                    model=model_name, contents=contents, config=config
                )
            except Exception as e:
                err = str(e)
                if any(k in err for k in ("503", "UNAVAILABLE", "429", "RESOURCE_EXHAUSTED")):
                    time.sleep(2 ** attempt)
                    continue
                raise
    raise RuntimeError("All fallback models are temporarily busy. Try again in a moment.")


COVERED_CATEGORIES = (
    "Covered categories: garbage dumping, construction & demolition waste, "
    "open burning, water supply leakage, sewer overflow, illegal tree cutting, "
    "biodiversity harm, noise/air pollution, and grievance escalation. "
    "कवर की गई श्रेणियाँ: कचरा, मलबा, खुले में जलाना, पानी रिसाव, सीवर ओवरफ्लो, "
    "पेड़ कटाई, जैव विविधता, ध्वनि/वायु प्रदूषण, शिकायत एस्केलेशन।"
)


def add_categories(result):
    if isinstance(result, dict) and "error" in result:
        result["error"] = str(result["error"]).rstrip(". ") + ". " + COVERED_CATEGORIES
    return result


def build_structured_response(text, language="English", location="", timestamp=""):
    # TRUE RAG RETRIEVAL: top-3 verified entries for the raw user text
    query_result = collection.query(query_texts=[text], n_results=3)
    metas = query_result["metadatas"][0] if (query_result and query_result.get("metadatas")) else []
    retrieved_entries = [m["full_entry"] for m in metas]

    if not retrieved_entries:
        return add_categories({"error": "This issue is not covered under Jaipur civic & environmental complaints."})

    retrieved_context = "\n\n---\n\n".join(
        [f"Option {i+1}: {entry}" for i, entry in enumerate(retrieved_entries)]
    )

    lang_clean = language.strip().lower()
    if "hindi" in lang_clean or "हिन्दी" in lang_clean:
        lang_instruction = "Write the 'letter' field completely in polite, official Hindi (Devanagari script), while keeping all phone numbers, emails, and URLs verbatim. Close with [आपका नाम] and [मोबाइल नंबर]."
    else:
        lang_instruction = "Write the 'letter' field in clear, formal English. Close with [Your Name] and [Your Contact Number]."

    location_context = location if location else "Not provided (use placeholder [Exact Landmark / Ward, Jaipur])"

    prompt = f"""
Role: You are 'Hari Awaaz', a civic complaint drafting tool for Jaipur, Rajasthan (never use 'Hari Awaaz' as the sender's name inside the letter).
Task: Read 'User Complaint' and the 3 'Retrieved Entries' below.
- If the complaint is unrelated to Jaipur civic/environmental issues or fits NONE of the 3 Retrieved Entries, return ONLY:
  {{"error": "This issue is not covered under Jaipur civic & environmental complaints."}}
- Otherwise, pick the single best matching 'Retrieved Entry', extract its verified details, and draft a formal complaint letter on behalf of a concerned Jaipur resident based ONLY on those facts.

STRICT RULES:
1. Use ONLY facts explicitly written in the selected 'Retrieved Entry'. Do NOT guess or invent phone numbers, emails, links, or legal rules.
2. If any field (like rule) is 'not available' in the selected 'Retrieved Entry', write exactly "not available".
3. Language Requirement: {lang_instruction}
4. Timestamp & Location Header Grounding: Start the very top of the letter with two explicit header lines:
   Date & Time: {timestamp}
   Location / Landmark: [insert exact location from 'Location / Landmark', or [Exact Landmark / Ward, Jaipur] if marked Not provided]
5. Return valid JSON with these exact keys:
   - "category": short issue category name (e.g., "Garbage dumping", "Waste/open burning", "Water leakage/wastage", "Tree cutting", "Noise/air pollution", "Sewer overflow/blocked drain", "C&D waste dumping", "Biodiversity damage", "Unresolved grievance escalation")
   - "urgency": "low", "medium", or "high"
   - "authority": exact department/authority name
   - "how_to_submit": exact helpline, app, portal instructions, AND escalation phone numbers/emails from the selected Retrieved Entry
   - "rule": exact Act/Rule or "not available"
   - "source": exact source URL from the selected Retrieved Entry
   - "letter": complete formal complaint letter addressed to the authority (plain text with line breaks, no markdown asterisks)

User Complaint: {text}
Location / Landmark: {location_context}
Report Timestamp: {timestamp}
Retrieved Entries:
{retrieved_context}
"""
    res = safe_generate(
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.2, response_mime_type="application/json"
        ),
    )
    parsed = json.loads(res.text.strip())
    return add_categories(parsed)


# ----------------------------------------------------------------------------
# 5. Flask API
# ----------------------------------------------------------------------------
app = Flask(__name__)
CORS(app)


@app.route("/", methods=["GET"])
def health():
    return "Hari Aawaz API is running", 200


@app.route("/api/complaint", methods=["POST"])
def process_complaint():
    try:
        data = request.get_json(force=True)
        user_text = data.get("complaint", "").strip()[:1000]  # cap input length
        target_language = data.get("language", "English").strip()
        location_text = data.get("location", "").strip()[:200]

        ist = timezone(timedelta(hours=5, minutes=30))
        default_ts = datetime.now(ist).strftime("%d %b %Y, %I:%M %p IST")
        report_timestamp = data.get("timestamp", "").strip() or default_ts

        if not user_text:
            return jsonify({"error": "Empty complaint text."}), 400
        result = build_structured_response(
            user_text, target_language, location_text, report_timestamp
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 7860)))
