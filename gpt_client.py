"""
gpt_client.py  —  THE ONE DOOR TO THE MODEL.

Everywhere the app needs AI, it calls ask_gpt(). The model is OpenAI's
GPT-4o-mini, called over the network via the official OpenAI API.

Model selection: set the OPENAI_MODEL environment variable to switch models
with zero code changes (defaults to "gpt-4o-mini").

Your API key lives in a local .env file (OPENAI_API_KEY=sk-...) and is loaded
automatically at import time via python-dotenv — it is never hard-coded here.

If no API key is configured, or the API call fails for any reason, the app
still works: it falls back to clearly-marked placeholder text instead of
crashing. Function names (ask_gpt, gpt_available, ...) are kept as-is so
every other module in this app works unchanged.
"""
import os
import re

from dotenv import load_dotenv
from openai import OpenAI

# Load OPENAI_API_KEY (and any other vars) from a local .env file, if present.
load_dotenv()

# --------------------------------------------------------------------------
# plainify(): strip LaTeX from model output so no raw "$" / "\frac" ever
# reaches the UI. The app's house style is plain-English math ("2/3", "2^3"),
# so we convert rather than render. Applied to every human-facing string
# GPT produces (NOT to JSON responses, which are parsed, not shown).
# --------------------------------------------------------------------------
_SUP = str.maketrans("0123456789+-=()n", "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾ⁿ")

_SYMBOLS = {
    r"\\times": "×", r"\\cdot": "·", r"\\div": "÷", r"\\pm": "±",
    r"\\leq": "≤", r"\\le": "≤", r"\\geq": "≥", r"\\ge": "≥",
    r"\\neq": "≠", r"\\ne": "≠", r"\\approx": "≈", r"\\pi": "π",
    r"\\circ": "°", r"\\degree": "°", r"\\%": "%", r"\\Delta": "Δ",
    r"\\left": "", r"\\right": "", r"\\,": " ", r"\\;": " ", r"\\!": "",
    r"\\quad": "  ", r"\\qquad": "   ",
}


# House vocabulary: the app talks about "snares" (the wrong idea that feels
# right). Model output sometimes reaches for other words; normalize them so
# every screen speaks one language.
_VOCAB = [
    (re.compile(r"\bmisconceptions\b", re.I), "snares"),
    (re.compile(r"\bmisconception\b", re.I), "snare"),
    (re.compile(r"\bconfusing\b", re.I), "mixing up"),
    (re.compile(r"\bconfused\b", re.I), "mixed up"),
    (re.compile(r"\bconfusion\b", re.I), "mix-up"),
    (re.compile(r"\bprobing\b", re.I), "checking"),
    (re.compile(r"\bprobes\b", re.I), "check questions"),
    (re.compile(r"\bprobe\b", re.I), "check question"),
    (re.compile(r"\b(?:learning|knowledge|skill)\s+gaps\b", re.I), "snares"),
    (re.compile(r"\b(?:learning|knowledge|skill)\s+gap\b", re.I), "snare"),
    (re.compile(r"\bgaps\b", re.I), "snares"),
    (re.compile(r"\btricks\b"), "snares"),
    (re.compile(r"\bTricks\b"), "Snares"),
    (re.compile(r"\btrick\b"), "snare"),
    (re.compile(r"\bTrick\b"), "Snare"),
    (re.compile(r"\bgap\b", re.I), "snare"),
]


def plainify(text: str) -> str:
    if not text:
        return text
    t = text
    for pat, rep in _VOCAB:
        t = pat.sub(rep, t)
    # Dollar signs: '$450' is money and must survive; every other '$' is a
    # LaTeX math delimiter and must go, or the UI shows raw '$-3 ... = 2$'.
    # The test is what follows the sign: a digit means currency, anything
    # else (letter, minus, space, punctuation, end of string) means delimiter.
    t = t.replace("\\$", "\x00")                       # \$ in LaTeX is always money
    t = t.replace("$$", "")
    t = re.sub(r"\$(?!\d)", "", t)                     # drop math delimiters only
    t = t.replace("{,}", ",")                          # LaTeX thousands separator
    t = re.sub(r"\\[\(\)\[\]]", "", t)                 # \( \) \[ \]
    t = re.sub(r"\\begin\{[^}]*\}|\\end\{[^}]*\}", "", t)
    t = re.sub(r"\\[dt]?frac\s*\{([^{}]*)\}\s*\{([^{}]*)\}", r"\1/\2", t)  # fractions
    t = re.sub(r"\\sqrt\s*\{([^{}]*)\}", r"√(\1)", t)
    t = re.sub(r"\\(?:text|mathrm|mathbf|mathit|operatorname)\s*\{([^{}]*)\}", r"\1", t)
    for pat, rep in _SYMBOLS.items():
        t = re.sub(pat, rep, t)

    def _sup(match):
        s = match.group(1)
        return s.translate(_SUP) if all(c in "0123456789+-=()n" for c in s) else "^" + s
    t = re.sub(r"\^\{([^{}]*)\}", _sup, t)             # ^{...}
    t = re.sub(r"\^\(([^()]*)\)", _sup, t)             # ^(3+2) -> ⁽³⁺²⁾
    # The whole exponent, not its first digit: matching one character turned
    # 5^12 into 5 with a superscript one, followed by a plain 2.
    t = re.sub(r"\^(-?\d+|n)", lambda m: m.group(1).translate(_SUP), t)  # ^12
    t = re.sub(r"_\{([^{}]*)\}", r"_\1", t)            # _{...}
    t = t.replace("\\\\", " ")                          # LaTeX line breaks
    t = t.replace("\\ ", " ")                           # backslash-space artifacts
    t = re.sub(r"\\([a-zA-Z]+)", r"\1", t)             # drop any leftover \command
    t = t.replace("^°", "°")                            # 180^\circ -> 180°
    t = t.replace("\x00", "$")                          # restore protected currency
    t = re.sub(r"[ \t]{2,}", " ", t)
    return t.strip()

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
# gpt-4o-mini is multimodal, so the same model handles vision by default.
VISION_MODEL = os.environ.get("OPENAI_VISION_MODEL", "gpt-4o-mini")
TIMEOUT_S = int(os.environ.get("OPENAI_TIMEOUT_S", "120"))

