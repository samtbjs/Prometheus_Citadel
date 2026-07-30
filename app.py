import time
import uuid

import streamlit as st
from logic.streak_engine import (
    load_anomalies,
    load_chapters,
    load_progress,
    save_progress,
    get_anomaly_progress,
    update_anomaly_progress,
    update_streak,
    is_anomaly_cleared,
    is_chapter_unlocked,
    debug_force_clear_chapter,
    debug_force_clear_anomaly,
    debug_reset_progress,
)
from logic.physics_calc import check_vacuum_box_force, vacuum_box_feedback
from ai.tutor import judge_explanation, mock_in_character_response
from ui.styles import inject_custom_css
from ui.scene_viewer import (
    render_anomaly_scene,
    render_boot_scene,
    render_briefing_scene,
    render_command_center_scene,
    render_debrief_scene,
    render_transition_scene,
)
from ui.mentor import MENTOR_NAME, briefing_lines_for, debrief_line_for
import ui.design_tokens as tokens

inject_custom_css()

debug_mode = st.query_params.get("debug") == "1"

# ---------------------------------------------------------------------------
# Load the list of Anomalies + Chapters from data/anomalies.json every time
# the app runs. anomalies is still a FLAT dict keyed by anomaly id (Milestone
# 3 keeps that shape via load_anomalies() even though the file on disk is
# now nested) -- so this line doesn't need to move or change.
# ---------------------------------------------------------------------------
anomalies = load_anomalies()
anomaly_ids = list(anomalies.keys())
chapters = load_chapters()

# Load saved progress from data/progress.json exactly once per browser
# session, and keep it in Streamlit's session_state from then on so we're
# not re-reading the file on every single click. (Moved above the intro
# scenes in Milestone 3 -- the Command Center needs it to know lock state.)
if "progress" not in st.session_state:
    st.session_state.progress = load_progress()

# ---------------------------------------------------------------------
# MILESTONE 5, Part C: Travel Transition. Buttons that change screens no
# longer set view/intro_stage + st.rerun() directly -- they call
# _begin_transition() below, which stashes the real destination in
# "pending_view"/"pending_intro_stage" and reruns with "transitioning"
# on. THIS block, which runs before any normal screen on every rerun, is
# the only place that ever reads those pending values: it shows the
# corridor once, sleeps briefly, then lands on the real destination and
# reruns again. try/except/finally guarantees we always land -- if the
# corridor render or the sleep ever raises, or if TRANSITION_STUCK_AFTER
# seconds somehow pass without landing, we skip straight to the
# destination instead of ever looping or freezing on this screen.
# ---------------------------------------------------------------------
TRANSITION_SECONDS = 0.7
TRANSITION_STUCK_AFTER = 3.0

for _key, _default in (
    ("transitioning", False),
    ("pending_view", None),
    ("pending_intro_stage", None),
    ("transition_accent", None),
    ("transition_started", 0.0),
):
    if _key not in st.session_state:
        st.session_state[_key] = _default


def _begin_transition(view=None, intro_stage=None, accent_hex=None):
    """Call this instead of setting view/intro_stage + st.rerun() directly
    whenever a button changes screens, so the corridor plays first."""
    st.session_state.pending_view = view
    st.session_state.pending_intro_stage = intro_stage
    st.session_state.transition_accent = accent_hex
    st.session_state.transitioning = True
    st.session_state.transition_started = time.time()
    st.rerun()


if st.session_state.transitioning:
    stuck = (time.time() - st.session_state.transition_started) > TRANSITION_STUCK_AFTER
    try:
        if not stuck:
            render_transition_scene(accent_hex=st.session_state.transition_accent)
            time.sleep(TRANSITION_SECONDS)
    except Exception:
        pass  # never let a render/timing hiccup block landing, below
    finally:
        if st.session_state.pending_view is not None:
            st.session_state.view = st.session_state.pending_view
        if st.session_state.pending_intro_stage is not None:
            st.session_state.intro_stage = st.session_state.pending_intro_stage
        st.session_state.transitioning = False
        st.session_state.pending_view = None
        st.session_state.pending_intro_stage = None
        st.rerun()
    st.stop()

