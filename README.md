# Hari Awaaz - Environmental Complaint Helper (Jaipur)



A Hindi / English / Hinglish assistant that helps a citizen turn a description of an environmental problem
(garbage dumping, waste burning, water leakage, tree cutting, noise/air pollution, C&D waste, sewer overflow, biodiversity harm) into a ready-to-submit
complaint letter, using details retrieved from a source-linked knowledge base instead of the model's memory.

> **Prototype for a Prompt Engineering capstone project.** It is not an official government service.
> Always verify authority names, helplines and rules on the official source before relying on them.
> Please do not enter phone numbers or other personal details.

**Live frontend:** `https://hari-aawaz.vercel.app`
**Backend API:** Runs via Google Colab + Cloudflare Quick Tunnel (see instructions below)

## The problem
Citizens often do not know which authority handles an environmental problem, how to submit a complaint, or what to do
if nothing happens. General chatbots can answer, but they may give outdated or invented contact details.
This project grounds every answer in collected official sources, injects deterministic submission metadata (landmark + live IST timestamp), and shows where each detail came from.

## How it works
Citizen text + Landmark + Language + Live IST Timestamp
--> 1. Classify (Gemini, JSON output, temp=0.1)
--> 2.- **Classifier-Augmented Retrieval (`n_results=1`):** Prepends the classifier's normalized English category to the vector search query (`f"{category}. {text}"`) alongside Hindi/Hinglish keywords in the KB to overcome English-centric embeddings (`all-MiniLM-L6-v2`) and prevent cross-authority contamination.
--> 3. Draft (Gemini, grounded ONLY in retrieved entries + runtime context, temp=0.2) --> JSON --> web page

| Part | What it is |
|---|---|
| Frontend | HTML, CSS and JavaScript page with complaint box, optional Jaipur landmark input, letter language selector (`English` / `Hindi`), and automatic `Asia/Kolkata` IST timestamp capture |
| Backend | Flask API (`/api/complaint`) hosted on Render (or run in Google Colab via Cloudflare quick tunnel) |
| Retrieval | ChromaDB (`paraphrase-multilingual-MiniLM-L12-v2`) over 9 manually verified Jaipur government entries |
| LLM | Google Gemini through the `google-genai` SDK, with exponential backoff retry and model fallback (`gemini-3.8-flash` -> `gemini-3.5-flash-lite` -> `gemini-3.8-pro`) |

## Prompt engineering techniques used
- Role, Task, Context, Constraints and Output-format structure in every prompt (`'Hari Awaaz'`, official civic assistant persona)
- Chain prompting: classify intent & urgency, retrieve top-2 documents, then draft structured JSON response
- Schema-enforced structured output (`response_mime_type="application/json"`) and low temperature (`0.1` for classification, `0.2` for drafting)
- Strict extractive grounding rules: use only the retrieved entry, write `"not available"` for missing fields, never invent contacts or statutes
- Out-of-scope guardrail: early classifier rejection (`"Not covered"`) before retrieval or drafting
- Explicit output language control via UI dropdown (formal Devanagari Hindi vs. formal English, preserving phone numbers/emails/URLs verbatim)
- Programmatic context injection & privacy slot filling: embeds live IST timestamp and user landmark, or inserts bracketed placeholders (`[Exact Landmark / Ward, Jaipur]`, `[Your Name]`, `[Your Contact Number]`) without exposing PII
- Temperature experiment (`0.0` / `0.5` / `1.0`) - see `docs/`
- Retry with exponential backoff and model fallback for `503` / `429` API errors
- Prompt versions v1 (unstructured) to v3 (chained + grounded) logged in `docs/prompt_log`

## Repository structure
frontend/    index.html, style.css, script.js        (deployed on Vercel / Netlify)
backend/     app.py, requirements.txt                (deployed on Render)
notebook/    Hari_Aawaz_Final.ipynb                  (RAG pipeline, experiments & Colab Flask API)
data/        knowledge base entries with verified official source links
docs/        prompt log, test results, screenshots
README.md
LICENSE

## Running it

### Option A: Permanent Deployment (Render + Vercel/Netlify)
1. Deploy `backend/` (`app.py` + `requirements.txt`) as a Web Service on Render (`Start Command`: `gunicorn app:app`) and add `GEMINI_API_KEY` in Environment Variables.
2. Set `API_URL` at the top of `frontend/script.js` to your Render endpoint (`https://<your-app>.onrender.com/api/complaint`).
3. Deploy `frontend/` to Vercel or Netlify.

### Option B: Google Colab Demo
## Running it (Google Colab Demo)
1. Open `notebook/Hari_Aawaz_Final.ipynb` in Google Colab.
2. Add your own Gemini API key in Colab's left sidebar **Secrets (🔑)** with the name `GEMINI_API_KEY` (the repo does not expose any private keys).
3. Run all cells. The final cell starts the Flask server and prints a live `trycloudflare.com` URL.
4. Paste `<printed-url>/api/complaint` into `API_URL` at the top of `frontend/script.js` (or test via local frontend).

## Knowledge base
Each entry contains an issue category with English/Hindi/Hinglish keywords, responsible authority, submission channels, governing rule/Act, escalation path, and **an official source link with the date verified (23–24 Nov 2026)**.
Entries were manually verified against official Rajasthan and Indian government portals (`jaipurmc.org`, `environment.rajasthan.gov.in`, `sampark.rajasthan.gov.in`, `swmp.cpcb.gov.in`).

**Verification status:** `9 / 9 entries verified against official government portals (screenshots in docs/).`
**Anti-hallucination controls:** `2 entries (Water Supply Leakage and Unresolved Grievance Escalation) intentionally retain "Rule: not available" to verify that the LLM outputs "not available" rather than inventing legal citations.`

## Evaluation
| Retrieval accuracy — Baseline raw query (`query_texts=[text]`) | `2 / 6` |
| Retrieval accuracy — Classifier-Augmented query (`f"{category}. {text}"`) | `4 / 6` |
| Retrieval accuracy — Classifier-Augmented + Hindi/Hinglish KB keywords (`n_results=1`) | `[6 / 6]` |


| Test | Result |
|---|---|
| Classification accuracy on 8 test complaints (English, Hindi & Hinglish) | `[8 / 8]` |
| Correct authority retrieved (top 1 / top 3) | `[8 / 8]` |
| Unsupported details / hallucinated rules found in drafted letters | `0` |
| Bilingual letter generation (English & Devanagari Hindi) with intact contacts | `[3 / 3]` |
| Same complaints through ungrounded ChatGPT / Gemini / Claude vs. Hari Awaaz | `[x / N each]` |

## Limitations
- Prototype only: scoped to Jaipur city, covering 9 civic/environmental categories.
- Free-tier Gemini API rate limits (`429` / `503`) can occasionally slow down responses (mitigated via automatic retry and model fallback).
- ChromaDB's default embedding model (`all-MiniLM-L6-v2`) is English-centric, so transliterated Hinglish queries rely on curated Hindi/Hinglish keywords embedded in each KB entry.
- Official contacts and rules change over time; each entry records the verification date (`Nov 2026`).
- Drafts a ready-to-submit letter only; does not directly file, store, or track complaints on government portals.

## Future scope
Add Jaipur ward-level sub-routing (250 wards to zonal offices), persistent vector database storage, and multimodal image/voice input for geotagged photo evidence.

## AI tools used
Frontend first draft: Bolt.new. Code assistance, RAG integration, and prompt refinement: Gemini and Claude. All prompt iterations and fixes are recorded in `docs/prompt_log`.

## Author
`AKSHITA TEJWANI, 25BCON0140, JECRC University`

## License
MIT
