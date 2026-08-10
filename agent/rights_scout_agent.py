"""
Rights & Clearance Scout — main agent.

Defines the agent using Google's Agent Development Kit (ADK), the code-first
framework for the Gemini Enterprise Agent Platform, and wires up the
deterministic 3-step pipeline:

    extract_entities  ->  parallel_clearance_search (per entity)  ->  classify_risk

The `root_agent` object below is what `adk run` / `adk web` / Agent Engine
deployment discover automatically. `run_pipeline()` is a plain-Python entry
point used by the FastAPI backend and the CLI, so the same logic works
whether you're driving it through the ADK runtime or embedding it in your
own service.
"""

from __future__ import annotations

import sys

from google.adk.agents import Agent

from agent.entity_extraction import extract_entities
from agent.risk_classifier import classify_risk
from agent.tools.parallel_search import parallel_clearance_search

AGENT_INSTRUCTIONS = """You are the Rights & Clearance Scout, an agent that \
helps film/TV production legal teams catch clearance risk before shooting.

Given a script or shot-list excerpt, you:
1. Identify every song, brand, real person, trademark, and location mentioned
   that could carry legal clearance risk.
2. For each one, use the parallel_clearance_search tool to research its
   current legal/licensing status on the open web.
3. Classify each as clear / flag / escalate with a short reasoning and a
   recommended next action, citing your sources.

Always work through entities one at a time and be conservative: when in
doubt, flag rather than clear. Never fabricate a source — only cite URLs
returned by parallel_clearance_search.
"""

# The ADK agent registered with Gemini Enterprise. `adk web` or `adk run`
# will pick this up automatically; it's also what gets deployed to Vertex AI
# Agent Engine (see DEPLOY.md).
root_agent = Agent(
    name="rights_clearance_scout",
    model="gemini-3.6-flash",
    description=(
        "Scans scripts and shot lists for legal clearance risk (songs, "
        "brands, real people, trademarks, locations) using live web research."
    ),
    instruction=AGENT_INSTRUCTIONS,
    tools=[parallel_clearance_search],
)


def run_pipeline(script_text: str) -> list[dict]:
    """Deterministic pipeline version of the agent, used by app.py and the CLI.

    Runs the same 3 steps the ADK agent performs, but as explicit Python
    control flow rather than letting the model decide tool-call order. This
    guarantees every entity gets researched and classified, which matters
    for a compliance workflow — useful when you want reproducible behavior
    instead of the model's own planning loop.
    """
    extraction = extract_entities(script_text)

    report = []
    for entity in extraction.entities:
        research = parallel_clearance_search(entity.name, entity.type)
        verdict = classify_risk(entity.name, entity.type, entity.context, research)
        report.append(verdict.model_dump())

    return report


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python -m agent.rights_scout_agent <script_file.txt>")
        sys.exit(1)

    with open(sys.argv[1], "r", encoding="utf-8") as f:
        text = f.read()

    results = run_pipeline(text)

    for r in results:
        print(f"\n[{r['risk_level'].upper()}] {r['entity_name']} ({r['entity_type']})")
        print(f"  Reasoning: {r['reasoning']}")
        print(f"  Action:    {r['recommended_action']}")
        if r["sources"]:
            print(f"  Sources:   {', '.join(r['sources'])}")