_client = None

def _get_client():
    """Lazily build the OpenAI client so importing this module never fails
    just because a key isn't set yet (e.g. before .env is filled in)."""
    global _client
    if _client is None and OPENAI_API_KEY:
        _client = OpenAI(api_key=OPENAI_API_KEY, timeout=TIMEOUT_S)
    return _client


def ask_gpt(prompt: str, max_new_tokens: int = 600) -> str:
    """Text in, text out. The only function that talks to the model.

    A model that is slow, missing a key, or unreachable answers the same way
    one with no key configured does: with clearly marked placeholder text, so
    a judge without an OPENAI_API_KEY sees the app degrade, not throw.
    Raise OPENAI_TIMEOUT_S to give a slow call more room.
    """
    if gpt_available():
        try:
            return _openai_chat(prompt, max_new_tokens)
        except Exception:
            return _stub(prompt)
    return _stub(prompt)


_available = None

def gpt_available() -> bool:
    """True if an OpenAI API key is configured (checked once per process)."""
    global _available
    if _available is None:
        _available = bool(OPENAI_API_KEY)
    return _available


def _openai_chat(prompt: str, max_new_tokens: int) -> str:
    client = _get_client()
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,          # low = consistent math
        max_tokens=max_new_tokens,
    )
    return (resp.choices[0].message.content or "").strip()


_PREAMBLE = re.compile(
    r"(?i)(here.?s a report|here is a report|please be aware|^okay[,!]|^sure[,!]|"
    r"as requested|based (only )?on the provided facts|this response|i will|below is)")


def format_teacher_report(header_md: str, narrative: str) -> str:
    """Turn a raw GPT report into clean, wrapping markdown: a header line, the
    prose, and a bulleted 'Try in class' section. Strips model preamble and
    splits interventions even when the model numbers them inline."""
    # 1) drop leading preamble paragraphs ("Okay, here's a report...")
    paras = [p.strip() for p in re.split(r"\n\s*\n", narrative) if p.strip()]
    while len(paras) > 1 and _PREAMBLE.search(paras[0]):
        paras.pop(0)
    narrative = "\n\n".join(paras)

    # 2) split off the interventions
    low = narrative.lower()
    marker = "try at home" if "try at home" in low else ("try in class" if "try in class" in low else None)
    if marker:
        i = low.index(marker)
        prose = narrative[:i].strip()
        after = narrative[i:].split(":", 1)[1] if ":" in narrative[i:] else ""
        # Split on bullet/number markers only at the START of a line. Matching
        # them inline tore activities in half: '2x2x2 x 2x2) - and then...'
        # looks like a numbered marker at '2) ', mid-expression.
        items = [t.strip() for t in
                 re.split(r"(?m)^[ \t]*(?:\d+[.)]|[-–*•])[ \t]+", after) if t.strip()]
    else:
        prose, items = narrative.strip(), []

    md = header_md.strip() + "\n\n" + prose
    if items:
        md += "\n\n**Try at home**\n\n" + "\n".join(f"- {it}" for it in items)
    return md


def vision_available() -> bool:
    """True if an OpenAI API key is configured (gpt-4o-mini is multimodal)."""
    return gpt_available()


def transcribe_image(image_bytes: bytes) -> str:
    """The model reads a photo of handwritten work over the OpenAI API. It
    TRANSCRIBES ONLY; judging correctness stays with the grader and the
    verified bank (transcription is where vision models are weakest, so we
    never let the photo decide what is mathematically true)."""
    import base64
    client = _get_client()
    b64 = base64.b64encode(image_bytes).decode()
    resp = client.chat.completions.create(
        model=VISION_MODEL,
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": (
                    "Transcribe this handwritten math work verbatim, one "
                    "line per step, as plain text like 2/3 + 1/4 = 3/7. "
                    "Do NOT correct any mistakes. If a line is illegible, "
                    "write [illegible]. Output only the transcription.")},
                {"type": "image_url",
                 "image_url": {"url": f"data:image/png;base64,{b64}"}},
            ],
        }],
        temperature=0,
        max_tokens=600,
    )
    return plainify((resp.choices[0].message.content or "").strip())


# --------------------------------------------------------------------------
# Fallback stub — used only when no OPENAI_API_KEY is configured (or a call
# fails), so the app still runs for teammates without a key set up yet.
# --------------------------------------------------------------------------
def _stub(prompt: str) -> str:
    task = _tag(prompt, "TASK") or "explain"
    misc = _tag(prompt, "TRICK") or "this trick"
    if task == "practice":
        return ("_(GPT-4o-mini will generate a fresh practice question here — one that "
                f"targets '{misc}'. Add OPENAI_API_KEY to your .env file to see it live.)_")
    return ("_(GPT-4o-mini will write a personalized explanation here for '"
            f"{misc}'. Add OPENAI_API_KEY to your .env file to see it live.)_")


def _tag(prompt: str, key: str) -> str:
    for line in prompt.splitlines():
        if line.strip().upper().startswith(key + ":"):
            return line.split(":", 1)[1].strip()
    return ""