# ---------------------------------------------------------------------
# MILESTONE 1 — new opening scene, gating entry into the existing app.
# "intro_stage" is a separate flag from the existing "view" state below
# on purpose, so this doesn't touch the menu/anomaly_room logic at all.
# ---------------------------------------------------------------------
if "intro_stage" not in st.session_state:
    st.session_state.intro_stage = "boot"

if "current_chapter" not in st.session_state:
    st.session_state.current_chapter = None

# MILESTONE 6: which chapters have already shown their Mission Briefing
# THIS session. Deliberately session-only (not saved to progress.json)
# so every fresh run sees each chapter's briefing again once.
if "briefed_chapters" not in st.session_state:
    st.session_state.briefed_chapters = set()

if st.session_state.intro_stage == "boot":
    render_boot_scene()
    if st.button("ENTER FACILITY"):
        st.session_state.intro_stage = "command_center"
        st.rerun()
    st.stop()

if st.session_state.intro_stage == "command_center":
    # MILESTONE 3: stations are now REAL chapter data (name / accent color
    # / lock state), not hardcoded mock divs. Lock state comes straight
    # from is_chapter_unlocked(), which reuses the existing progress data
    # -- no second progress system invented.
    stations = [
        {
            "name": chapters[cid]["name"],
            "accent_hex": getattr(tokens, chapters[cid]["accent_token"]),
            "unlocked": is_chapter_unlocked(cid, chapters, st.session_state.progress),
        }
        for cid in chapters
    ]
    render_command_center_scene(stations=stations)

    # The 3D cards above are visual only (they live inside a sandboxed
    # iframe with no click-back-to-Streamlit hook). These real buttons
    # right underneath are what you actually click -- one per chapter,
    # in the same left-to-right order as the stations above.
    cols = st.columns(len(chapters))
    for col, cid in zip(cols, chapters):
        chapter = chapters[cid]
        unlocked = is_chapter_unlocked(cid, chapters, st.session_state.progress)
        with col:
            if unlocked:
                if st.button(f"▶ {chapter['name']}", key=f"enter_chapter_{cid}"):
                    st.session_state.current_chapter = cid
                    chapter_accent = getattr(tokens, chapter["accent_token"])
                    # MILESTONE 6: first time this chapter is entered THIS
                    # session, detour through the Mission Briefing; after
                    # that, go straight to the menu like before.
                    next_view = "menu" if cid in st.session_state.briefed_chapters else "briefing"
                    _begin_transition(view=next_view, intro_stage="done", accent_hex=chapter_accent)
            else:
                st.button(f"🔒 {chapter['name']}", key=f"locked_chapter_{cid}", disabled=True)

    if debug_mode:
        st.caption("DEBUG: instantly mark a chapter's anomalies cleared, to test lock states.")
        dcols = st.columns(len(chapters) + 1)
        for col, cid in zip(dcols, chapters):
            with col:
                if st.button(f"Force-clear: {chapters[cid]['name']}", key=f"debug_clear_{cid}"):
                    debug_force_clear_chapter(st.session_state.progress, chapters[cid])
                    save_progress(st.session_state.progress)
                    st.rerun()
        with dcols[-1]:
            if st.button("Reset all progress", key="debug_reset_progress"):
                st.session_state.progress = debug_reset_progress()
                st.rerun()

        # MILESTONE 6: re-trigger any chapter's Mission Briefing on
        # demand, since otherwise it only shows once per chapter per
        # session -- same button-per-chapter pattern as Force-clear above.
        st.caption("DEBUG: re-trigger a chapter's Mission Briefing on demand.")
        bcols = st.columns(len(chapters))
        for col, cid in zip(bcols, chapters):
            with col:
                if st.button(f"Briefing: {chapters[cid]['name']}", key=f"debug_briefing_{cid}"):
                    st.session_state.current_chapter = cid
                    _begin_transition(
                        view="briefing",
                        intro_stage="done",
                        accent_hex=getattr(tokens, chapters[cid]["accent_token"]),
                    )

        # -------------------------------------------------------------
        # MILESTONE 5: instantly jump to the Mission Debrief scene for
        # any anomaly, so it can be tested repeatedly without grinding
        # through real questions each time.
        # -------------------------------------------------------------
        st.caption("DEBUG: instantly trigger the Mission Debrief scene for any anomaly.")
        debrief_choice = st.selectbox(
            "Anomaly to instantly clear + debrief:", anomaly_ids, key="debug_debrief_choice"
        )
        if st.button("Trigger Debrief", key="debug_trigger_debrief"):
            unlocked_before = {
                cid: is_chapter_unlocked(cid, chapters, st.session_state.progress) for cid in chapters
            }
            debug_force_clear_anomaly(st.session_state.progress, debrief_choice)
            save_progress(st.session_state.progress)
            unlocked_after = {
                cid: is_chapter_unlocked(cid, chapters, st.session_state.progress) for cid in chapters
            }
            newly_unlocked = [
                chapters[cid]["name"] for cid in chapters
                if not unlocked_before[cid] and unlocked_after[cid]
            ]
            owning_chapter = next(
                (cid for cid in chapters if debrief_choice in chapters[cid]["anomalies"]), None
            )
            st.session_state.current_chapter = owning_chapter
            st.session_state.current_anomaly = debrief_choice
            st.session_state.debrief_anomaly_id = debrief_choice
            st.session_state.debrief_newly_unlocked = newly_unlocked
            st.session_state.intro_stage = "done"
            debrief_accent = (
                getattr(tokens, chapters[owning_chapter]["accent_token"])
                if owning_chapter else tokens.MENTOR_ACCENT
            )
            _begin_transition(view="debrief", accent_hex=debrief_accent)
    st.stop()

