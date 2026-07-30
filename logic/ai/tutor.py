"""
ai/tutor.py

PHASE 5: Give the AI verdict an actual PERSONALITY.

WHAT THIS FILE DOES, IN PLAIN ENGLISH
--------------------------------------------------------------------------
In Phase 4, the AI silently returned one word: resolved / thin / wrong.
That word drove the streak logic, but the student never got any real
"dialogue" back -- just a bare label on screen.

Phase 5 keeps EVERYTHING from Phase 4 (same verdict word, same streak
rules, same fallback safety net) and adds ONE new thing: a short,
in-character line of dialogue from a "ship's diagnostic AI" persona,
returned in the SAME API call as the verdict (not a second call -- that
would double the cost).

To get both pieces of information out of a single reply, we ask the
model to answer in a strict, two-line format:

    VERDICT: resolved
    RESPONSE: Good work, Engineer. The readings check out.

We then parse that text ourselves with a small, defensive parser. If
anything about the reply doesn't match what we expect (missing line,
extra chatter, garbled text), we do NOT crash or guess wildly -- we
fall back to "thin" for the verdict (exactly like Phase 4 did) and a
short hardcoded generic line for the dialogue, so the student never
sees a blank or broken message.

IMPORTANT SAFETY DETAILS (unchanged from Phase 4, still true here):
  - max_tokens is capped at 300 for the WHOLE call (verdict + dialogue
    together) -- we did not raise this budget for Phase 5.
  - The AI is never allowed to invent a physics number, formula, or
    fact. It only reacts to right/vague/wrong and asks guiding
    questions. All real physics values still come only from
    logic/physics_calc.py.
"""

import os
import re

from dotenv import load_dotenv
from openai import OpenAI

# Load variables from the .env file (like OPENAI_API_KEY) into the
# environment. This must happen before we try to read the key below.
load_dotenv()

# The three, and ONLY three, verdict values this app understands anywhere.
VALID_VERDICTS = {"resolved", "thin", "wrong"}

# Keep this well within the 250-300 token range you specified. This is a
# hard ceiling on how long the model's ENTIRE reply (verdict line +
# dialogue line, combined) is allowed to be -- the main lever for
# controlling API cost per call. We did not raise this for Phase 5, even
# though we're now asking for more content in the same call.
MAX_TOKENS = 300

# -----------------------------------------------------------------------
# PHASE 5: shown on screen any time we can't get (or can't trust) a real
# in-character line from the model -- either because the mock-verdict
# checkbox is checked, or the real API call failed, or the reply came
# back in a shape we couldn't parse. Kept deliberately generic and
# free of any physics content, per the "never invent a physics fact"
# rule -- this is a safety-net line, not a real diagnosis.
# -----------------------------------------------------------------------
GENERIC_FALLBACK_RESPONSE = (
    "Diagnostic link unstable, Engineer. Trust the instruments in front "
    "of you and try that reasoning again."
)

# Short, plain instructions for the model. Kept intentionally brief so
# the input side of the call stays cheap too, not just the output side.
#
# PHASE 5 CHANGE: added a brief "ship's diagnostic AI" persona, and
# switched the requested output format from a single word to the
# two-line VERDICT / RESPONSE format described above -- still one call,
# still cheap, just structured so we can pull two things out of it.
SYSTEM_PROMPT = (
    "You are the ship's diagnostic AI aboard a research station -- "
    "friendly but precise, and you always address the student as "
    "'Engineer'. You will be given a question, the concept the student "
    "is expected to understand, and the student's one-sentence "
    "explanation. Judge ONLY the quality of their reasoning -- you must "
    "NEVER do any physics/chemistry math yourself and NEVER state or "
    "invent any specific number, formula, or fact; all real values come "
    "from elsewhere. "
    "Reply in EXACTLY this two-line format and nothing else:\n"
    "VERDICT: <resolved, thin, or wrong>\n"
    "RESPONSE: <1-2 sentences>\n"
    "If VERDICT is 'resolved', RESPONSE should be a short affirming line. "
    "If VERDICT is 'thin' or 'wrong', RESPONSE must ask a guiding "
    "Socratic question rather than giving the answer away."
)


