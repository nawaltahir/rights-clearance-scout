# Rights & Clearance Scout 🎬

**An autonomous agent that flags legal-clearance risk in scripts and shot lists — before it becomes an expensive problem on set.**

Built for the **Agentic Cinema: The Blockbuster Hackathon** — Parallel track.

Service URL: https://rights-clearance-scout-445594624234.us-central1.run.app

## The problem

Before a scene can be shot, legal/production teams have to manually check every song, brand, real person, and location referenced in a script for clearance risk: active litigation, licensing disputes, right-of-publicity issues, trademark conflicts. This is slow, manual, and easy to miss things on — a single uncleared song cue or a real person's name in a "based on true events" script can trigger a six-figure lawsuit or a forced re-shoot.

Rights & Clearance Scout automates the first pass: it reads a script excerpt or shot list, identifies every entity that carries legal risk, researches each one's *current* status on the open web (not stale training data — active news, lawsuits, disputes), and returns a structured, source-cited risk report with a recommended action per entity.

## Architecture

```
                    ┌─────────────────────────────┐
                    │   Gemini Enterprise Agent    │
                    │   (Agent Development Kit)    │
                    └──────────────┬──────────────┘
                                   │
        ┌──────────────────────────┼──────────────────────────┐
        │                          │                          │
┌───────▼────────┐      ┌──────────▼──────────┐    ┌──────────▼──────────┐
│ 1. Entity       │      │ 2. Parallel Search    │    │ 3. Risk Synthesis    │
│    Extraction   │─────▶│    Tool (per entity)  │───▶│    & Report Builder  │
│  (Gemini call)  │      │  api.parallel.ai      │    │  (Gemini call)       │
└─────────────────┘      └──────────────────────┘    └──────────────────────┘
```

The agent runs a deterministic, multi-step pipeline (not a single free-form chat turn):

1. **Extract** — Gemini parses the uploaded script/shot list and pulls out every entity that carries clearance risk: song titles, brand/product mentions, real people's names, trademarks, real locations.
2. **Research** — for *each* extracted entity, the agent calls the **Parallel Search API** to pull current, cited web results (recent litigation, licensing news, disputes, right-of-publicity concerns). This is the step that makes the agent "agentic" rather than a single LLM call — it's a tool-use loop over a dynamic list the model itself produced.
3. **Synthesize** — Gemini classifies each entity's risk (`clear` / `flag` / `escalate`) and writes a structured report, citing the sources Parallel returned.

## Tech stack

| Layer | Technology |
|---|---|
| Agent orchestration | Google Cloud **Gemini Enterprise Agent Platform** — Agent Development Kit (ADK) |
| Model | Gemini (via ADK's Gemini model client) |
| Live web research | **Parallel Search API** (partner integration) |
| Backend | Python, FastAPI |
| UI | Single-page HTML/JS (`static/index.html`) served by FastAPI |
| Deployment target | Vertex AI Agent Engine (Gemini Enterprise Agent Platform runtime) |

## Project layout

```
rights-clearance-scout/
├── agent/
│   ├── rights_scout_agent.py   # ADK agent definition + pipeline orchestration
│   ├── entity_extraction.py    # Step 1: Gemini entity extraction
│   ├── risk_classifier.py      # Step 3: Gemini risk synthesis
│   └── tools/
│       └── parallel_search.py  # Step 2: Parallel Search API tool wrapper
├── app.py                      # FastAPI server exposing the agent + serving the UI
├── static/index.html           # Minimal upload UI for the demo
├── sample_data/sample_script.txt
├── requirements.txt
├── Dockerfile                  # For Agent Engine / Cloud Run deployment
├── .env.example
└── LICENSE
```

## Setup

```bash
git clone <your-repo-url>
cd rights-clearance-scout
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in your keys
```

You need two keys in `.env`:

```
GOOGLE_API_KEY=...        # or GOOGLE_APPLICATION_CREDENTIALS for Vertex AI service account
PARALLEL_API_KEY=...      # from platform.parallel.ai
```

Run locally:

```bash
uvicorn app:app --reload
# open http://localhost:8000
```

Or run the agent directly from the CLI against the sample script:

```bash
python -m agent.rights_scout_agent sample_data/sample_script.txt
```

## Deploying to Google Cloud (Gemini Enterprise Agent Platform)

See **[DEPLOY.md](./DEPLOY.md)** for the full walkthrough of taking this from local ADK agent → registered, governed agent in Gemini Enterprise, deployed on Vertex AI Agent Engine.

## License

MIT — see [LICENSE](./LICENSE).
