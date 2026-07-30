import json
import os

# ---------------------------------------------------------------------------
# PHASE 2: Where our data files live.
#
# This file (streak_engine.py) sits inside the "logic" folder. The data files
# (anomalies.json and progress.json) sit inside the "data" folder, which is a
# sibling of "logic" — both live directly inside the main project folder.
#
# So starting from this file's location, we go "up one level" (out of logic/)
# and then "into data/". Building the path this way means it will work no
# matter which folder you happen to run the app from.
# ---------------------------------------------------------------------------
_THIS_FILE_DIR = os.path.dirname(os.path.abspath(__file__))      # .../prometheus_lab/logic
_PROJECT_ROOT = os.path.dirname(_THIS_FILE_DIR)                   # .../prometheus_lab
DATA_DIR = os.path.join(_PROJECT_ROOT, "data")
ANOMALIES_PATH = os.path.join(DATA_DIR, "anomalies.json")
PROGRESS_PATH = os.path.join(DATA_DIR, "progress.json")


def _load_anomalies_file():
    """Reads the whole data/anomalies.json file (chapters + anomalies)."""
    with open(ANOMALIES_PATH, "r") as f:
        return json.load(f)


def load_anomalies():
    """
    Returns the FLAT dict of anomalies, keyed by anomaly id (like
    "vacuum_box"), each with "name", "description", and "questions" --
    exactly the same shape every existing caller already expects.
    (MILESTONE 3: anomalies.json is now nested under a "chapters" key
    and an "anomalies" key on disk, but this function unwraps that so
    nothing that already reads load_anomalies() as a flat dict breaks.)
    """
    return _load_anomalies_file()["anomalies"]


def load_chapters():
    """
    MILESTONE 3: Returns the "chapters" dict from anomalies.json. Each
    chapter has a "name", an "accent_token" (a name to look up in
    ui/design_tokens.py -- never a hardcoded hex color here), an
    "unlocks_after" (the previous chapter's id, or None if it's always
    unlocked), and a list of "anomalies" (ids belonging to that chapter).
    """
    return _load_anomalies_file()["chapters"]


def is_chapter_unlocked(chapter_id, chapters, progress):
    """
    A chapter is unlocked if its "unlocks_after" is None (always-unlocked,
    e.g. mechanics), OR every anomaly belonging to the PREVIOUS chapter has
    been cleared at least once (per the existing get_anomaly_progress data
    -- this does not invent a second progress system).
    """
    prereq_id = chapters[chapter_id]["unlocks_after"]
    if prereq_id is None:
        return True
    prereq_anomalies = chapters[prereq_id]["anomalies"]
    return all(
        get_anomaly_progress(progress, aid)["cleared"]
        for aid in prereq_anomalies
    )


def load_progress():
    """
    Reads data/progress.json from disk and returns it as a Python dictionary.
    If the file is empty or doesn't exist yet, we return an empty dictionary
    instead of crashing, since that just means "no progress saved yet".
    """
    if not os.path.exists(PROGRESS_PATH) or os.path.getsize(PROGRESS_PATH) == 0:
        return {}
    with open(PROGRESS_PATH, "r") as f:
        return json.load(f)


def save_progress(progress):
    """
    Writes the given progress dictionary back out to data/progress.json,
    overwriting whatever was there before. This is what makes your streak
    survive a Streamlit reload.
    """
    with open(PROGRESS_PATH, "w") as f:
        json.dump(progress, f, indent=2)


def get_anomaly_progress(progress, anomaly_id):
    """
    Looks up saved progress for one specific Anomaly. If there isn't any yet
    (e.g. you've never played this Anomaly before), returns fresh defaults:
    starting on question 0, with a streak of 0, not yet cleared.
    """
    return progress.get(
        anomaly_id,
        {"question_index": 0, "streak": 0, "cleared": False},
    )


def update_anomaly_progress(progress, anomaly_id, question_index, streak, cleared):
    """
    Updates the progress dictionary in memory for one Anomaly. This does NOT
    write to disk by itself — call save_progress() afterward to persist it.
    """
    progress[anomaly_id] = {
        "question_index": question_index,
        "streak": streak,
        "cleared": cleared,
    }
    return progress


def check_answer(questions, question_index, student_answer):
    """Very simple check — does the student's answer contain the expected keyword?"""
    correct_answer = questions[question_index]["answer"]
    return correct_answer.lower() in student_answer.lower()


def mock_tag_explanation(tag_choice):
    """
    Phase 1/2 fake the AI verdict — you pick it from a dropdown instead of
    calling a real AI. tag_choice will be one of: 'resolved', 'thin', 'wrong'.
    """
    return tag_choice


def update_streak(current_streak, tag):
    """
    Returns the new streak count based on the verdict tag.

    PHASE 4 BUG FIX:
    Previously, "thin" and "wrong" were both treated as a full reset to 0.
    That was wrong. The correct behavior is:
      - "resolved"        -> streak goes UP by 1 (clearly understood it)
      - "thin"            -> streak stays THE SAME (not confidently right,
                              not confidently wrong -- so we don't punish
                              or reward it, we just ask again)
      - "wrong"/"wrong idea" -> streak resets to 0 (misunderstanding)
    """
    if tag == "resolved":
        return current_streak + 1
    elif tag == "thin":
        return current_streak  # unchanged
    else:
        return 0  # "wrong" (or "wrong idea") resets the streak


def is_anomaly_cleared(streak):
    return streak >= 2


def debug_force_clear_chapter(progress, chapter):
    """
    DEBUG-ONLY (only ever called from behind ?debug=1): marks every
    anomaly in the given chapter dict as cleared, so you can instantly
    test a chapter's unlocked/locked state without grinding through the
    real questions. Does not touch any anomaly NOT in this chapter.
    """
    for aid in chapter["anomalies"]:
        update_anomaly_progress(progress, aid, 0, 2, True)
    return progress


def debug_reset_progress():
    """DEBUG-ONLY: wipes all saved progress back to a fresh save."""
    save_progress({})
    return {}
