"""
MILESTONE 5, Part C: the reusable Travel Transition -- ONE shared corridor
scene played between every real view change, same config-dict + shared-
HTML-template pattern as MENTOR_CORE_CONFIG/mentor_core.html. The streak
layout (position/width/timing) lives here, exactly once; accent_hex is
passed in per-call (like MENTOR_ACCENT) since the tint changes with
whichever chapter is relevant -- see ui/scene_viewer.py's
render_transition_scene() and app.py's _begin_transition().
"""

TRANSITION_CONFIG = {
    "corridor": [
        {"top": 18, "width": 46, "delay": 0.00, "duration": 0.55},
        {"top": 34, "width": 62, "delay": 0.05, "duration": 0.60},
        {"top": 50, "width": 38, "delay": 0.10, "duration": 0.55},
        {"top": 66, "width": 58, "delay": 0.04, "duration": 0.60},
        {"top": 82, "width": 44, "delay": 0.12, "duration": 0.55},
    ]
}


def _streak_html(streak, accent_hex):
    return (
        f'<div class="streak" style="top:{streak["top"]}%;width:{streak["width"]}%;'
        f'background:linear-gradient(90deg, transparent, {accent_hex}, transparent);" '
        f'data-delay="{streak["delay"]}" data-duration="{streak["duration"]}"></div>'
    )


def build_streaks_html(accent_hex, layout_key="corridor"):
    """Returns the streak divs for scenes/transition.html's __STREAKS_HTML__,
    tinted to accent_hex. Falls back to the "corridor" layout if an unknown
    layout_key is ever passed, so this never returns an empty scene."""
    layout = TRANSITION_CONFIG.get(layout_key, TRANSITION_CONFIG["corridor"])
    return "".join(_streak_html(s, accent_hex) for s in layout)
