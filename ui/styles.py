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

CUSTOM_CSS = """
<style>

/* ---- Fonts ---------------------------------------------------------- */
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@600;800&family=Share+Tech+Mono&display=swap');

:root {
    --accent: #2dd6e0;
    --accent-glow: rgba(45, 214, 224, 0.55);
    --accent-dim: rgba(45, 214, 224, 0.18);
    --panel-bg: rgba(255, 255, 255, 0.035);
    --panel-border: rgba(45, 214, 224, 0.28);
    --success: #4ade80;
    --warning: #fbbf24;
    --error: #f87171;
    --text-main: #e6f1f3;
    --text-dim: #8aa0aa;
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

</style>
"""


def inject_custom_css():
    """Call this once near the top of app.py to apply Prometheus Lab's
    sci-fi diagnostic-terminal visual theme. Pure styling -- no logic."""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