st.title("Prometheus Lab")

# -----------------------------------------------------------------------
# PHASE 4 FIX: messages (like "Correct!" or an AI-error warning) used to
# vanish almost instantly. That's because every Submit click calls
# st.rerun() to refresh the streak/question -- and Streamlit throws away
# any st.info/st.warning/st.error the moment it reruns. So instead of
# printing a message once and hoping it survives, we now save messages
# here in session_state and redraw them on every rerun until the
# student clicks the "✕" button to dismiss them.
# -----------------------------------------------------------------------
if "feedback_messages" not in st.session_state:
    st.session_state.feedback_messages = []

# THIS MILESTONE: the most recent verdict for the current Anomaly, so the
# Anomaly Chamber scene can react to it (calm/stabilize on "resolved",
# shudder/destabilize on "thin"/"wrong"). None = no submission yet this
# visit -> scene stays neutral. Reset whenever a new Anomaly is entered,
# in _enter_anomaly() below.
if "last_verdict" not in st.session_state:
    st.session_state.last_verdict = None

# -----------------------------------------------------------------------
# PHASE 8: which screen is showing right now. "menu" = new Home Menu.
# "anomaly_room" = the existing question/streak/3D-scene screen. Defaults
# to "menu" on first load, and ALSO on every real browser refresh, since
# session_state is wiped on a true reload (only progress.json on disk
# survives a reload, which is exactly what we want).
# -----------------------------------------------------------------------
if "view" not in st.session_state:
    st.session_state.view = "menu"


def _enter_anomaly(anomaly_id):
    """Switch to an Anomaly's room and load ITS saved progress into
    session_state, so it resumes exactly where it left off."""
    st.session_state.current_anomaly = anomaly_id
    saved = get_anomaly_progress(st.session_state.progress, anomaly_id)
    st.session_state.question_index = saved["question_index"]
    st.session_state.streak = saved["streak"]
    st.session_state.cleared = saved["cleared"]
    st.session_state.feedback_messages = []
    st.session_state.last_verdict = None


# -----------------------------------------------------------------------
# PHASE 8: HOME MENU screen. Replaces the old st.selectbox dropdown. Lists
# all 3 Anomalies with a cleared/uncleared badge (read from
# st.session_state.progress, always current since we save to disk after
# every Submit) and a button to enter each one.
# -----------------------------------------------------------------------
if st.session_state.view == "menu":
    # MILESTONE 3: only show anomalies from the chapter the player entered
    # through in the Command Center -- not the old flat all-anomalies list.
    current_chapter_id = st.session_state.current_chapter
    if current_chapter_id and current_chapter_id in chapters:
        chapter_anomaly_ids = chapters[current_chapter_id]["anomalies"]
        st.subheader(f"Select an Anomaly — {chapters[current_chapter_id]['name']}")
    else:
        # Fallback (shouldn't normally happen): show everything rather
        # than crash if current_chapter was never set.
        chapter_anomaly_ids = anomaly_ids
        st.subheader("Select an Anomaly")

    if st.button("← Back to Command Center"):
        _begin_transition(intro_stage="command_center", accent_hex=tokens.CHAPTER_1_ACCENT)

    for aid in chapter_anomaly_ids:
        info = anomalies[aid]
        saved = get_anomaly_progress(st.session_state.progress, aid)
        status = "✅ Cleared" if saved["cleared"] else "🔒 In Progress"
        with st.container(border=True):
            st.markdown(f"**{info['name']}** — {status}")
            st.caption(info["description"])
            if st.button("Enter", key=f"enter_{aid}"):
                _enter_anomaly(aid)
                enter_accent = (
                    getattr(tokens, chapters[current_chapter_id]["accent_token"])
                    if current_chapter_id in chapters else tokens.CHAPTER_1_ACCENT
                )
                _begin_transition(view="anomaly_room", accent_hex=enter_accent)
    st.stop()

