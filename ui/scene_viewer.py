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

import os

import streamlit.components.v1 as components

_THIS_FILE_DIR = os.path.dirname(os.path.abspath(__file__))       # .../prometheus_lab/ui
_PROJECT_ROOT = os.path.dirname(_THIS_FILE_DIR)                    # .../prometheus_lab
SCENE_FILE_PATH = os.path.join(_PROJECT_ROOT, "scenes", "anomaly_acene.html")
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


# ---------------------------------------------------------------------
# MILESTONE 1 — opening scene (Facility Boot Sequence -> Command Center).
# Everything below is new and does not alter anything above this line.
#
# Three.js/GSAP are vendored locally (static/vendor/) per the Build Spec
# no-CDN requirement. components.html() renders each scene inside a
# sandboxed iframe with no access to the local filesystem, so the vendor
# files can't be loaded via a plain <script src="..."> pointed at disk --
# instead we read their contents once and inline them as <script> blocks
# ahead of the scene's own markup/JS.
# ---------------------------------------------------------------------
_VENDOR_DIR = os.path.join(_PROJECT_ROOT, "static", "vendor")
_SCENES_DIR = os.path.join(_PROJECT_ROOT, "scenes")


def _read_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _render_intro_fallback(label, height):
    """Plain-CSS stand-in shown if a vendor file or scene file is missing
    or unreadable, so a broken asset never shows a blank iframe."""
    components.html(
        f"""
        <div style="display:flex;align-items:center;justify-content:center;
            width:100%;height:100%;box-sizing:border-box;background:#05080a;
            font-family:monospace;">
          <div style="border:1px solid #2dd6e0;border-radius:6px;
              padding:20px 24px;color:#e6f1f3;text-align:center;">
            <div style="color:#2dd6e0;font-weight:bold;letter-spacing:1px;">
              [ {label} — VISUAL FEED OFFLINE ]
            </div>
          </div>
        </div>
        """,
        height=height,
    )


def _render_vendored_scene(scene_filename, label, height=420):
    """Inlines static/vendor/three.min.js + gsap.min.js ahead of a scene
    HTML file from scenes/, then renders it via components.html. Falls
    back to a 2D placeholder if any file is missing/unreadable."""
    try:
        three_js = _read_file(os.path.join(_VENDOR_DIR, "three.min.js"))
        gsap_js = _read_file(os.path.join(_VENDOR_DIR, "gsap.min.js"))
        scene_html = _read_file(os.path.join(_SCENES_DIR, scene_filename))
        if not (three_js.strip() and gsap_js.strip() and scene_html.strip()):
            raise ValueError("One or more scene assets are empty.")
    except (OSError, ValueError):
        _render_intro_fallback(label, height)
        return

    full_html = f"<script>{three_js}</script><script>{gsap_js}</script>" + scene_html
    components.html(full_html, height=height)


def render_boot_scene():
    """Stage: boot — the power-core-igniting opening moment."""
    _render_vendored_scene("boot.html", "BOOT SEQUENCE", height=420)


def render_command_center_scene():
    """Stage: command_center — hardcoded/mock 3-chapter station list,
    no anomalies.json read yet (per Milestone 1 mock-data requirement)."""
    _render_vendored_scene("command_center.html", "COMMAND CENTER", height=420)


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
