"""
ai/tutor.py

PHASE 6 (this session): route through the one door, add snare tagging.

WHAT CHANGED FROM PHASE 5
--------------------------------------------------------------------------
1. This file no longer imports `OpenAI` or builds its own client -- it
   now calls `ai.client.ask_arbiter()` for the actual API request. All
   behavior and the `(verdict, in_character_response)` return signature
   of `judge_explanation()` are UNCHANGED.
2. The same single API call now asks for a THIRD line, SNARE, so we can
   tag which known misconception (if any) the student's explanation
   matches. This is parsed and defaulted independently, exactly like
   VERDICT and RESPONSE already were -- a missing/garbled/unmatched
   SNARE line never affects the verdict or response. The snare id is
   stored in `st.session_state["last_snare_id"]` for now; there is no
   UI for it yet (that's a later phase).

IMPORTANT SAFETY DETAILS (unchanged from Phase 5, still true here):
  - max_tokens is capped at 300 for the WHOLE call (verdict + dialogue
    + snare, together).
  - The AI is never allowed to invent a physics number, formula, or
    fact. It only reacts to right/vague/wrong, asks guiding questions,
    and (new) points at a misconception id from a fixed list we give
    it -- it never invents a new misconception of its own.
"""

import re

import streamlit as st

from ai.client import ask_arbiter

# The three, and ONLY three, verdict values this app understands anywhere.
VALID_VERDICTS = {"resolved", "thin", "wrong"}

# Used when no known snare matches, or the SNARE line is missing/garbled.
DEFAULT_SNARE = "none"

# Keep this well within the 250-300 token range specified. This is a hard
# ceiling on how long the model's ENTIRE reply (verdict + dialogue +
# snare, combined) is allowed to be -- the main lever for controlling API
# cost per call. Not raised for this session despite the extra SNARE line.
MAX_TOKENS = 300

# -----------------------------------------------------------------------
# Shown on screen any time we can't get (or can't trust) a real
# in-character line from the model -- either because the mock-verdict
# checkbox is checked, or the real API call failed, or the reply came
# back in a shape we couldn't parse. Kept deliberately generic and free
# of any physics content, per the "never invent a physics fact" rule --
# this is a safety-net line, not a real diagnosis.
# -----------------------------------------------------------------------
GENERIC_FALLBACK_RESPONSE = (
    "Diagnostic link unstable, Researcher. Trust the instruments in front "
    "of you and try that reasoning again."
)

# Short, plain instructions for the model. Kept intentionally brief so the
# input side of the call stays cheap too, not just the output side.
#
# THIS SESSION'S CHANGE: added the optional SNARE line to the requested
# output format -- still one call, still cheap, just one more thing we
# pull out of it.
SYSTEM_PROMPT = (
    "You are the ship's diagnostic AI aboard a research station -- "
    "friendly but precise, and you always address the student as "
    "'Researcher'. You will be given a question, the concept the student "
    "is expected to understand, the student's one-sentence explanation, "
    "and (optionally) a short list of known misconceptions ('snares') for "
    "this question, each with an id and a one-line hint. Judge ONLY the "
    "quality of their reasoning -- you must NEVER do any physics/chemistry "
    "math yourself and NEVER state or invent any specific number, "
    "formula, or fact; all real values come from elsewhere. You must "
    "NEVER invent a new misconception id -- only use one from the list "
    "you are given, or 'none'. "
    "Reply in EXACTLY this three-line format and nothing else:\n"
    "VERDICT: <resolved, thin, or wrong>\n"
    "RESPONSE: <1-2 sentences>\n"
    "SNARE: <the id of the ONE listed misconception the explanation "
    "matches, or 'none'>\n"
    "If VERDICT is 'resolved', RESPONSE should be a short affirming line "
    "and SNARE should be 'none'. If VERDICT is 'thin' or 'wrong', "
    "RESPONSE must ask a guiding Socratic question rather than giving the "
    "answer away, and SNARE should name a listed misconception id only if "
    "it clearly matches -- otherwise 'none'."
)


