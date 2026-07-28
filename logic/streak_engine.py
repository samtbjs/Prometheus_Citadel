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


def load_anomalies():
    """
    Reads data/anomalies.json from disk and returns it as a Python dictionary.
    Each key is an Anomaly's id (like "vacuum_box"), and each value has a
    "name", a "description", and a list of "questions".
    """
    with open(ANOMALIES_PATH, "r") as f:
        return json.load(f)


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
    """Returns the new streak count based on the verdict tag."""
    if tag == "resolved":
        return current_streak + 1
    else:
        return 0  # thin or wrong resets the streak


def is_anomaly_cleared(streak):
    return streak >= 2
