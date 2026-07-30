"""
render_anomaly_scene() renders scenes/anomaly_acene.html the same way
render_boot_scene()/render_command_center_scene() below render their
scenes: Three.js + GSAP are read from static/vendor/ and inlined as
<script> tags ahead of the scene's own markup, so nothing is ever
fetched from a CDN inside the iframe (per this project's no-CDN rule).

FAILURE HANDLING: if any of the three files (three.min.js, gsap.min.js,
scenes/anomaly_acene.html) is missing, unreadable, or empty, Python
catches that directly (it's the thing trying to open the files) and
falls back to a plain 2D description card instead of a blank iframe.
"""

import os

import streamlit.components.v1 as components

import ui.design_tokens as tokens
from ui.focal_objects import FOCAL_OBJECT_CONFIG

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


def _render_2d_fallback(description_text):
    """Shows the same dark/cyan "diagnostic terminal" styled 2D card as
    the JS-side fallback in anomaly_acene.html, but built with Streamlit
    markdown/CSS instead -- this copy is needed because this path runs
    when we never even got as far as handing anything to the browser.
    MILESTONE 4: description_text is now passed in per-anomaly instead of
    being hardcoded to vacuum_box's description."""
    components.html(
        f"""
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
              {description_text}
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


def _station_html(name, accent_hex, unlocked):
    """One station card's markup, matching the original hardcoded look,
    just with real data swapped in for name/color/lock-state."""
    if unlocked:
        border = accent_hex
        bg = "rgba(45,214,224,0.06)"
        label_color = accent_hex
        label = "UNLOCKED"
        text_color = "#e6f1f3"
    else:
        border = "#3a4650"
        bg = "rgba(255,255,255,0.03)"
        label_color = "#8aa0aa"
        label = "LOCKED"
        text_color = "#8aa0aa"
    return f"""
      <div class="cc-station" style="opacity:0;border:1px solid {border};border-radius:6px;padding:10px 16px;min-width:140px;background:{bg};">
        <div style="color:{label_color};font-size:12px;letter-spacing:1px;">{label}</div>
        <div style="color:{text_color};font-size:14px;margin-top:4px;">{name}</div>
      </div>"""


def render_command_center_scene(stations=None):
    """Stage: command_center.

    MILESTONE 3: stations is a list of dicts, one per chapter, each like
    {"name": ..., "accent_hex": "#2dd6e0", "unlocked": True/False}, built
    by app.py from data/anomalies.json's chapters + progress.json. If not
    given (e.g. some future caller), falls back to the original 3 mock
    stations so this never renders blank.
    """
    if not stations:
        stations = [
            {"name": "Fundamental Forces", "accent_hex": "#2dd6e0", "unlocked": True},
            {"name": "Energy & Heat", "accent_hex": "#f4a640", "unlocked": False},
            {"name": "Space-Time", "accent_hex": "#a06de0", "unlocked": False},
        ]
    stations_html = "".join(
        _station_html(s["name"], s["accent_hex"], s["unlocked"]) for s in stations
    )
    try:
        scene_html = _read_file(os.path.join(_SCENES_DIR, "command_center.html"))
        three_js = _read_file(os.path.join(_VENDOR_DIR, "three.min.js"))
        gsap_js = _read_file(os.path.join(_VENDOR_DIR, "gsap.min.js"))
        if not (three_js.strip() and gsap_js.strip() and scene_html.strip()):
            raise ValueError("One or more scene assets are empty.")
    except (OSError, ValueError):
        _render_intro_fallback("COMMAND CENTER", 420)
        return
    scene_html = scene_html.replace("__STATIONS_HTML__", stations_html)
    full_html = f"<script>{three_js}</script><script>{gsap_js}</script>" + scene_html
    components.html(full_html, height=420)


def render_anomaly_scene(anomaly_id, verdict=None):
    """Read scenes/anomaly_acene.html (the GENERIC reaction template, as of
    Milestone 4) and render it as a live 3D scene for the given anomaly_id,
    falling back to a 2D description if anything can't be read. See module
    docstring for the failure modes this covers.

    anomaly_id: one of the keys in ui/focal_objects.py's FOCAL_OBJECT_CONFIG
        (vacuum_box, sinking_stone, hot_cold_chairs, gps_clock_drift). Picks
        which focal object + idle motion + chapter accent color get baked
        into the shared template.
    verdict: one of "resolved" / "thin" / "wrong" / None. None means "no
        submission yet this visit" -- the scene stays neutral (just the
        idle motion). Baked into the HTML as a JS constant the scene reads
        on load; see scenes/anomaly_acene.html's header note for why this
        doesn't need any live Python<->iframe messaging.
    """
    config = FOCAL_OBJECT_CONFIG.get(anomaly_id)
    if config is None:
        # No live scene defined for this anomaly (shouldn't happen for the
        # 4 current anomalies, but never blank the screen if it does).
        _render_2d_fallback("No visual feed is configured for this anomaly yet.")
        return

    if FORCE_FALLBACK_FOR_TESTING:
        _render_2d_fallback(config["fallback_text"])
        return

    try:
        three_js = _read_file(os.path.join(_VENDOR_DIR, "three.min.js"))
        gsap_js = _read_file(os.path.join(_VENDOR_DIR, "gsap.min.js"))
        with open(SCENE_FILE_PATH, "r", encoding="utf-8") as scene_file:
            scene_html = scene_file.read()
        if not (three_js.strip() and gsap_js.strip() and scene_html.strip()):
            raise ValueError("One or more scene assets are empty.")
    except (OSError, ValueError):
        _render_2d_fallback(config["fallback_text"])
        return

    accent_hex = getattr(tokens, config["accent_token"])  # e.g. "#2dd6e0"
    scene_html = scene_html.replace("__REACTION_VERDICT__", verdict or "")
    scene_html = scene_html.replace("__ACCENT_HEX_JS__", "0x" + accent_hex.lstrip("#"))
    scene_html = scene_html.replace("__ACCENT_HEX_CSS__", accent_hex)
    scene_html = scene_html.replace("__FOCAL_SETUP_JS__", config["focal_setup_js"])
    scene_html = scene_html.replace("__IDLE_TICK_JS__", config["idle_tick_js"])
    full_html = f"<script>{three_js}</script><script>{gsap_js}</script>" + scene_html
    components.html(full_html, height=SCENE_HEIGHT_PX)
