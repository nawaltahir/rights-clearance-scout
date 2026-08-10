"""
Parallel Search API tool.

This is the Partner integration for the hackathon's Parallel track. It wraps
api.parallel.ai's Search endpoint as a callable ADK tool so the Gemini agent
can invoke it autonomously, per-entity, during the research step of the
pipeline.

Docs: https://docs.parallel.ai/search/search-quickstart
"""

from __future__ import annotations

import os
from typing import Any

from parallel import Parallel

_client: Parallel | None = None


def _get_client() -> Parallel:
    global _client
    if _client is None:
        api_key = os.environ.get("PARALLEL_API_KEY")
        if not api_key:
            raise RuntimeError(
                "PARALLEL_API_KEY is not set. Get one at platform.parallel.ai "
                "and add it to your .env file."
            )
        _client = Parallel(api_key=api_key)
    return _client


def parallel_clearance_search(entity_name: str, entity_type: str) -> dict[str, Any]:
    """Research an entity's current legal/clearance risk on the open web.

    This is registered as a Tool on the ADK agent. The model calls it once
    per extracted entity (song, brand, real person, trademark, location)
    during the research step of the pipeline.

    Args:
        entity_name: The entity as it appears in the script, e.g. "Coca-Cola",
            "Bohemian Rhapsody", "John Smith (real person referenced)".
        entity_type: One of "song", "brand", "person", "trademark", "location".

    Returns:
        A dict with the objective used, and a list of source-cited excerpts
        Gemini can reason over when classifying risk.
    """
    client = _get_client()

    objective = (
        f"Find current information about legal, licensing, or clearance risk "
        f"involving the {entity_type} '{entity_name}'. Focus on active "
        f"litigation, recent licensing disputes, right-of-publicity issues, "
        f"trademark conflicts, or cease-and-desist actions."
    )

    search_queries = [
        f"{entity_name} lawsuit OR litigation",
        f"{entity_name} licensing dispute OR cease and desist",
        f"{entity_name} rights clearance media entertainment",
    ]

    result = client.search(
        objective=objective,
        search_queries=search_queries,
        mode="advanced",
    )

    excerpts = []
    for r in getattr(result, "results", []) or []:
        excerpts.append(
            {
                "url": getattr(r, "url", None),
                "title": getattr(r, "title", None),
                "excerpt": (getattr(r, "excerpts", None) or [""])[0][:800],
            }
        )

    return {
        "entity_name": entity_name,
        "entity_type": entity_type,
        "objective": objective,
        "sources": excerpts,
    }
