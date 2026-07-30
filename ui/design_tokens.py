"""
Single source of truth for colors/spacing used by the new intro scenes
(Build Spec §4). Milestone 1 only pulls in the Chapter-1 cyan accent —
amber/violet chapter accents are defined here now so Milestone 4 doesn't
need to touch this file again, but nothing uses them yet.
"""

BG_VOID = "#05080a"
TEXT_MAIN = "#e6f1f3"
TEXT_DIM = "#8aa0aa"

CHAPTER_1_ACCENT = "#2dd6e0"   # Mechanics — cyan (used in Milestone 1)
CHAPTER_2_ACCENT = "#f4a640"   # Thermal — amber (not used yet)
CHAPTER_3_ACCENT = "#a06de0"   # Quantum — violet (not used yet)

# MILESTONE 5: the mentor AI's core visual uses this neutral steel/white
# accent rather than any single chapter color, since ARBITER is a
# facility-wide presence, not tied to one chapter.
MENTOR_ACCENT = "#c9d6da"

FONT_STACK = "'Share Tech Mono', 'Courier New', monospace"
DISPLAY_FONT_STACK = "'Orbitron', 'Share Tech Mono', sans-serif"

# ---------------------------------------------------------------------
# VISUAL REDESIGN: full design-system layer. Nothing above this line
# changes meaning or is removed -- existing imports/getattr lookups
# (app.py, ui/scene_viewer.py, chapter["accent_token"] strings in
# data/anomalies.json) keep working exactly as before. Everything below
# is new, additive vocabulary for the "premium sci-fi facility" restyle
# (ui/styles.py + mission-card markup in ui/scene_viewer.py read these).
# ---------------------------------------------------------------------
PRIMARY = CHAPTER_1_ACCENT          # cyan -- primary interactive accent
SECONDARY = CHAPTER_3_ACCENT        # violet -- secondary/quantum accent
ACCENT = CHAPTER_1_ACCENT
WARNING = "#f4913a"                 # orange -- warning states, "thin" verdict
SUCCESS = "#4ade80"
ERROR = "#f0475a"

BACKGROUND = BG_VOID
SURFACE = "rgba(255, 255, 255, 0.035)"       # glass panel fill
SURFACE_RAISED = "rgba(255, 255, 255, 0.06)"  # slightly brighter glass (hover/selected)
BORDER = "rgba(45, 214, 224, 0.28)"
BORDER_MUTED = "rgba(255, 255, 255, 0.12)"
GLOW = "rgba(45, 214, 224, 0.55)"
GLOW_WARNING = "rgba(244, 145, 58, 0.55)"

TEXT = TEXT_MAIN
TEXT_MUTED = TEXT_DIM
