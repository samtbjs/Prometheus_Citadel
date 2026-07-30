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
