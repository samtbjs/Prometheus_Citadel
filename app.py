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

st.title("Prometheus Lab — Anomaly Room (Phase 2 Prototype)")

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

    student_answer = st.text_input("Your answer:")
    explanation = st.text_area("Explain your reasoning in one sentence:")

    # Phase 1/2: fake the AI verdict with a dropdown instead of a real API call
    fake_verdict = st.selectbox(
        "Mock AI verdict (stand-in for real AI later):",
        ["resolved", "thin", "wrong"],
    )

    if st.button("Submit"):
        st.session_state.streak = update_streak(st.session_state.streak, fake_verdict)
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
