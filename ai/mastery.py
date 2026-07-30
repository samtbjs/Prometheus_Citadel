"""
ai/mastery.py

PHASE 2 (this session): the mastery loop -- richer teaching BETWEEN
attempts on a wrong/thin answer. This module does NOT decide when an
anomaly clears (logic/streak_engine.py's streak rule is still the only
source of truth for that) -- it only decides what lesson to show after
a miss, and when to stop teaching and just reveal the answer.

STATE
-----
Per-anomaly mastery state lives inside the SAME progress dict that
already lives in st.session_state.progress (so it's automatically "in
st.session_state" the moment it's in that dict, and automatically
persisted to progress.json the next time the caller calls
streak_engine.save_progress() -- no new save path needed). It is kept
under a top-level "_mastery" key, keyed by anomaly_id, deliberately
SEPARATE from the existing per-anomaly dict that
update_anomaly_progress() overwrites -- so nothing here can ever be
wiped out by, or interfere with, the existing streak bookkeeping.

    progress["_mastery"][anomaly_id] = {
        "strategy_index": 0,
        "attempts_this_strategy": 0,
        "snares_seen": [],
    }

STRATEGY LADDER
----------------
4 rungs, 2 attempts each = 8 AI-taught lessons max (the hard cap this
session's spec asks for) before we deterministically reveal the answer
on attempt 9 -- no API call, guaranteed to terminate.
"""

import json

from ai.client import ask_arbiter

MAX_ATTEMPTS_PER_STRATEGY = 2
MASTERY_MAX_TOKENS = 200  # short single-lesson line; well under the 300 ceiling

STRATEGIES = [
    {
        "id": "analogy",
        "label": "Worked Analogy",
        "instruction": (
            "Teach using ONE short, concrete everyday analogy that mirrors "
            "the physics situation. Do not state any new number or formula."
        ),
    },
    {
        "id": "socratic",
        "label": "Guiding Question",
        "instruction": (
            "Teach by asking exactly one guiding Socratic question that "
            "nudges the student toward the correct concept, without "
            "stating the answer outright."
        ),
    },
    {
        "id": "contrast",
        "label": "Contrast Case",
        "instruction": (
            "Teach by briefly contrasting the student's likely "
            "misconception against what correct reasoning would look "
            "like, side by side, in 1-2 sentences."
        ),
    },
    {
        "id": "direct",
        "label": "Plain Restatement",
        "instruction": (
            "Teach with a direct, plain-language restatement of the "
            "correct reasoning in 1 short sentence. No jargon, no new facts."
        ),
    },
]

# Shown when the API call fails/parses badly, or when the app has no key.
# Deliberately generic and physics-fact-free -- never a substitute for real
# reasoning, just a safety net so the screen is never blank.
GENERIC_LESSON_FALLBACK = (
    "Diagnostic link unstable, Researcher -- re-read the last reading "
    "and try explaining it again in your own words."
)

SYSTEM_PROMPT = (
    "You are the ship's diagnostic AI tutor, addressing the student as "
    "'Researcher'. You will be given a question, the single correct "
    "concept/answer for it, optionally a hint describing the specific "
    "misconception the student seems to hold, and a teaching instruction "
    "naming which strategy to use. You must NEVER invent, calculate, or "
    "state any physics/chemistry number or formula that was not already "
    "given to you -- ground your lesson ONLY in the given concept/answer "
    "and hint. Follow the given teaching instruction exactly. "
    "Reply with ONLY a JSON object and nothing else, in exactly this "
    'shape: {"lesson": "<your 1-2 sentence lesson>"}'
)


def _default_state():
    return {"strategy_index": 0, "attempts_this_strategy": 0, "snares_seen": []}


def load_mastery_state(progress, anomaly_id):
    """Returns this anomaly's mastery state, or fresh defaults if none yet."""
    return dict(progress.get("_mastery", {}).get(anomaly_id, _default_state()))


def _save_mastery_state(progress, anomaly_id, state):
    """Writes the state into the progress dict in memory. Caller is still
    responsible for calling streak_engine.save_progress() to persist it,
    exactly like every other change to the progress dict already does."""
    progress.setdefault("_mastery", {})[anomaly_id] = state
    return progress


def reset_mastery_state(progress, anomaly_id):
    """Resets one anomaly's ladder back to rung 0. Call this whenever the
    student resolves the miss, or restarts the anomaly."""
    return _save_mastery_state(progress, anomaly_id, _default_state())


