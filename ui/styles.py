"""
Phase 6 — Visual identity for Prometheus Lab.

This file ONLY injects CSS into the page. It does not touch any game logic,
session_state keys, or file structure. app.py calls inject_custom_css() once,
near the top, and everything below just changes how existing Streamlit
elements LOOK.

DESIGN NOTES (so future-you remembers the reasoning):

Palette — "diagnostic terminal on a dark ship console":
  - Cyan/teal accent (#2dd6e0) for anything "active" or informational:
    titles, the streak HUD, borders, focus states, primary buttons.
  - Amber (#fbbf24) is reserved for "thin"/warning states.
  - Green (#4ade80) and red (#f87171) stay green=resolved, red=wrong,
    matching normal traffic-light expectations so nothing feels backwards.
  - Background stays Streamlit's own near-black so we're not fighting the
    theme; we just add slightly-lighter "panel" surfaces on top of it for
    cards/boxes, which is what makes things read as distinct UI elements
    instead of plain text on a void.

Fonts — a two-font pairing pulled from Google Fonts:
  - "Orbitron" (a geometric, techy display face) for the big/short text:
    the app title, the Anomaly's terminal-readout heading, and the streak
    number in the HUD. It's what sells the "sci-fi console" feel.
  - "Share Tech Mono" (a monospace terminal face) for everything else:
    body copy, buttons, labels, and the feedback/log messages. Monospace
    reinforces the "diagnostic readout" feeling without being hard to read.
  Both are loaded via an @import at the top of the CSS block.

FRAGILITY WARNING (read this if something doesn't render right):
  Streamlit doesn't give every element a public, guaranteed-stable CSS
  hook. The selectors below mostly use `data-testid="..."` attributes,
  which Streamlit itself uses for automated testing and tends to keep
  stable across versions (this was true as of Streamlit 1.32+, which is
  what this project targets). The two selectors most likely to break on
  a future Streamlit upgrade are:
    1. `[data-testid="stAlert"]` — this is the container for
       st.info/success/warning/error. We deliberately do NOT override
       its background color — Streamlit already tints info/success/
       warning/error differently out of the box, and we don't want to
       accidentally make two different verdict types look identical.
       We only add the "card" chrome (border, radius, shadow, font)
       on top of whatever color Streamlit already applied. If a future
       Streamlit version changes how it colors alerts, our card styling
       will still apply, but the color nuance is up to Streamlit itself.
    2. The global `h3` styling for the "terminal readout" look. Right now
       app.py only calls st.subheader() in one place (the Anomaly
       question), so styling all h3 elements is safe. If a later phase
       adds another st.subheader() elsewhere, it will pick up this same
       look too -- which is probably fine, but worth remembering.
  If anything looks unstyled after you update Streamlit, open your
  browser's dev tools (F12), click an element, and check whether its
  `data-testid` attribute still matches what's referenced below.
"""

import streamlit as st

from ui.design_tokens import BG_VOID, TEXT_MAIN, TEXT_DIM, CHAPTER_1_ACCENT, WARNING, SECONDARY

# NOTE (this milestone): styles.py now reads its palette from
# design_tokens.py instead of hardcoding the same hex values a second
# time, so there's one single source of truth. Chapter-2/3 accents in
# design_tokens.py stay unused here on purpose -- only Chapter 1 (cyan)
# is in scope right now.
_ROOT_VARS = f"""
:root {{
    --accent: {CHAPTER_1_ACCENT};
    --accent-glow: rgba(45, 214, 224, 0.55);
    --accent-dim: rgba(45, 214, 224, 0.18);
    --panel-bg: rgba(255, 255, 255, 0.035);
    --panel-border: rgba(45, 214, 224, 0.28);
    --secondary: {SECONDARY};
    --success: #4ade80;
    --warning: {WARNING};
    --warning-glow: rgba(244, 145, 58, 0.5);
    --error: #f0475a;
    --text-main: {TEXT_MAIN};
    --text-dim: {TEXT_DIM};
    --bg-void: {BG_VOID};
    --surface: rgba(255, 255, 255, 0.04);
    --surface-raised: rgba(255, 255, 255, 0.07);
    --blur: blur(14px);
}}
"""

