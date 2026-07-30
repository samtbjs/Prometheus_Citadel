"""
MILESTONE 5 (Part A/B): fixed identity + flavor text for the facility's
diagnostic AI mentor. Everything here is STATIC text, not a live API call
-- the Debrief is a UI moment, not a grading moment. ai/tutor.py's live
resolved/thin/wrong verdict + in-run dialogue logic is untouched.
"""

MENTOR_NAME = "ARBITER"
MENTOR_FLAVOR_LINE = "Continuity noted. Proceeding to next directive."

# One fixed debrief line per anomaly, in ARBITER's voice. Shown once, the
# moment an anomaly is newly cleared -- see app.py's ANALYZE handler and
# ui/scene_viewer.py's render_debrief_scene().
DEBRIEF_LINES = {
    "vacuum_box": "Force accounted for. The chamber holds no exceptions to Newton, only ones you hadn't found yet.",
    "sinking_stone": "Terminal velocity confirmed. Constant is not the same as harmless.",
    "hot_cold_chairs": "Thermal equilibrium restored to your model, if not to the room.",
    "gps_clock_drift": "Relativity logged and reconciled. The clocks were never wrong — your frame was incomplete.",
}
DEBRIEF_LINE_FALLBACK = "Anomaly stabilized. Filed for facility record."


def debrief_line_for(anomaly_id):
    return DEBRIEF_LINES.get(anomaly_id, DEBRIEF_LINE_FALLBACK)


# MILESTONE 6: Mission Briefing lines, one 2-3 line briefing per chapter,
# in ARBITER's same clinical voice as DEBRIEF_LINES above. Shown once per
# chapter per session by app.py, before that chapter's anomaly menu.
BRIEFING_LINES = {
    "mechanics": [
        "Structural anomaly logged in this wing: force balances refusing to close.",
        "Objects here behave as though Newton's laws are negotiable. They are not.",
        "Find where the accounting fails, then correct it.",
    ],
    "thermal": [
        "Thermal drift flagged across this wing's chambers.",
        "Two bodies, one room, no agreement on temperature. That should have resolved by now.",
        "Trace where the heat is actually flowing, and why it stopped.",
    ],
    "quantum": [
        "Reference-frame anomaly detected in this wing.",
        "The clocks here disagree with each other. Each one is still correct — for its own frame.",
        "Reconcile them. Do not assume a single universal clock.",
    ],
}
BRIEFING_LINES_FALLBACK = ["Anomaly signatures detected in this wing. Proceed with standard protocol."]


def briefing_lines_for(chapter_id):
    return BRIEFING_LINES.get(chapter_id, BRIEFING_LINES_FALLBACK)
