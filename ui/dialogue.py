"""
MILESTONE 6: reusable "reveal one line at a time" dialogue helper. Any
scene that wants ARBITER (or anyone) to speak several lines in sequence
-- each one only starting once the previous has fully appeared -- calls
the two functions below instead of building a bespoke version per scene.
Mission Briefing (scenes/briefing.html) is the first user of this; the
Debrief scene's single fixed line is untouched since it never needed
sequencing.
"""


def build_dialogue_lines_html(lines, css_class="dialogueLine", id_prefix="dialogueLine"):
    """One <div> per line, each with its own id so the JS timeline below
    can reveal them in order."""
    return "".join(
        f'<div class="{css_class}" id="{id_prefix}{i}">{line}</div>'
        for i, line in enumerate(lines)
    )


def build_dialogue_reveal_js(line_count, id_prefix="dialogueLine", start_delay=0.5, gap=1.3, duration=0.6):
    """GSAP timeline that fades/rises in #{id_prefix}0, #{id_prefix}1, ...
    one at a time, each starting `gap` seconds after the previous one
    started -- roughly 1-1.5s apart, per this feature's spec, with
    `duration` shorter than `gap` so each line finishes appearing before
    the next begins."""
    steps = "\n".join(
        f'  .from("#{id_prefix}{i}", '
        f'{{ opacity: 0, y: 10, duration: {duration}, ease: "power2.out" }}, '
        f'{round(start_delay + i * gap, 2)})'
        for i in range(line_count)
    )
    # MILESTONE 7: no trailing ";" here -- the caller (scenes/briefing.html)
    # wraps this expression in pmSkip(...) so the reveal can be jumped
    # straight to its end state under reduced motion; the ";" is added
    # there, after the closing paren of pmSkip(...).
    return f"gsap.timeline()\n{steps}"
