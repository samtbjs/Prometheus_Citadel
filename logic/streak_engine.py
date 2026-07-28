

MOCK_QUESTIONS = [
    {
        "id": 1,
        "prompt": "A box floats motionless in a vacuum. What net force acts on it?",
        "answer": "zero",
    },
    {
        "id": 2,
        "prompt": "If the box is motionless, what does that tell you about the forces acting on it?",
        "answer": "balanced",
    },
]

def check_answer(question_index, student_answer):
    """Very simple check — does the student's answer contain the expected keyword?"""
    correct_answer = MOCK_QUESTIONS[question_index]["answer"]
    return correct_answer.lower() in student_answer.lower()

def mock_tag_explanation(tag_choice):
    """
    Phase 1 fakes the AI verdict — you'll pick it from a dropdown instead of calling GPT.
    tag_choice will be one of: 'resolved', 'thin', 'wrong'
    """
    return tag_choice

def update_streak(current_streak, tag):
    """Returns the new streak count based on the verdict tag."""
    if tag == "resolved":
        return current_streak + 1
    else:
        return 0  # thin or wrong resets the streak

def is_anomaly_cleared(streak):
    return streak >= 2