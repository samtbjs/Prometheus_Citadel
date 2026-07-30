"""
ai/client.py

THE ONE DOOR: this is the ONLY file in the codebase that imports
`OpenAI` or calls `.chat.completions.create()`. Every AI-flavored
feature (today's tutor verdict, and anything added in later phases --
the mastery loop, the "what to attempt next" director, reward flavor
text) must call `ask_arbiter()` below instead of building its own
client. That way there is exactly one place to change the model, the
token budget, or add retry/fallback logic later.
"""

import os

from dotenv import load_dotenv
from openai import OpenAI

# Load variables from the .env file (like OPENAI_API_KEY) into the
# environment. Must happen before we try to read the key below.
load_dotenv()

# The only model this app is allowed to call.
MODEL = "gpt-4o-mini"


def _get_client():
    """
    Builds the OpenAI client fresh on each call (not at import time), so
    a missing/blank key raises a clear error only when someone actually
    tries to use it, not the moment the app starts up.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is missing or blank. Add it to your .env file."
        )
    return OpenAI(api_key=api_key)


def ask_arbiter(system_prompt, user_message, max_tokens=300, temperature=0):
    """
    THE single function every AI call in this app goes through.

    Inputs:
      - system_prompt: persona/instructions for the model.
      - user_message: the actual question/content for this call.
      - max_tokens: hard cap on reply length (default 300, matching the
        existing tutor.py budget -- keep new callers within this same
        order of magnitude for short verdicts/lines).
      - temperature: sampling temperature (default 0, deterministic).

    Returns the raw text of the model's reply.

    Raises RuntimeError if OPENAI_API_KEY is missing/blank, and
    re-raises whatever the OpenAI SDK raises for network/rate-limit/API
    errors -- callers must catch those themselves and fall back
    gracefully (exactly as ai/tutor.py already does).
    """
    client = _get_client()

    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=max_tokens,
        temperature=temperature,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
    )

    return response.choices[0].message.content
