"""
Step 1 of the pipeline: extract clearance-relevant entities from a script
or shot list using Gemini, as structured JSON.
"""

from __future__ import annotations

import json
import os

from google import genai
from agent.retry_util import call_with_retry
from pydantic import BaseModel


class Entity(BaseModel):
    name: str
    type: str  # song | brand | person | trademark | location
    context: str  # the line/scene where it appears


class ExtractionResult(BaseModel):
    entities: list[Entity]


EXTRACTION_PROMPT = """You are a production legal assistant. Read the script \
or shot-list excerpt below and extract every entity that could carry legal \
clearance risk if the production is filmed and released as-is.

Extract:
- Songs or musical works referenced or implied (e.g. needle-drops, hummed tunes)
- Brand names, products, or logos mentioned or described
- Real, named people (public figures or private individuals)
- Trademarks or trade dress described in visual detail
- Real, specific locations (named businesses, landmarks, private property)

For each, give: name, type (song|brand|person|trademark|location), and the \
surrounding context (the line or scene it appears in).

Return ONLY valid JSON matching this schema, no other text:
{{"entities": [{{"name": "...", "type": "...", "context": "..."}}]}}

SCRIPT:
---
{script_text}
---
"""


def extract_entities(script_text: str) -> ExtractionResult:
    client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))

    response = call_with_retry(
        lambda: client.models.generate_content(
            model="gemini-3.6-flash",
            contents=EXTRACTION_PROMPT.format(script_text=script_text),
            config={"response_mime_type": "application/json"},
        )
    )

    data = json.loads(response.text)
    return ExtractionResult(**data)