def _get_client():
    """
    Creates the OpenAI client using the API key from your .env file.
    We build this fresh each call rather than at import time, so a
    missing/blank key raises a clear error only when someone actually
    tries to use it, not the moment the app starts up.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is missing or blank. Add it to your .env file."
        )
    return OpenAI(api_key=api_key)


def _extract_verdict(raw_text):
    """
    Takes whatever raw text the model returned and tries to pull out one
    of our three valid verdict words from it. This is the same defensive
    logic as Phase 4, just reused here.

    We do NOT just trust the model blindly, because even a good model can
    occasionally reply with something like "Resolved." (extra punctuation)
    or a whole sentence instead of one word. This function:
      1. Lowercases and strips whitespace/punctuation.
      2. Checks if the cleaned text IS one of our three valid words.
      3. As a fallback, looks for one of our three words as a whole word
         anywhere in a longer reply (in case the model added extra
         words). This uses a word-boundary check (\\b) so, for example,
         the word "think" is never mistaken for containing "thin".
      4. If more than one distinct verdict word shows up (genuinely
         ambiguous), or nothing matches at all, returns None so the
         caller can decide what to do (we default to "thin" -- see
         judge_explanation below).
    """
    if not raw_text:
        return None

    cleaned = raw_text.strip().lower().strip(".!?\"'")

    if cleaned in VALID_VERDICTS:
        return cleaned

    found = {
        verdict
        for verdict in VALID_VERDICTS
        if re.search(rf"\b{verdict}\b", cleaned)
    }

    if len(found) == 1:
        return found.pop()

    return None


def _parse_verdict_and_response(raw_text):
    """
    PHASE 5: NEW. Pulls BOTH the verdict word and the in-character
    dialogue line out of a single raw reply that should look like:

        VERDICT: resolved
        RESPONSE: Good work, Engineer. The readings check out.

    We use regular expressions with re.IGNORECASE and re.DOTALL so this
    still works even if the model changes capitalization slightly, adds
    a blank line, or wraps the response line onto multiple lines.

    Returns a tuple: (verdict_or_None, response_text_or_None).
    Neither value is guaranteed to be present -- the caller
    (judge_explanation) is responsible for defaulting each one
    independently if it's missing, exactly as the spec asks:
    "If parsing fails for either part" -- verdict and response are
    defaulted separately, not as an all-or-nothing pair.
    """
    if not raw_text:
        return None, None

    verdict = None
    verdict_match = re.search(r"VERDICT:\s*(\w+)", raw_text, re.IGNORECASE)
    if verdict_match:
        verdict = _extract_verdict(verdict_match.group(1))

    # If we couldn't find a labeled VERDICT: line at all, fall back to
    # scanning the whole raw reply for a valid verdict word, the same
    # way Phase 4 did. This keeps us robust even if the model forgets
    # the "VERDICT:" label but still says the word somewhere.
    if verdict is None:
        verdict = _extract_verdict(raw_text)

    response_text = None
    response_match = re.search(
        r"RESPONSE:\s*(.+)", raw_text, re.IGNORECASE | re.DOTALL
    )
    if response_match:
        candidate = response_match.group(1).strip()
        if candidate:
            response_text = candidate

    return verdict, response_text


def judge_explanation(question_prompt, expected_concept, student_explanation):
    """
    THE MAIN FUNCTION FOR THIS PHASE.

    Inputs:
      - question_prompt: the text of the question that was asked
      - expected_concept: the concept/answer we expect (e.g. "zero",
        "balanced", "conductivity") -- this is the "answer" field already
        stored in data/anomalies.json for that question
      - student_explanation: the sentence the student typed

    Returns a tuple: (verdict, in_character_response)
      - verdict is always exactly one of "resolved", "thin", "wrong".
      - in_character_response is always a non-empty string -- either the
        model's real 1-2 sentence dialogue, or (if that part of the
        parse failed) the hardcoded GENERIC_FALLBACK_RESPONSE.

    PHASE 5 CHANGE: this used to return just the verdict string. It now
    returns the (verdict, response) tuple described above. This function
    still makes exactly ONE API call, same as Phase 4 -- we did not add
    a second call to get the dialogue.

    This function DOES raise an exception for things like a missing API
    key, no internet, or a rate limit -- app.py is responsible for
    catching that exception and turning it into a graceful on-screen
    fallback, per the existing Phase 4 spec (unchanged in Phase 5).
    """
    client = _get_client()

    user_message = (
        f"Question: {question_prompt}\n"
        f"Expected concept: {expected_concept}\n"
        f"Student's explanation: {student_explanation}\n\n"
        "Reply with the two-line VERDICT / RESPONSE format described in "
        "your instructions."
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=MAX_TOKENS,
        temperature=0,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
    )

    raw_text = response.choices[0].message.content
    verdict, in_character_response = _parse_verdict_and_response(raw_text)

    # Default the VERDICT independently -- same safe default as Phase 4:
    # an unparseable/ambiguous verdict becomes "thin" rather than us
    # guessing "resolved" or "wrong".
    if verdict is None:
        verdict = "thin"

    # Default the RESPONSE independently -- if we couldn't confidently
    # pull a real dialogue line out of the reply, show the hardcoded
    # generic fallback line instead of a blank or broken message. Note
    # this is deliberately a SEPARATE check from the verdict default
    # above: it's possible to get a good verdict but a malformed/missing
    # response line, or vice versa.
    if not in_character_response:
        in_character_response = GENERIC_FALLBACK_RESPONSE

    return verdict, in_character_response


def mock_in_character_response():
    """
    PHASE 5: NEW. Used when the "Use mock verdict" checkbox is checked,
    or whenever we fall back to the mock verdict because the real API
    call failed. In both of those cases there was no real model reply,
    so there is nothing genuine to show -- we show this same generic,
    hardcoded, physics-fact-free line instead so app.py never has to
    show a blank message.
    """
    return GENERIC_FALLBACK_RESPONSE
