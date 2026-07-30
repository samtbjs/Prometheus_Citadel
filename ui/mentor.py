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
