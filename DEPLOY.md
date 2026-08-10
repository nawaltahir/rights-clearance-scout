# Deploying to Gemini Enterprise Agent Platform

This walks through taking `agent/rights_scout_agent.py` from a local ADK
agent to a governed, registered agent running on Google Cloud, which is what
the hackathon submission needs to demonstrate.

## 0. Prerequisites

```bash
# Install the Google Cloud CLI, then:
gcloud auth login
gcloud auth application-default login
gcloud config set project YOUR_PROJECT_ID

# Enable the APIs you need
gcloud services enable aiplatform.googleapis.com \
                        run.googleapis.com \
                        cloudbuild.googleapis.com
```

Install the ADK CLI (already in `requirements.txt`, but standalone install
also works):

```bash
pip install google-adk
```

## 1. Run and test the agent locally with ADK's dev UI

From the project root:

```bash
adk web
```

This launches ADK's local web UI, auto-discovers `root_agent` in
`agent/rights_scout_agent.py`, and lets you chat with it and watch its tool
calls (including every `parallel_clearance_search` call) in real time. This
is the fastest way to debug the extraction → research → classification loop
before deploying anything.

You can also run it headless from the CLI:

```bash
adk run agent
```

## 2. Register the agent in Gemini Enterprise

1. Open your Gemini Enterprise web app (console.cloud.google.com →
   **Gemini Enterprise**).
2. Create (or select) an **App** — this is the container agents live in.
3. In the app, click **+ Create agent** → since we already have a
   code-first ADK agent, choose the **flow builder / import** path rather
   than the prompt-only quick-create, and point it at this repo (or the
   deployed Agent Engine endpoint from step 3).
4. Gemini Enterprise will register the agent's name, description, and tool
   list (you'll see `parallel_clearance_search` listed as a registered
   tool) — this is what gives you the governance layer: Agent Identity lets
   you scope exactly what this agent can call and with what permissions.

## 3. Deploy the agent runtime to Vertex AI Agent Engine

Agent Engine is the managed, scalable compute environment Gemini Enterprise
Agent Platform uses to run ADK agents in production (as opposed to `adk web`,
which is local-only).

```bash
gcloud ai agent-engines deploy \
  --project=YOUR_PROJECT_ID \
  --region=us-central1 \
  --agent-module=agent.rights_scout_agent \
  --agent-name=rights-clearance-scout \
  --requirements-file=requirements.txt \
  --env-vars-file=.env
```

(Exact flags evolve with the platform — check `gcloud ai agent-engines
deploy --help` or the Agent Platform docs for the current syntax at deploy
time; the ADK project scaffold also includes an `adk deploy agent_engine`
shortcut that wraps this.)

Once deployed, Agent Engine gives you an endpoint you can call from the
FastAPI backend (`app.py`) instead of running the pipeline in-process — swap
`run_pipeline()` for a call to the deployed endpoint if you want the
demo app talking to the managed runtime rather than local Python.

## 4. Deploy the demo UI (FastAPI app) to Cloud Run

This is the part judges actually click on — the hosted project URL.

```bash
gcloud run deploy rights-clearance-scout \
  --source . \
  --region=us-central1 \
  --allow-unauthenticated \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=YOUR_PROJECT_ID,GOOGLE_GENAI_USE_VERTEXAI=true" \
  --set-secrets="PARALLEL_API_KEY=parallel-api-key:latest"
```

(Store `PARALLEL_API_KEY` in Secret Manager first: `gcloud secrets create
parallel-api-key --data-file=-` and paste the key.)

Cloud Run builds the `Dockerfile` in this repo automatically via Cloud
Build, and gives you a public HTTPS URL — that's your "URL to hosted
Project" for the Devpost submission.

## 5. What to show in the demo video

1. Open the hosted Cloud Run URL.
2. Paste `sample_data/sample_script.txt` into the UI.
3. Show the agent working through each entity live (it calls Parallel per
   entity — real API calls, not canned data).
4. Show the final report: clear/flag/escalate verdicts with cited sources.
5. Briefly show the ADK dev UI (`adk web`) or Gemini Enterprise console to
   prove the underlying agent is registered on Google Cloud, not just a
   plain script calling two APIs.

This directly satisfies the submission requirement that Google Cloud and
the Parallel service are "imported and called in code, not just named in
the README."