# -----------------------------------------------------------------------
# MILESTONE 6: Mission Briefing. Shown once per chapter per session,
# right after the Travel Transition into that chapter and before its
# anomaly menu -- see the Command Center button + debug buttons above,
# which decide when to route here. A separate "view" state, same pattern
# as "menu"/"anomaly_room"/"debrief" -- doesn't touch any of their logic.
# -----------------------------------------------------------------------
if st.session_state.view == "briefing":
    briefing_chapter_id = st.session_state.current_chapter
    chapter = chapters.get(briefing_chapter_id)
    chapter_name = chapter["name"] if chapter else "Unknown Wing"
    chapter_accent = getattr(tokens, chapter["accent_token"]) if chapter else tokens.MENTOR_ACCENT
    render_briefing_scene(
        chapter_name=chapter_name,
        mentor_name=MENTOR_NAME,
        lines=briefing_lines_for(briefing_chapter_id),
        accent_hex=chapter_accent,
    )
    if st.button("Begin Investigation", type="primary"):
        st.session_state.briefed_chapters.add(briefing_chapter_id)
        _begin_transition(view="menu", accent_hex=chapter_accent)
    st.stop()

# -----------------------------------------------------------------------
# MILESTONE 5, Part B: Mission Debrief. Shown once, right when an anomaly
# is newly cleared (see the ANALYZE handler below), before returning to
# the chapter menu. A separate "view" state, same pattern as "menu" vs
# "anomaly_room" above -- doesn't touch either of their logic.
# -----------------------------------------------------------------------
if st.session_state.view == "debrief":
    debrief_id = st.session_state.get("debrief_anomaly_id")
    debrief_anomaly_name = anomalies.get(debrief_id, {}).get("name", debrief_id or "Unknown Anomaly")
    render_debrief_scene(
        anomaly_name=debrief_anomaly_name,
        mentor_name=MENTOR_NAME,
        mentor_line=debrief_line_for(debrief_id),
        newly_unlocked_names=st.session_state.get("debrief_newly_unlocked", []),
    )
    if st.button("Continue", type="primary"):
        _begin_transition(view="menu", accent_hex=tokens.CHAPTER_1_ACCENT)
    st.stop()

# From here down we are inside "anomaly_room" for st.session_state.current_anomaly.
selected_id = st.session_state.current_anomaly

if st.button("← Back to Menu"):
    _begin_transition(view="menu", accent_hex=tokens.CHAPTER_1_ACCENT)

anomaly = anomalies[selected_id]
questions = anomaly["questions"]

st.caption(anomaly["description"])

# -----------------------------------------------------------------------
# MILESTONE 4: every Anomaly now has its own live 3D reaction scene (was
# vacuum_box-only through Milestone 3). render_anomaly_scene() picks the
# right focal object + chapter accent color for selected_id -- see
# ui/focal_objects.py and ui/scene_viewer.py.
# -----------------------------------------------------------------------
render_anomaly_scene(anomaly_id=selected_id, verdict=st.session_state.last_verdict)

# -----------------------------------------------------------------------
# Redraw any messages saved from the last Submit click, each with its own
# ✕ button. Clicking ✕ removes just that one message and reruns, so the
# rest stay put. Messages stay on screen indefinitely otherwise -- no
# more disappearing after a few seconds.
# -----------------------------------------------------------------------
for msg in list(st.session_state.feedback_messages):
    col_text, col_close = st.columns([20, 1])
    with col_text:
        getattr(st, msg["kind"])(msg["text"])
    with col_close:
        if st.button("✕", key=f"dismiss_{msg['id']}"):
            st.session_state.feedback_messages = [
                m for m in st.session_state.feedback_messages if m["id"] != msg["id"]
            ]
            st.rerun()

