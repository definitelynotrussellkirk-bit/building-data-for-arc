# Solve work log

I had no earlier exposure to this task's generator, Racket rule, private labels,
or prior solution notes. I used only the visible examples prepared in this lane.

## Revision 1

Hypothesis: the unique color outside `{1, 2, 5}` is a trace. It starts by
reaching the nearest axis-aligned blue/red guide. At every guide the trace turns
90 degrees, alternates blue and red while an opposite-color guide remains, and
then aims at gray. An aligned target is reached and consumed. If the next target
is off the required axis, the trace turns toward that target's row/column but
continues to the border. Unused guide points are distractors.

Evidence from the visible examples:

- Example 1 follows `7 -> blue -> red -> gray` through three aligned segments.
- Example 3 follows `8 -> blue -> red -> blue -> gray`, preferring the blue
  point aligned with the required horizontal turn over an off-axis blue point.
- Example 2 follows `3 -> red -> blue`; both gray candidates are off-axis, and
  the closer row determines a downward ray to the border.
- Example 0 follows `6 -> blue`; the off-axis red point selects the leftward
  border ray.

The implementation keeps guide colors unchanged, paints only background zeros,
prefers aligned legal-turn targets, and uses deterministic nearest-axis tie
breaking for off-axis targets. Remaining uncertainty: the visible set does not
show ties between two equally aligned targets or an input whose initial
blue/red guide is not axis-aligned.