def _extract_verdict(raw_text):
    """
    Takes whatever raw text the model returned and tries to pull out one
    of our three valid verdict words from it. Unchanged from Phase 5.

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


def _parse_reply(raw_text):
    """
    Pulls VERDICT, RESPONSE, and SNARE out of a single raw reply that
    should look like:

        VERDICT: resolved
        RESPONSE: Good work, Researcher. The readings check out.
        SNARE: none

    Uses re.IGNORECASE and re.DOTALL so this still works even if the
    model changes capitalization slightly, adds a blank line, or wraps
    the response line onto multiple lines.

    Returns a tuple: (verdict_or_None, response_text_or_None,
    snare_id_or_None). None of the three values is guaranteed to be
    present -- the caller (judge_explanation) defaults each one
    independently, exactly as it already did for verdict/response in
    Phase 5. A missing/garbled SNARE line never affects verdict or
    response, and vice versa.
    """
    if not raw_text:
        return None, None, None

    verdict = None
    verdict_match = re.search(r"VERDICT:\s*(\w+)", raw_text, re.IGNORECASE)
    if verdict_match:
        verdict = _extract_verdict(verdict_match.group(1))

    # If we couldn't find a labeled VERDICT: line at all, fall back to
    # scanning the whole raw reply for a valid verdict word.
    if verdict is None:
        verdict = _extract_verdict(raw_text)

    response_text = None
    # Stop RESPONSE capture at a following SNARE: line (if present) so it
    # doesn't swallow the snare line too; otherwise capture to the end.
    response_match = re.search(
        r"RESPONSE:\s*(.+?)(?:\n\s*SNARE:|\Z)", raw_text, re.IGNORECASE | re.DOTALL
    )
    if response_match:
        candidate = response_match.group(1).strip()
        if candidate:
            response_text = candidate

    snare_id = None
    snare_match = re.search(r"SNARE:\s*([\w\-]+)", raw_text, re.IGNORECASE)
    if snare_match:
        candidate = snare_match.group(1).strip().lower().strip(".!?\"'")
        if candidate:
            snare_id = candidate

    return verdict, response_text, snare_id


def _record_snare(snare_id):
    """
    Stores the most recent snare id in session state for now -- there is
    no UI for it yet (that's a later phase). Wrapped in try/except so
    this module never crashes if it's ever called outside a real
    Streamlit script run (e.g. a future test harness).
    """
    try:
        st.session_state["last_snare_id"] = snare_id
    except Exception:
        pass


def judge_explanation(
    question_prompt, expected_concept, student_explanation, known_snares=None
):
    """
    THE MAIN FUNCTION FOR THIS PHASE.

    Inputs:
      - question_prompt: the text of the question that was asked
      - expected_concept: the concept/answer we expect (e.g. "zero",
        "balanced", "conductivity") -- this is the "answer" field already
        stored in data/anomalies.json for that question
      - student_explanation: the sentence the student typed
      - known_snares: OPTIONAL list of {"id", "name", "hint"} dicts from
        that question's "known_snares" field in anomalies.json. Defaults
        to an empty list, so existing callers that don't pass this still
        work exactly as before -- SNARE will just always default to
        "none" in that case.

    Returns a tuple: (verdict, in_character_response) -- UNCHANGED from
    Phase 5. verdict is always exactly one of "resolved", "thin",
    "wrong". in_character_response is always a non-empty string.

    As a SIDE EFFECT, this also stores the tagged snare id (or "none")
    in st.session_state["last_snare_id"]. This does not change the
    return signature and has no visible effect on screen yet.

    This function still makes exactly ONE API call. It DOES raise an
    exception for things like a missing API key, no internet, or a rate
    limit -- app.py is responsible for catching that and turning it into
    a graceful on-screen fallback, unchanged from before.
    """
    known_snares = known_snares or []

    if known_snares:
        snare_lines = "\n".join(
            f"- {s['id']}: {s['hint']}" for s in known_snares
        )
        snare_block = (
            f"Known misconceptions for this question:\n{snare_lines}\n\n"
        )
    else:
        snare_block = "No known misconceptions are listed for this question.\n\n"

    user_message = (
        f"Question: {question_prompt}\n"
        f"Expected concept: {expected_concept}\n"
        f"Student's explanation: {student_explanation}\n\n"
        f"{snare_block}"
        "Reply with the three-line VERDICT / RESPONSE / SNARE format "
        "described in your instructions."
    )

    raw_text = ask_arbiter(
        system_prompt=SYSTEM_PROMPT,
        user_message=user_message,
        max_tokens=MAX_TOKENS,
        temperature=0,
    )

    verdict, in_character_response, snare_id = _parse_reply(raw_text)

    # Default the VERDICT independently -- same safe default as before:
    # an unparseable/ambiguous verdict becomes "thin" rather than us
    # guessing "resolved" or "wrong".
    if verdict is None:
        verdict = "thin"

    # Default the RESPONSE independently -- if we couldn't confidently
    # pull a real dialogue line out of the reply, show the hardcoded
    # generic fallback line instead of a blank or broken message.
    if not in_character_response:
        in_character_response = GENERIC_FALLBACK_RESPONSE

    # Default (and validate) the SNARE independently -- never trust the
    # model to only use ids we actually listed. Anything that isn't a
    # known id for this question becomes "none".
    known_ids = {s["id"] for s in known_snares}
    if snare_id not in known_ids:
        snare_id = DEFAULT_SNARE

    _record_snare(snare_id)

    return verdict, in_character_response


def mock_in_character_response():
    """
    Used when the "Use mock verdict" checkbox is checked, or whenever we
    fall back to the mock verdict because the real API call failed. In
    both cases there was no real model reply, so we show this same
    generic, hardcoded, physics-fact-free line instead. Also records
    "none" as the snare for this submission, since there was no real
    tagging to report.
    """
    _record_snare(DEFAULT_SNARE)
    return GENERIC_FALLBACK_RESPONSE
