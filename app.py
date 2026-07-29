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

st.title("Prometheus Lab — Anomaly Room (Phase 3 Prototype)")

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

# A dropdown so the student can choose which Anomaly to work on.
selected_id = st.selectbox(
    "Choose an Anomaly:",
    anomaly_ids,
    format_func=lambda aid: anomalies[aid]["name"],
)

# If this is the first time we've seen this Anomaly selected in this
# session (either the app just started, or the student just switched to a
# different Anomaly in the dropdown), pull that Anomaly's saved progress
# back into session_state so the streak/question picks up where it left off.
if st.session_state.get("current_anomaly") != selected_id:
    st.session_state.current_anomaly = selected_id
    saved = get_anomaly_progress(st.session_state.progress, selected_id)
    st.session_state.question_index = saved["question_index"]
    st.session_state.streak = saved["streak"]
    st.session_state.cleared = saved["cleared"]

anomaly = anomalies[selected_id]
questions = anomaly["questions"]

st.caption(anomaly["description"])

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

    # Phase 1/2: fake the AI verdict with a dropdown instead of a real API call
    fake_verdict = st.selectbox(
        "Mock AI verdict (stand-in for real AI later):",
        ["resolved", "thin", "wrong"],
    )

    if st.button("Submit"):
        if is_vacuum_box:
            # Grade the NUMBER with real physics, not string matching.
            force_is_correct = check_vacuum_box_force(student_force)
            if force_is_correct:
                st.info(vacuum_box_feedback(student_force))
            else:
                st.warning(vacuum_box_feedback(student_force))

            # The real calculation always has the final say on the
            # numeric part: if the force value is wrong, the verdict is
            # "wrong" no matter what the mock-AI dropdown says. If the
            # force value is right, we still fall back to the mock-AI
            # dropdown to judge the quality of the written explanation
            # (that's the part real AI will grade in a later phase).
            verdict = fake_verdict if force_is_correct else "wrong"
        else:
            verdict = fake_verdict

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