CUSTOM_CSS = """
<style>

/* ---- Fonts ---------------------------------------------------------- */
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@600;800&family=Share+Tech+Mono&display=swap');

""" + _ROOT_VARS + """

/* ---- Cleanup item 2: hide Streamlit's own dev toolbar (Deploy button,
   hamburger menu, "Made with Streamlit" footer) so it never shows in the
   shipped game, same as any polished Streamlit app. ---- */
#MainMenu, header[data-testid="stHeader"], footer {
    visibility: hidden;
    height: 0;
}

/* Apply the monospace "terminal" font everywhere by default ... */
html, body, [class*="css"], .stApp, p, li, label, span, div {
    font-family: 'Share Tech Mono', monospace;
}

/* ... then reserve the display font for the big / HUD text only. */
h1, h2, h3, [data-testid="stMetricValue"] {
    font-family: 'Orbitron', sans-serif !important;
}

/* ---- Page title ------------------------------------------------------ */
h1 {
    color: var(--text-main) !important;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    text-shadow: 0 0 18px var(--accent-glow);
    border-bottom: 1px solid var(--panel-border);
    padding-bottom: 0.6rem;
}

/* ---- Anomaly question: "terminal readout" card ----------------------- */
h3 {
    color: var(--accent) !important;
    background: var(--panel-bg);
    border: 1px solid var(--panel-border);
    border-left: 4px solid var(--accent);
    border-radius: 6px;
    padding: 0.9rem 1.2rem !important;
    letter-spacing: 0.03em;
    box-shadow: 0 0 22px rgba(45, 214, 224, 0.08) inset;
    position: relative;
}
h3::before {
    content: "// ANOMALY READOUT";
    display: block;
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.65rem;
    letter-spacing: 0.15em;
    color: var(--text-dim);
    margin-bottom: 0.35rem;
}

/* ---- Streak HUD (st.metric) ------------------------------------------ */
[data-testid="stMetric"] {
    background: var(--panel-bg);
    border: 1px solid var(--panel-border);
    border-radius: 8px;
    padding: 0.8rem 1.2rem;
    box-shadow: 0 0 20px rgba(45, 214, 224, 0.10);
}
[data-testid="stMetricLabel"] {
    color: var(--text-dim) !important;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    font-size: 0.75rem !important;
}
[data-testid="stMetricValue"] {
    color: var(--accent) !important;
    text-shadow: 0 0 14px var(--accent-glow);
}

/* ---- Feedback message cards (st.info / success / warning / error) ---- */
/* We intentionally do NOT set background-color here -- see the fragility
   note at the top of this file. This only adds "diagnostic log" chrome
   on top of whatever color Streamlit already gives each alert kind. */
[data-testid="stAlert"] {
    border-radius: 8px !important;
    border: 1px solid rgba(255, 255, 255, 0.12) !important;
    /* A soft ambient glow on every alert card. This is deliberately
       kind-agnostic (not "success-only") -- see the note below on why.
       It still reads as a nice little "moment" whenever the message
       happens to be a success one, like "Anomaly Cleared". */
    box-shadow: 0 4px 18px rgba(0, 0, 0, 0.35), 0 0 26px rgba(45, 214, 224, 0.06);
    padding: 0.9rem 1.1rem !important;
    font-family: 'Share Tech Mono', monospace !important;
}
[data-testid="stAlert"] p {
    font-family: 'Share Tech Mono', monospace !important;
}

/* NOTE: "Anomaly Cleared" is rendered via st.success(), and a "resolved"
   verdict message is ALSO rendered via st.success() -- Streamlit gives
   both the exact same data-testid, with no stable hook to tell them
   apart in CSS alone. Rather than reach for a fragile/clever selector
   that could silently stop matching on a Streamlit update, both
   success-kind alerts get the same soft glow above (plus Streamlit's
   own green tint, plus the 🎉 emoji already in that message's text) --
   which reads as celebratory without relying on anything brittle. */

/* ---- Buttons: Submit / Restart / the dismiss "X" buttons -------------- */
.stButton > button {
    font-family: 'Share Tech Mono', monospace;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    background: transparent;
    color: var(--accent);
    border: 1px solid var(--accent);
    border-radius: 6px;
    padding: 0.4rem 1rem;
    transition: all 0.15s ease-in-out;
}
.stButton > button:hover {
    background: var(--accent);
    color: #04141a;
    box-shadow: 0 0 16px var(--accent-glow);
    border-color: var(--accent);
}
.stButton > button:active {
    transform: scale(0.98);
}

/* ---- Phase 8: Home Menu Anomaly cards ---------------------------------
   Reuses the same panel-bg/panel-border/accent look as the question
   "terminal readout" card above, just applied to st.container(border=True)
   instead of an h3. */
[data-testid="stVerticalBlockBorderWrapper"] {
    background: var(--panel-bg);
    border: 1px solid var(--panel-border) !important;
    border-left: 4px solid var(--accent) !important;
    border-radius: 6px !important;
    box-shadow: 0 0 22px rgba(45, 214, 224, 0.08) inset;
}

/* ---- Minor cohesion touches on other inputs --------------------------- */
[data-testid="stSelectbox"] div[data-baseweb="select"] > div,
.stTextInput > div > div,
.stNumberInput > div > div,
.stTextArea > div > div {
    border-radius: 6px !important;
    border: 1px solid var(--panel-border) !important;
}


/* =======================================================================
   THIS MILESTONE -- "in-world consoles" restyle of the raw form widgets.
   Pure CSS on top of the SAME real Streamlit widgets (st.number_input,
   st.text_area, st.button) -- nothing underneath is replaced. Uses the
   same --accent (Chapter 1 cyan) and same two fonts already set up above.
   ======================================================================= */

/* ---- Force-entry console dial (vacuum_box's st.number_input) --------- */
[data-testid="stNumberInput"] {
    position: relative;
    margin: 14px 6px;
    padding: 6px;
}
[data-testid="stNumberInput"]::before,
[data-testid="stNumberInput"]::after {
    content: "";
    position: absolute;
    width: 14px;
    height: 14px;
    pointer-events: none;
}
[data-testid="stNumberInput"]::before {
    top: 0; left: 0;
    border-top: 2px solid var(--accent);
    border-left: 2px solid var(--accent);
    filter: drop-shadow(0 0 4px var(--accent-glow));
}
[data-testid="stNumberInput"]::after {
    bottom: 0; right: 0;
    border-bottom: 2px solid var(--accent);
    border-right: 2px solid var(--accent);
    filter: drop-shadow(0 0 4px var(--accent-glow));
}
.stNumberInput > div > div {
    position: relative !important;
    background: var(--panel-bg) !important;
}
.stNumberInput > div > div::before,
.stNumberInput > div > div::after {
    content: "";
    position: absolute;
    width: 10px;
    height: 10px;
    pointer-events: none;
}
.stNumberInput > div > div::before {
    top: -2px; right: -2px;
    border-top: 2px solid var(--accent);
    border-right: 2px solid var(--accent);
}
.stNumberInput > div > div::after {
    bottom: -2px; left: -2px;
    border-bottom: 2px solid var(--accent);
    border-left: 2px solid var(--accent);
}
.stNumberInput input {
    font-family: 'Share Tech Mono', monospace !important;
    text-align: right !important;
    color: var(--accent) !important;
    background: transparent !important;
    letter-spacing: 0.05em;
    padding-right: 28px !important;
    text-shadow: 0 0 8px var(--accent-glow);
}
.stNumberInput [data-baseweb="base-input"] {
    position: relative;
}
.stNumberInput [data-baseweb="base-input"]::after {
    content: "N";
    position: absolute;
    right: 34px;
    top: 50%;
    transform: translateY(-50%);
    color: var(--text-dim);
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.85rem;
    pointer-events: none;
}

/* ---- AI terminal for the reasoning field (st.text_area) --------------- */
.stTextArea {
    position: relative;
    margin-top: 22px;
}
.stTextArea::before {
    content: "\25B8 AI_TUTOR_LINK -- awaiting input";
    position: absolute;
    top: -20px;
    left: 2px;
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.7rem;
    letter-spacing: 0.1em;
    color: var(--text-dim);
}
.stTextArea > div > div {
    border: 1px solid var(--panel-border) !important;
    background: rgba(0, 0, 0, 0.25) !important;
    box-shadow: 0 0 22px rgba(45, 214, 224, 0.06) inset;
}
.stTextArea textarea {
    font-family: 'Share Tech Mono', monospace !important;
    color: var(--accent) !important;
    background: transparent !important;
    caret-color: var(--accent);
}
.stTextArea::after {
    content: "\2588";
    position: absolute;
    bottom: 8px;
    right: 12px;
    color: var(--accent);
    font-family: 'Share Tech Mono', monospace;
    animation: prometheus-blink 1s step-end infinite;
    pointer-events: none;
}
@keyframes prometheus-blink {
    0%, 50% { opacity: 1; }
    50.01%, 100% { opacity: 0; }
}

/* ---- "ANALYZE" console action button ----------------------------------
   Extends the existing .stButton hover-glow look above; the primary-typed
   ANALYZE button gets a filled default state (not a new style family) so
   it reads as THE console action. */
button[kind="primary"] {
    background: var(--accent) !important;
    color: #04141a !important;
    border: 1px solid var(--accent) !important;
    box-shadow: 0 0 14px var(--accent-glow) !important;
}
button[kind="primary"]:hover {
    box-shadow: 0 0 22px var(--accent-glow) !important;
}

/* =======================================================================
   VISUAL REDESIGN PASS -- "premium research-facility" depth layer.
   Additive only: every rule below cascades on top of the identical-or-
   lower-specificity rules above (same selectors, later in the sheet, or
   more specific) -- nothing above this line is removed, no data-testid
   hooks are renamed, no Streamlit widget is replaced. Pure look-and-feel.
   ======================================================================= */

/* ---- Depth: layered ambient lighting behind the whole app ------------ */
.stApp {
    background:
        radial-gradient(ellipse 900px 500px at 15% -10%, rgba(45,214,224,0.10), transparent 60%),
        radial-gradient(ellipse 700px 500px at 110% 10%, rgba(160,109,224,0.08), transparent 55%),
        radial-gradient(ellipse 1000px 700px at 50% 120%, rgba(244,145,58,0.05), transparent 60%),
        var(--bg-void) !important;
}

/* ---- Cinematic title: bigger, tighter, gradient-lit ------------------- */
h1 {
    font-size: clamp(1.9rem, 3.2vw, 2.8rem) !important;
    font-weight: 800 !important;
    background: linear-gradient(120deg, var(--text-main) 40%, var(--accent) 100%);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent !important;
    text-shadow: none;
    filter: drop-shadow(0 0 20px var(--accent-glow));
    border-bottom: 1px solid var(--panel-border);
    margin-bottom: 0.9rem !important;
}
h2 {
    color: var(--text-main) !important;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    font-size: 1.15rem !important;
    border-left: 3px solid var(--secondary);
    padding-left: 0.6rem;
    opacity: 0.92;
}

/* ---- Glassmorphism: panels get real depth (blur + layered shadow) ---- */
[data-testid="stVerticalBlockBorderWrapper"],
[data-testid="stAlert"],
[data-testid="stMetric"] {
    backdrop-filter: var(--blur);
    -webkit-backdrop-filter: var(--blur);
    background: linear-gradient(155deg, var(--surface-raised), var(--surface)) !important;
    box-shadow:
        0 10px 34px rgba(0, 0, 0, 0.45),
        0 0 26px rgba(45, 214, 224, 0.07),
        inset 0 1px 0 rgba(255, 255, 255, 0.05) !important;
    transition: box-shadow 0.2s ease, transform 0.2s ease;
}
[data-testid="stVerticalBlockBorderWrapper"]:hover {
    box-shadow:
        0 14px 40px rgba(0, 0, 0, 0.5),
        0 0 34px rgba(45, 214, 224, 0.14),
        inset 0 1px 0 rgba(255, 255, 255, 0.06) !important;
}

/* ---- Control-panel buttons: beveled corners, layered glow ------------- */
.stButton > button {
    clip-path: polygon(10px 0, 100% 0, 100% calc(100% - 10px), calc(100% - 10px) 100%, 0 100%, 0 10px);
    font-weight: 600;
    box-shadow: 0 0 0 rgba(0,0,0,0), inset 0 0 0 1px rgba(255,255,255,0.02);
}
.stButton > button:hover {
    box-shadow: 0 0 22px var(--accent-glow), inset 0 0 14px rgba(255,255,255,0.08);
}
.stButton > button:disabled {
    color: var(--text-dim) !important;
    border-color: var(--panel-border) !important;
    opacity: 0.45;
    box-shadow: none !important;
}
button[kind="primary"] {
    clip-path: polygon(10px 0, 100% 0, 100% calc(100% - 10px), calc(100% - 10px) 100%, 0 100%, 0 10px);
    box-shadow: 0 0 26px var(--accent-glow) !important, inset 0 0 16px rgba(255,255,255,0.10) !important;
}

/* ---- Orange warning accent: "thin"/degraded state cards --------------
   Anything explicitly flagged with this class (used sparingly, e.g. a
   locked-mission label) reads as an amber warning rather than the
   default cyan, matching the sci-fi "caution" panel convention. */
.pl-warning-glow {
    border-color: var(--warning) !important;
    box-shadow: 0 0 18px var(--warning-glow) inset !important;
}
.pl-warning-glow, .pl-warning-glow * { color: var(--warning) !important; }

</style>
"""


def inject_custom_css():
    """Call this once near the top of app.py to apply Prometheus Lab's
    sci-fi diagnostic-terminal visual theme. Pure styling -- no logic."""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
