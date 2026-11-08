# Native barrier-pivot family

`turn_barrier=nearest` is the exact canonical program. `farthest` scans the
same target-facing ray but selects the farthest nonzero barrier. In both rules,
step A identifies a barrier and derives the preceding pivot; step B consumes
that pivot to build the remaining orthogonal route to the red segment.

The adapter exposes 2–6 demonstrations and 1–4 prefix-stable queries. Inputs
are identical across settings. Every authored scene has three separated ray
barriers, later-leg distractors, both orientations/directions across the bank,
and the fourth query is a substantive 30×30 case.
