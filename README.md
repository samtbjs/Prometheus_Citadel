# Prometheus Lab

An anomaly-investigation game built with Python + Streamlit. You play a
researcher inside a broken-physics research facility, walking through
three wings (Mechanics, Thermal, Space-Time), reasoning through why
each "impossible" scene is actually behaving correctly, and getting
in-character feedback from the facility's diagnostic AI, ARBITER.

## Setup (from zero)

```bash
# 1. Clone/unzip, then move into the project folder
cd prometheus_lab_fixed/project

# 2. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. (Optional, see below) add your OpenAI API key
echo "OPENAI_API_KEY=sk-..." > .env

# 5. Run it
streamlit run app.py
```

Streamlit will open the app at `http://localhost:8501`.

## Do you need an OpenAI API key?

**No** — the whole game is playable without one.

- **With a key** (`.env` with `OPENAI_API_KEY`): each submitted
  explanation is graded live by an AI tutor, which also replies in
  character as ARBITER.
- **Without a key**: submissions still work. If no key is set (or the
  API call fails for any reason — no internet, rate limit, etc.), the
  app automatically falls back to a mock verdict so the game never
  breaks.
- **To manually control the mock verdict** (useful for quickly seeing
  all outcomes — resolved / thin / wrong — without depending on the
  API), open the app with `?debug=1` appended to the URL, e.g.
  `http://localhost:8501/?debug=1`. This reveals a "Use mock verdict"
  checkbox plus a few other developer-only tools (instant chapter
  unlock, jump-to-Debrief) for quickly exercising every scene. None of
  this appears on the plain URL.

## What to click first (guided tour)

1. **Boot sequence** — click "ENTER FACILITY."
2. **Command Center** — three wings are shown; only *Fundamental
   Forces* (Mechanics) is unlocked at the start. Click it.
3. **Mission Briefing** — ARBITER briefs you on the wing. Click
   "Begin Investigation."
4. **Anomaly menu** — pick **The Floating Box** (`vacuum_box`) and
   click "Enter."
5. Answer the numeric force question and the reasoning prompt, then
   click **ANALYZE**. Do this twice with correct reasoning to clear
   the anomaly and trigger the **Mission Debrief** scene.
6. Clearing every anomaly in a wing unlocks the next one — try
   clearing both Mechanics anomalies to unlock *Energy & Heat*.

## Project structure

```
app.py                  Main Streamlit app / screen routing
ai/tutor.py              Live AI grading + ARBITER's in-character reply
logic/                   Progress tracking, streak rules, physics checks
ui/                      Styling, design tokens, mentor text, 3D scene wiring
scenes/                  Three.js/GSAP scene HTML (boot, briefing, anomaly, etc.)
data/anomalies.json      Chapters, anomalies, and questions
data/progress.json       Player save state (resets to `{}` on a fresh checkout)
static/vendor/           Locally vendored Three.js + GSAP (no CDN)
```
