# Hari Awaaz - Environmental Complaint Helper (Jaipur)

A Hindi / English / Hinglish assistant that helps a citizen turn a description of an environmental problem (garbage dumping, waste burning, water leakage, tree cutting, noise/air pollution, C&D waste, sewer overflow, biodiversity harm, or unresolved grievance escalation) into a ready-to-submit complaint letter, using details retrieved from a source-linked knowledge base instead of the model's memory.

> **Prototype for a Prompt Engineering capstone project.** It is not an official government service.
> Always verify authority names, helplines, and rules on the official source before relying on them.
> Please do not enter phone numbers or other personal details.

**Live frontend:** `https://hari-aawaz.vercel.app`

**Backend API:** Runs via Google Colab + Cloudflare Quick Tunnel (see setup instructions below):
`https://hari-aawaz.vercel.app/?api=[cloudflare-tunnel-link-generated-in-colab]`


## The problem
Citizens often do not know which authority handles an environmental problem, how to submit a complaint, or what to do if nothing happens. General chatbots can answer, but they may give outdated or invented contact details. This project grounds every answer in collected official sources, injects deterministic submission metadata (landmark + live IST timestamp), and shows where each detail came from.

## How it works
```text
Citizen text + Landmark + Language + Live IST Timestamp
  --> 1. Multilingual Vector Retrieval (ChromaDB + paraphrase-multilingual-MiniLM-L12-v2, n_results=3)
  --> 2. Grounded Selection & Letter Drafting (Gemini, JSON schema output, temp=0.2)
  --> 3. Structured JSON Response --> Web UI
```

| Part | What it is |
|---|---|
| Frontend | HTML, CSS, and JavaScript web app (`https://vercel.app`) with complaint box, optional Jaipur landmark input, letter language selector (`English` / `Hindi`), and automatic `Asia/Kolkata` IST timestamp capture |
| Backend | Flask API (`/api/complaint`) served from Google Colab via a live `pycloudflared` quick tunnel |
| Retrieval | In-memory ChromaDB (`paraphrase-multilingual-MiniLM-L12-v2`) with focused English, Devanagari Hindi, and Hinglish search strings mapped to 9 verified Jaipur government metadata entries |
| LLM | Google Gemini through the `google-genai` SDK, with exponential backoff retry and model fallback (`gemini-3.5-flash-lite` -> `gemini-3.8-flash`) |

## Prompt engineering techniques used
- **Structured prompt design:** Explicit Role, Task, Context, Constraints, and Output-format instructions (`'Hari Awaaz'` civic drafting persona).
- **Single-call RAG grounding:** Passes the top-3 retrieved knowledge base entries to Gemini to select the best match, extract verified authority details, and draft the formal letter in one low-latency pass.
- **Schema-enforced structured output:** Uses `response_mime_type="application/json"` at low temperature (`0.2`) to guarantee consistent JSON keys (`category`, `urgency`, `authority`, `how_to_submit`, `rule`, `source`, `letter`).
- **Strict extractive grounding:** Uses only facts explicitly written in the selected entry, outputs `"not available"` when a field is missing, and never invents phone numbers, emails, links, or legal rules.
- **Out-of-scope guardrail:** Rejects unrelated queries with a bilingual error message listing all 9 covered civic/environmental categories.
- **Explicit output language control:** Generates letters in formal Devanagari Hindi or formal English based on the UI dropdown while keeping phone numbers, emails, and URLs verbatim.
- **Deterministic context injection & privacy placeholders:** Embeds live IST timestamp and user landmark, or inserts bracketed placeholders (`[Exact Landmark / Ward, Jaipur]`, `[Your Name]`, `[Your Contact Number]`) without exposing PII.
- **Resilience:** Exponential backoff retry and automatic model fallback for `503` / `429` API errors.
- **Iterative prompt logging:** Prompt versions v1 (unstructured) to v3 (grounded JSON RAG) and temperature experiments (`0.0` / `0.5` / `1.0`) recorded in `docs/`.

## Repository structure
```text
frontend/    index.html, style.css, script.js        (deployed on Vercel)
backend/     app.py, requirements.txt                (standalone Flask API)
notebook/    Hari_Aawaz_Final.ipynb                  (RAG pipeline, evaluation tests & Colab Flask server)
data/        knowledge base entries with verified official source links
docs/        prompt log, test results, screenshots
README.md
LICENSE
```

## Running it (Google Colab Demo)
1. Open `notebook/Hari_Aawaz_Final.ipynb` in Google Colab.
2. In Colab's left sidebar, open **Secrets (🔑)** and add your own Gemini API key with the name `GEMINI_API_KEY` (no private keys are stored in this repository).
3. Run all cells in order. The Flask server cell starts the API and prints a live `https://<random-subdomain>://` URL.
4. Paste that printed URL into `API_URL` in `frontend/script.js` (or your Vercel environment configuration) to connect the frontend to the live Colab backend.

## Knowledge base
Each entry contains an issue category with English/Hindi/Hinglish keywords, responsible authority, submission channels, governing rule/Act, escalation path, and **an official source link with the date verified (23–24 Nov 2026)**.
Entries were manually verified against official Rajasthan and Indian government portals (`jaipurmc.org`, `environment.rajasthan.gov.in`, `sampark.rajasthan.gov.in`, `phedwater.rajasthan.gov.in`).

- **Verification status:** `9 / 9` entries verified against official government portals (screenshots archived in `docs/`).
- **Anti-hallucination controls:** `2` entries (*Water Supply Leakage* and *Unresolved Grievance Escalation*) intentionally retain `"Rule: not available"` to verify that the LLM outputs `"not available"` rather than inventing legal citations.

## Evaluation

| Retrieval Metric | Result |
|---|---|
| Multilingual retrieval accuracy across English, Hindi & Hinglish test queries (`Top 1` match) | `8 / 8` (`100%`) |
| Out-of-scope guardrail rejection (unrelated queries blocked with bilingual category guidance) | `100%` |
| Unsupported details / hallucinated rules found in drafted letters | `0` |
| Bilingual letter generation (English & Devanagari Hindi) with verbatim contacts/URLs | Verified |

## Limitations
- Prototype only: scoped to Jaipur city, covering 9 civic and environmental categories.
- Because the backend runs on Google Colab via a temporary Cloudflare Quick Tunnel, the tunnel URL changes per Colab session and stays active only while the Colab runtime is running.
- Free-tier Gemini API rate limits (`429` / `503`) can occasionally slow down responses (mitigated via automatic retry and model fallback).
- Official contacts and rules change over time; each entry records its verification date (`Nov 2026`).
- Drafts a ready-to-submit letter only; does not directly file, store, or track complaints on government portals.

## Future scope
Add Jaipur ward-level sub-routing (mapping wards to zonal offices), persistent vector database storage, and multimodal image/voice input for geotagged photo evidence.

## AI tools used
Frontend first draft: Bolt.new. Code assistance, RAG integration, and prompt refinement: Gemini and Claude. All prompt iterations and fixes are recorded in `docs/prompt_log`.

## Author
`AKSHITA TEJWANI, 25BCON0140, JECRC University`

## License
MIT