if st.session_state.cleared:
    st.success("🎉 Anomaly Cleared!")
    if st.button("Restart This Anomaly"):
        st.session_state.question_index = 0
        st.session_state.streak = 0
        st.session_state.cleared = False

        update_anomaly_progress(st.session_state.progress, selected_id, 0, 0, False)
        save_progress(st.session_state.progress)
        st.rerun()
else:
    q = questions[st.session_state.question_index]
    st.subheader(q["prompt"])

    explanation_key = f"explanation_{selected_id}_{st.session_state.question_index}"

    # -----------------------------------------------------------------
    # PHASE 3: "vacuum_box" now gets a REAL calculation instead of the
    # old keyword-matching text box. The student types a NUMBER (their
    # guess for the net force on the box, in Newtons), and we check that
    # number with actual arithmetic in logic/physics_calc.py.
    #
    # The other two Anomalies (sinking_stone, hot_cold_chairs) are
    # untouched — they still show a plain text box like before.
    # -----------------------------------------------------------------
    is_vacuum_box = selected_id == "vacuum_box"

    if is_vacuum_box:
        force_key = f"force_{selected_id}_{st.session_state.question_index}"
        student_force = st.number_input(
            "Enter the net force acting on the box, in Newtons (N):",
            value=0.0,
            step=0.1,
            format="%.2f",
            key=force_key,
        )
    else:
        answer_key = f"answer_{selected_id}_{st.session_state.question_index}"
        student_answer = st.text_input("Your answer:", key=answer_key)

    explanation = st.text_area("Explain your reasoning in one sentence:", key=explanation_key)

    # -----------------------------------------------------------------
    # PHASE 4 (THIS MILESTONE: hidden by default): the old Phase 1/2
    # dropdown is a dev/testing safety net, not something a player should
    # see. It now only renders when the page URL includes "?debug=1" --
    # e.g. http://localhost:8501/?debug=1 -- so you can still flip it on
    # yourself to test offline without an API key, without it cluttering
    # the normal experience. When hidden, use_mock/fake_verdict default
    # to False/"resolved" so a real (or failed) AI call still behaves
    # exactly as before.
    # -----------------------------------------------------------------
    if debug_mode:
        use_mock = st.checkbox(
            "Use mock verdict instead of real AI (fallback if API fails or I'm low on budget)"
        )
        fake_verdict = st.selectbox(
            "Mock AI verdict (used only when the checkbox above is checked, "
            "or automatically if the real AI call fails):",
            ["resolved", "thin", "wrong"],
        )
    else:
        use_mock = False
        fake_verdict = "resolved"

    if st.button("ANALYZE", type="primary"):
        # Messages from THIS submission. We build a fresh list each time
        # rather than adding onto the old one, so a new Submit naturally
        # replaces the previous round's feedback -- but each message you
        # see is still yours to dismiss (or leave up) independently.
        new_messages = []

        # MILESTONE 5: snapshot "before" state so we can tell, after this
        # submission, whether the anomaly was JUST cleared (not already
        # cleared from an earlier visit) and whether that newly unlocked
        # any chapter -- needed to drive the one-time Debrief scene below.
        was_cleared_before = st.session_state.cleared
        unlocked_before = {
            cid: is_chapter_unlocked(cid, chapters, st.session_state.progress) for cid in chapters
        }

        if is_vacuum_box:
            # Grade the NUMBER with real physics, not string matching.
            force_is_correct = check_vacuum_box_force(student_force)
            new_messages.append({
                "id": str(uuid.uuid4()),
                "kind": "info" if force_is_correct else "warning",
                "text": vacuum_box_feedback(student_force),
            })

        # -------------------------------------------------------------
        # Decide the explanation-quality verdict. This applies to ALL
        # THREE Anomalies -- even vacuum_box, which additionally has
        # its own separate real numeric force check above.
        # -------------------------------------------------------------
        # ---------------------------------------------------------------
        # PHASE 5: judge_explanation() now returns TWO things from its
        # single API call: the verdict word (same as Phase 4) AND a
        # short in-character line of dialogue from the "ship's
        # diagnostic AI" persona. Whenever we're using the mock path
        # (checkbox checked, or the real call fails below), there is no
        # real dialogue to show, so we use the same hardcoded generic
        # line from mock_in_character_response() in both of those cases.
        # ---------------------------------------------------------------
        if use_mock:
            explanation_verdict = fake_verdict
            tutor_response = mock_in_character_response()
        else:
            try:
                explanation_verdict, tutor_response = judge_explanation(
                    question_prompt=q["prompt"],
                    expected_concept=q["answer"],
                    student_explanation=explanation,
                )
            except Exception as error:
                # Covers things like: no internet, invalid/missing API
                # key, rate limits, or any other unexpected API problem.
                # We never let this crash the app -- we tell the student
                # plainly what happened and fall back to the mock
                # dropdown's value (and the mock dialogue line) for
                # this one submission only.
                new_messages.append({
                    "id": str(uuid.uuid4()),
                    "kind": "error",
                    "text": (
                        f"⚠️ Couldn't reach the real AI tutor ({error}). "
                        "Falling back to the mock verdict for this submission."
                    ),
                })
                explanation_verdict = fake_verdict
                tutor_response = mock_in_character_response()

        if is_vacuum_box:
            # The real numeric calculation always has the final say: if
            # the force value is wrong, the verdict is "wrong" no matter
            # how good the written explanation was. If the force value
            # is right, the explanation-quality verdict (real AI, or the
            # mock fallback) decides resolved/thin/wrong.
            verdict = explanation_verdict if force_is_correct else "wrong"
        else:
            verdict = explanation_verdict

        # -------------------------------------------------------------
        # PHASE 5: this used to be a plain "AI verdict on your
        # explanation: X" line. We now fold the verdict word AND the
        # in-character tutor dialogue into ONE combined message instead
        # of showing them as two separate messages. Reasoning: the
        # dialogue line only makes sense paired with the verdict that
        # produced it ("resolved" -> affirming line, "thin"/"wrong" ->
        # guiding question), so keeping them together as one message
        # reads as a single coherent moment from the tutor rather than
        # cluttering the screen with two messages every submission. The
        # bold verdict word is kept at the front so it's still instantly
        # scannable, exactly like before.
        # -------------------------------------------------------------
        verdict_kind = {"resolved": "success", "thin": "warning", "wrong": "error"}[verdict]
        new_messages.append({
            "id": str(uuid.uuid4()),
            "kind": verdict_kind,
            "text": f"**{verdict.upper()}** — {tutor_response}",
        })

        st.session_state.feedback_messages = new_messages
        st.session_state.last_verdict = verdict

        st.session_state.streak = update_streak(st.session_state.streak, verdict)
        st.session_state.question_index = (st.session_state.question_index + 1) % len(questions)

        if is_anomaly_cleared(st.session_state.streak):
            st.session_state.cleared = True

        # Save this Anomaly's new streak/question/cleared status to
        # data/progress.json so it survives a reload.
        update_anomaly_progress(
            st.session_state.progress,
            selected_id,
            st.session_state.question_index,
            st.session_state.streak,
            st.session_state.cleared,
        )
        save_progress(st.session_state.progress)

        # MILESTONE 7 FIX: this is the actual "just cleared" -> Debrief
        # routing (previously misplaced under the Restart button, where
        # it referenced an undefined variable and could never run --
        # meaning the Debrief scene never appeared after a real clear).
        # was_cleared_before/unlocked_before were captured above, before
        # this submission changed anything, so the comparison is valid.
        if st.session_state.cleared and not was_cleared_before:
            unlocked_after = {
                cid: is_chapter_unlocked(cid, chapters, st.session_state.progress) for cid in chapters
            }
            newly_unlocked = [
                chapters[cid]["name"] for cid in chapters
                if not unlocked_before[cid] and unlocked_after[cid]
            ]
            st.session_state.debrief_anomaly_id = selected_id
            st.session_state.debrief_newly_unlocked = newly_unlocked
            chapter_id = st.session_state.current_chapter
            debrief_accent = (
                getattr(tokens, chapters[chapter_id]["accent_token"])
                if chapter_id in chapters else tokens.MENTOR_ACCENT
            )
            _begin_transition(view="debrief", accent_hex=debrief_accent)

        st.rerun()

    st.metric("Current Streak", st.session_state.streak)
