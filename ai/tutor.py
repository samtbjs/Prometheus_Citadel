"""
ai/tutor.py

PHASE 4: The real AI verdict call.

WHAT THIS FILE DOES, IN PLAIN ENGLISH
--------------------------------------------------------------------------
Up until now, "app.py" faked the AI's judgment with a dropdown menu where
YOU picked "resolved" / "thin" / "wrong" yourself. This file replaces that
fake dropdown with a real call to OpenAI's GPT-4o mini model.

We send the model three things:
  1. The question that was asked (the "prompt")
  2. The concept/answer we expect the student to have understood
  3. The student's own one-sentence written explanation

The model's ONLY job is to read the explanation and decide whether it
shows the student truly understands the concept. It is NOT allowed to do
any physics math itself (that's handled elsewhere, in physics_calc.py) --
it's purely judging the QUALITY of the written reasoning.

We ask the model to answer with exactly one word: resolved, thin, or
wrong. Since we can never 100% guarantee a model will follow instructions
perfectly, we also carefully check ("validate") whatever comes back. If
the response is anything other than those three exact words, we treat it
as "thin" instead of crashing the app or trusting a weird answer.

IMPORTANT SAFETY DETAIL: max_tokens is capped at 300 (between the
250-300 range you asked for) on every single call, to keep costs
predictable and small.
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
# hard ceiling on how long the model's reply is allowed to be, which is
# the main lever for controlling API cost per call.
MAX_TOKENS = 300

# Short, plain instructions for the model. Kept intentionally brief so
# the input side of the call stays cheap too, not just the output side.
SYSTEM_PROMPT = (
    "You are a strict but fair physics/chemistry tutor. You will be given "
    "a question, the concept the student is expected to understand, and "
    "the student's one-sentence explanation. Judge ONLY the quality of "
    "their reasoning -- do not do any math yourself. "
    "Reply with EXACTLY ONE WORD and nothing else, no punctuation: "
    "'resolved' if the explanation clearly shows correct understanding, "
    "'thin' if it's vague, incomplete, or only partially right, or "
    "'wrong' if it shows a clear misunderstanding."
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
    of our three valid verdict words from it.

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


def judge_explanation(question_prompt, expected_concept, student_explanation):
    """
    THE MAIN FUNCTION THIS PHASE ADDS.

    Inputs:
      - question_prompt: the text of the question that was asked
      - expected_concept: the concept/answer we expect (e.g. "zero",
        "balanced", "conductivity") -- this is the "answer" field already
        stored in data/anomalies.json for that question
      - student_explanation: the sentence the student typed

    Returns: one of "resolved", "thin", or "wrong" -- always exactly one
    of these three strings, never anything else. This function DOES raise
    an exception for things like a missing API key, no internet, or a
    rate limit -- app.py is responsible for catching that exception and
    turning it into a graceful on-screen fallback, per Phase 4 spec.
    """
    client = _get_client()

    user_message = (
        f"Question: {question_prompt}\n"
        f"Expected concept: {expected_concept}\n"
        f"Student's explanation: {student_explanation}\n\n"
        "One word only: resolved, thin, or wrong."
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
    verdict = _extract_verdict(raw_text)

    # If we couldn't confidently parse a valid verdict out of the
    # response, default to "thin" rather than guessing "resolved" or
    # "wrong" -- this keeps the app safe from a garbled AI reply ever
    # over/under-crediting the student.
    if verdict is None:
        return "thin"

    return verdict
