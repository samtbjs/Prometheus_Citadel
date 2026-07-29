"""
Phase 7a — loads scenes/anomaly_acene.html and shows it inside the
Streamlit app.

WHY THIS IS ITS OWN FILE (instead of just adding code into app.py):
This is a self-contained, single-purpose helper -- "read a file, show it
in a component" -- with no dependency on any of the game logic in app.py.
Keeping it separate means app.py only needs one new line to use it, and
this file can be found/edited on its own later (e.g. in Phase 7b/7c)
without scrolling through app.py's Reasoning Streak Loop code.

WHAT THIS FILE DOES NOT DO (on purpose, per Phase 7a's scope):
- No animation logic -- that lives entirely inside the HTML file itself
  (or will, starting in Phase 7b).
- No fallback/error-handling for a missing or broken file -- that's
  Phase 7c. If the file is missing, this will raise a normal Python
  error, which is expected for this phase.
"""

import streamlit.components.v1 as components

# Where the scene file lives, relative to the project's root folder (the
# same folder app.py is in). NOTE: the filename below intentionally
# matches the existing typo ("acene" instead of "scene") -- this is not a
# mistake in this file, it's kept as-is on purpose so nothing else breaks.
SCENE_FILE_PATH = "scenes/anomaly_acene.html"

# A fixed pixel height for the 3D scene's box on the page. Three.js scenes
# rendered via components.html() don't auto-resize their height to fit
# content the way normal Streamlit elements do -- the iframe is always
# exactly this tall, so this number is the one thing to change if the
# scene ever looks too cramped or too tall on screen.
SCENE_HEIGHT_PX = 420


def render_anomaly_scene():
    """Read scenes/anomaly_acene.html from disk and render it as a live
    3D scene inside the Streamlit page.

    HOW THIS WORKS, IN PLAIN LANGUAGE:
    Streamlit normally only knows how to display its own built-in pieces
    (buttons, text boxes, etc). `components.html()` is Streamlit's escape
    hatch for showing ANY arbitrary webpage inside the app -- it creates
    an <iframe> (literally a small, sandboxed browser window embedded in
    the page) and loads whatever HTML text you hand it into that iframe.
    Here, we hand it the entire contents of scenes/anomaly_acene.html, so
    that file's own Three.js code runs inside the iframe and draws the
    3D box, completely independently of the rest of the Streamlit app.
    """
    with open(SCENE_FILE_PATH, "r", encoding="utf-8") as scene_file:
        scene_html = scene_file.read()

    components.html(scene_html, height=SCENE_HEIGHT_PX)
