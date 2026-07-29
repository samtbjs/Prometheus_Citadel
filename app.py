import uuid

import streamlit as st
from logic.streak_engine import (
    load_anomalies,
    load_progress,
    save_progress,
    get_anomaly_progress,
    update_anomaly_progress,
    update_streak,
    is_anomaly_cleared,
)
from logic.physics_calc import check_vacuum_box_force, vacuum_box_feedback
from ai.tutor import judge_explanation, mock_in_character_response
from ui.styles import inject_custom_css
from ui.scene_viewer import render_anomaly_scene, render_boot_scene, render_command_center_scene

inject_custom_css()

# ---------------------------------------------------------------------
# MILESTONE 1 — new opening scene, gating entry into the existing app.
# "intro_stage" is a separate flag from the existing "view" state below
# on purpose, so this doesn't touch the menu/anomaly_room logic at all.
# ---------------------------------------------------------------------
if "intro_stage" not in st.session_state:
    st.session_state.intro_stage = "boot"

if st.session_state.intro_stage == "boot":
    render_boot_scene()
    if st.button("ENTER FACILITY"):
        st.session_state.intro_stage = "command_center"
        st.rerun()
    st.stop()

if st.session_state.intro_stage == "command_center":
    render_command_center_scene()
    if st.button("Continue to Anomaly Log"):
        st.session_state.intro_stage = "done"
        st.rerun()
    st.stop()

st.title("Prometheus Lab")

# ---------------------------------------------------------------------------
# Load the list of Anomalies from data/anomalies.json every time the app
# runs. This replaces the old hardcoded MOCK_QUESTIONS list from Phase 1.
# ---------------------------------------------------------------------------
anomalies = load_anomalies()
anomaly_ids = list(anomalies.keys())

# Load saved progress from data/progress.json exactly once per browser
# session, and keep it in Streamlit's session_state from then on so we're
# not re-reading the file on every single click.
if "progress" not in st.session_state:
    st.session_state.progress = load_progress()

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
    st.session_state.view = "anomaly_room"


# -----------------------------------------------------------------------
# PHASE 8: HOME MENU screen. Replaces the old st.selectbox dropdown. Lists
# all 3 Anomalies with a cleared/uncleared badge (read from
# st.session_state.progress, always current since we save to disk after
# every Submit) and a button to enter each one.
# -----------------------------------------------------------------------
if st.session_state.view == "menu":
    st.subheader("Select an Anomaly")
    for aid in anomaly_ids:
        info = anomalies[aid]
        saved = get_anomaly_progress(st.session_state.progress, aid)
        status = "✅ Cleared" if saved["cleared"] else "🔒 In Progress"
        with st.container(border=True):
            st.markdown(f"**{info['name']}** — {status}")
            st.caption(info["description"])
            if st.button("Enter", key=f"enter_{aid}"):
                _enter_anomaly(aid)
                st.rerun()
    st.stop()

# From here down we are inside "anomaly_room" for st.session_state.current_anomaly.
selected_id = st.session_state.current_anomaly

if st.button("← Back to Menu"):
    st.session_state.view = "menu"
    st.rerun()

anomaly = anomalies[selected_id]
questions = anomaly["questions"]

st.caption(anomaly["description"])

# -----------------------------------------------------------------------
# PHASE 7a: a single, STATIC (not yet animated) Three.js 3D scene, shown
# only for the "vacuum_box" Anomaly, above the question/readout card
# below. sinking_stone and hot_cold_chairs are untouched and show no
# scene at all. Animation (7b) and fallback/error-handling (7c) are
# deliberately NOT part of this step -- see ui/scene_viewer.py.
# -----------------------------------------------------------------------
if selected_id == "vacuum_box":
    render_anomaly_scene()

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
    # PHASE 4: the old Phase 1/2 dropdown is now a permanent SAFETY NET
    # rather than the only option. By default this checkbox is OFF,
    # which means the app calls the real GPT-4o mini AI (below) to judge
    # the explanation. If you check this box, the app skips the real AI
    # call entirely and goes back to using the dropdown's value instead
    # -- handy if you're out of API budget or just want to test quickly.
    # -----------------------------------------------------------------
    use_mock = st.checkbox(
        "Use mock verdict instead of real AI (fallback if API fails or I'm low on budget)"
    )
    fake_verdict = st.selectbox(
        "Mock AI verdict (used only when the checkbox above is checked, "
        "or automatically if the real AI call fails):",
        ["resolved", "thin", "wrong"],
    )

    if st.button("Submit"):
        # Messages from THIS submission. We build a fresh list each time
        # rather than adding onto the old one, so a new Submit naturally
        # replaces the previous round's feedback -- but each message you
        # see is still yours to dismiss (or leave up) independently.
        new_messages = []

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

        st.rerun()

    st.metric("Current Streak", st.session_state.streak)
