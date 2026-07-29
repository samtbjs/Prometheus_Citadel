"""
Phase 7c — adds failure-safe fallback around the working Phase 7b scene.

WHY THIS IS ITS OWN FILE: unchanged from Phase 7a -- see history for that
reasoning. This phase only adds error-handling; it does not touch the
animation, camera, lighting, or box appearance from Phase 7b.

THE TWO FAILURE MODES THIS PHASE HANDLES (and why BOTH are needed):
1. PYTHON-SIDE failure: scenes/anomaly_acene.html is missing, unreadable,
   or empty. Python can detect this directly (it's the thing trying to
   open the file), so it's handled here with a plain try/except.
2. BROWSER-SIDE failure: the file reads fine in Python and gets handed
   to the iframe, but the browser then fails to download Three.js from
   its CDN (no internet, firewall, CDN outage, etc). Python has already
   finished its job by this point and has no way to see into the
   browser/iframe -- so this failure can ONLY be caught by JavaScript
   running inside the HTML file itself. That check lives in
   scenes/anomaly_acene.html (a setTimeout that looks for `THREE` being
   undefined and swaps in a 2D fallback if so).
Together, these two checks cover "the file itself is the problem" and
"the file is fine but the network inside the browser is the problem."
"""

import streamlit.components.v1 as components

SCENE_FILE_PATH = "scenes/anomaly_acene.html"
SCENE_HEIGHT_PX = 420

# ---------------------------------------------------------------------
# MANUAL TEST FLAG (Phase 7c) -- set this to True temporarily to force
# the Python-side fallback to show, without deleting/renaming the real
# scene file. REMEMBER TO SET IT BACK TO False WHEN YOU'RE DONE TESTING.
# ---------------------------------------------------------------------
FORCE_FALLBACK_FOR_TESTING = False


def _render_2d_fallback():
    """Shows the same dark/cyan "diagnostic terminal" styled 2D card as
    the JS-side fallback in anomaly_acene.html, but built with Streamlit
    markdown/CSS instead -- this copy is needed because this path runs
    when we never even got as far as handing anything to the browser."""
    components.html(
        """
        <div style="
            display:flex; align-items:center; justify-content:center;
            width:100%; height:100%; box-sizing:border-box; padding:24px;
            background:#05080a; font-family:monospace;
        ">
          <div style="
              border:1px solid #2dd6e0; border-radius:6px; padding:20px 24px;
              max-width:420px; color:#e6f1f3; text-align:center;
          ">
            <div style="color:#2dd6e0; font-weight:bold; letter-spacing:1px; margin-bottom:10px;">
              [ 3D VISUAL FEED OFFLINE ]
            </div>
            <div style="color:#8aa0aa; font-size:14px; line-height:1.5;">
              A box floats motionless in a vacuum chamber, with nothing touching it.
            </div>
          </div>
        </div>
        """,
        height=SCENE_HEIGHT_PX,
    )


def render_anomaly_scene():
    """Read scenes/anomaly_acene.html and render it as a live 3D scene,
    falling back to a 2D description if the file can't be read for any
    reason. See module docstring for the two failure modes this covers.
    """
    if FORCE_FALLBACK_FOR_TESTING:
        _render_2d_fallback()
        return

    try:
        with open(SCENE_FILE_PATH, "r", encoding="utf-8") as scene_file:
            scene_html = scene_file.read()
        if not scene_html.strip():
            raise ValueError("Scene file is empty.")
    except (OSError, ValueError):
        _render_2d_fallback()
        return

    components.html(scene_html, height=SCENE_HEIGHT_PX)
