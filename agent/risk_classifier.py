"""
Step 3 of the pipeline: given an entity and its Parallel search results,
have Gemini classify the clearance risk and produce a cited verdict.
"""

from __future__ import annotations

import json
import os
from typing import Any

from google import genai
from pydantic import BaseModel


class RiskVerdict(BaseModel):
    entity_name: str
    entity_type: str
    risk_level: str  # clear | flag | escalate
    reasoning: str
    recommended_action: str
    sources: list[str]


CLASSIFICATION_PROMPT = """You are a production legal risk analyst. Given an \
entity referenced in a script and web research about it, classify the \
clearance risk.

Entity: {entity_name} ({entity_type})
Script context: {context}

Web research findings:
{research_json}

Classify risk_level as one of:
- "clear": no meaningful legal/clearance concern found
- "flag": some risk signal found (recent dispute, ambiguous rights, needs a
  human clearance-team review before shooting)
- "escalate": active litigation, cease-and-desist, or high-profile dispute —
  do not proceed without legal sign-off

Return ONLY valid JSON matching this schema, no other text:
{{"risk_level": "...", "reasoning": "...", "recommended_action": "..."}}
"""


def classify_risk(
    entity_name: str, entity_type: str, context: str, research: dict[str, Any]
) -> RiskVerdict:
    client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))

    prompt = CLASSIFICATION_PROMPT.format(
        entity_name=entity_name,
        entity_type=entity_type,
        context=context,
        research_json=json.dumps(research.get("sources", []), indent=2),
    )

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt,
        config={"response_mime_type": "application/json"},
    )

    data = json.loads(response.text)

    return RiskVerdict(
        entity_name=entity_name,
        entity_type=entity_type,
        risk_level=data["risk_level"],
        reasoning=data["reasoning"],
        recommended_action=data["recommended_action"],
        sources=[s["url"] for s in research.get("sources", []) if s.get("url")],
    )
