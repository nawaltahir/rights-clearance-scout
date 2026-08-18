"""
Shared helper for calling Gemini with automatic retry on:
  - 429 RESOURCE_EXHAUSTED (free-tier rate limit -- expected on any script
    with more than a couple entities, since each entity costs a
    classification call and the free tier caps requests per minute)
  - 503 UNAVAILABLE (temporary Google-side overload -- transient, unrelated
    to our usage, safe to retry with backoff)
"""

from __future__ import annotations

import re
import time

from google.genai import errors as genai_errors


def call_with_retry(fn, max_retries: int = 5):
    """Call `fn()` and retry on 429 or 503 errors, honoring the server's
    suggested retryDelay when present. Raises the last error if retries
    are exhausted.
    """
    last_error: Exception | None = None

    for attempt in range(max_retries):
        try:
            return fn()
        except genai_errors.ClientError as e:
            if getattr(e, "code", None) != 429:
                raise

            last_error = e
            # Parse "Please retry in 29.28s" from the error message, or
            # default to a conservative fixed backoff.
            match = re.search(r"retry in ([\d.]+)s", str(e))
            delay = float(match.group(1)) + 1 if match else 15.0
            time.sleep(delay)
        except genai_errors.ServerError as e:
            if getattr(e, "code", None) != 503:
                raise

            last_error = e
            # No retryDelay is given for 503s -- use a fixed backoff that
            # grows slightly with each attempt.
            time.sleep(10 + attempt * 5)

    raise last_error