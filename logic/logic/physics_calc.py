"""
logic/physics_calc.py

PHASE 3: Real physics calculations (not string matching).

So far, only ONE Anomaly has a real calculation behind it: "vacuum_box"
(the box floating motionless in a vacuum). The other two Anomalies
(sinking_stone, hot_cold_chairs) still use the old fake-AI-verdict flow
from Phases 1/2 -- they are untouched in this phase.

--------------------------------------------------------------------------
THE PHYSICS, IN PLAIN ENGLISH
--------------------------------------------------------------------------
Newton's First Law says: an object that is NOT accelerating (i.e. it's
either sitting still, or moving in a straight line at constant speed) must
have a net force of exactly ZERO acting on it. It doesn't matter how many
individual forces are pushing or pulling on it -- as long as they all
cancel out, the object won't speed up, slow down, or change direction.

The "vacuum_box" Anomaly is a box floating motionless in a vacuum chamber.
There's no air resistance, no friction, nothing touching it, and it's not
moving. So the net force on it has to be 0 Newtons.

--------------------------------------------------------------------------
WHY A NUMBER INSTEAD OF TEXT?
--------------------------------------------------------------------------
The student is asked to type in their numeric guess for the net force, in
Newtons (N). We then check that number with real arithmetic -- is it close
enough to 0? -- instead of checking whether they happened to type the word
"zero" somewhere in a sentence. That's what makes this a genuine
calculation rather than a keyword match.
"""

# How close to exactly 0 the student's number has to be to count as
# correct. We use a small tolerance rather than demanding *exactly* 0.0,
# since floating-point numbers (and typing) are never perfectly exact.
VACUUM_BOX_FORCE_TOLERANCE = 0.01  # Newtons


def check_vacuum_box_force(net_force_guess):
    """
    Real physics check for the "Floating Box" Anomaly.

    Takes the student's numeric guess for the net force on the box (in
    Newtons) and returns True if it's within a small tolerance of 0,
    False otherwise.

    This is the actual calculation: abs(guess) <= tolerance. No string
    comparison happens here at all.
    """
    return abs(net_force_guess) <= VACUUM_BOX_FORCE_TOLERANCE


def vacuum_box_feedback(net_force_guess):
    """
    Returns a short, plain-English explanation of why the guess was right
    or wrong, based on the actual number the student typed in.
    """
    if check_vacuum_box_force(net_force_guess):
        return (
            "Correct -- the net force is essentially zero. That matches a "
            "box that just sits there, motionless."
        )
    elif net_force_guess > 0:
        return (
            f"Not quite. A net force of {net_force_guess} N would push the "
            "box in one direction and it would start moving -- but the box "
            "stays put."
        )
    else:
        return (
            f"Not quite. A net force of {net_force_guess} N would push the "
            "box in the opposite direction and it would start moving -- but "
            "the box stays put."
        )
