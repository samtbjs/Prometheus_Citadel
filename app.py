import streamlit as st
from logic.streak_engine import MOCK_QUESTIONS, check_answer, update_streak, is_anomaly_cleared

st.title("PARADOX — Anomaly Room (Phase 1 Prototype)")

# Set up session state so Streamlit remembers values between interactions
if "question_index" not in st.session_state:
    st.session_state.question_index = 0
if "streak" not in st.session_state:
    st.session_state.streak = 0
if "cleared" not in st.session_state:
    st.session_state.cleared = False

if st.session_state.cleared:
    st.success("🎉 Anomaly Cleared!")
    if st.button("Restart"):
        st.session_state.question_index = 0
        st.session_state.streak = 0
        st.session_state.cleared = False
        st.rerun()
else:
    q = MOCK_QUESTIONS[st.session_state.question_index]
    st.subheader(q["prompt"])
    student_answer = st.text_input("Your answer:")
    explanation = st.text_area("Explain your reasoning in one sentence:")

    # Phase 1: fake the AI verdict with a dropdown instead of a real API call
    fake_verdict = st.selectbox("Mock AI verdict (stand-in for real AI later):", ["resolved", "thin", "wrong"])

    if st.button("Submit"):
        st.session_state.streak = update_streak(st.session_state.streak, fake_verdict)
        st.session_state.question_index = (st.session_state.question_index + 1) % len(MOCK_QUESTIONS)

        if is_anomaly_cleared(st.session_state.streak):
            st.session_state.cleared = True

        st.rerun()

    st.metric("Current Streak", st.session_state.streak)