def _find_snare_hint(snare_id, known_snares):
    if not snare_id or snare_id == "none":
        return None
    for s in known_snares or []:
        if s.get("id") == snare_id:
            return s.get("hint")
    return None


def _get_lesson_text(question_prompt, expected_concept, snare_hint, strategy):
    """Makes ONE ask_arbiter() call for the current rung's lesson. Never
    raises -- any failure (missing key, network, bad JSON) falls back to
    the hardcoded generic line so the caller never has to catch anything."""
    hint_block = (
        f"Student's likely misconception: {snare_hint}\n"
        if snare_hint
        else "No specific misconception identified for this attempt.\n"
    )
    user_message = (
        f"Question: {question_prompt}\n"
        f"Correct concept/answer: {expected_concept}\n"
        f"{hint_block}"
        f"Teaching instruction (strategy: {strategy['label']}): "
        f"{strategy['instruction']}\n"
        'Reply with ONLY the JSON object described in your instructions.'
    )
    try:
        raw_text = ask_arbiter(
            system_prompt=SYSTEM_PROMPT,
            user_message=user_message,
            max_tokens=MASTERY_MAX_TOKENS,
            temperature=0,
        )
        cleaned = (raw_text or "").strip()
        # Models sometimes wrap JSON in ```...``` fences despite instructions.
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`").lstrip("json").strip()
        parsed = json.loads(cleaned)
        lesson = str(parsed.get("lesson", "")).strip()
        return lesson or GENERIC_LESSON_FALLBACK
    except Exception:
        return GENERIC_LESSON_FALLBACK


def record_attempt_and_get_lesson(
    progress, anomaly_id, question_prompt, expected_concept, verdict, snare_id, known_snares
):
    """
    THE MAIN ENTRY POINT for this phase. Call this once per ANALYZE click,
    right after the verdict ("resolved"/"thin"/"wrong") is known.

    - On "resolved": resets the ladder for this anomaly (a fresh miss
      later starts back at rung 0) and returns None -- no lesson needed.
    - On "thin"/"wrong": records the attempt, advances the rung after
      MAX_ATTEMPTS_PER_STRATEGY misses on the current one, and returns
      either:
        {"type": "lesson", "strategy_label": <str>, "text": <str>}
      or, once the ladder is exhausted (guaranteed within 8 lesson
      calls):
        {"type": "reveal", "strategy_label": "Answer Revealed", "text": <str>}
      The "reveal" case makes NO API call -- it deterministically states
      the already-known correct concept, so this can never loop forever
      regardless of what the model returns.

    Mutates `progress` in place (same dict as st.session_state.progress).
    Caller must still call streak_engine.save_progress(progress) after,
    exactly as it already does for the streak fields.
    """
    if verdict == "resolved":
        reset_mastery_state(progress, anomaly_id)
        return None

    state = load_mastery_state(progress, anomaly_id)

    if snare_id and snare_id != "none" and snare_id not in state["snares_seen"]:
        state["snares_seen"].append(snare_id)

    # This attempt is taught at the CURRENT rung -- decide whether to
    # advance only AFTER teaching it, so each rung actually gets its
    # full MAX_ATTEMPTS_PER_STRATEGY misses before moving on.
    state["attempts_this_strategy"] += 1
    ladder_exhausted = state["strategy_index"] >= len(STRATEGIES)

    if ladder_exhausted:
        _save_mastery_state(progress, anomaly_id, state)
        return {
            "type": "reveal",
            "strategy_label": "Answer Revealed",
            "text": (
                f"Let's settle it plainly, Researcher: the correct answer "
                f"is \"{expected_concept}\". Carry that forward to the "
                f"next reading."
            ),
        }

    strategy = STRATEGIES[state["strategy_index"]]
    snare_hint = _find_snare_hint(snare_id, known_snares)
    lesson_text = _get_lesson_text(question_prompt, expected_concept, snare_hint, strategy)

    # Now that this rung has been taught, advance for NEXT time if this
    # rung has hit its attempt cap.
    if state["attempts_this_strategy"] >= MAX_ATTEMPTS_PER_STRATEGY:
        state["strategy_index"] += 1
        state["attempts_this_strategy"] = 0

    _save_mastery_state(progress, anomaly_id, state)

    return {"type": "lesson", "strategy_label": strategy["label"], "text": lesson_text}
