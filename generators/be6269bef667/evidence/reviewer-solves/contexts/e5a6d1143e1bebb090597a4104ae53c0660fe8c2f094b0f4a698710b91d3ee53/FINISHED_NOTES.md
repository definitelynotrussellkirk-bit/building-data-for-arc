# Solve work log

## Exposure declaration before solving

I had not opened this task's generator, Racket rule, reference solution, private
query labels, audit evidence, or any earlier explanation. I used only the visible
examples printed by `python3 review.py blind prepare` and my own local calculations.

## Revision 1 — diagnostic baseline

The prepared stub raised `NotImplementedError`. I ran the checker once as a
`diagnostic_probe` to establish that the unimplemented program failed for the
expected reason before changing it.

## Observations and hypothesis

The sparse nonzero cells split naturally into emitters (colors 1–4) and blockers
(color 5). The visible outputs suggested the direction mapping:

- 1 emits upward;
- 2 emits rightward;
- 3 emits downward;
- 4 emits leftward.

Each ray starts on its emitter and continues to the grid boundary unless it first
reaches a color-5 cell. A blocker is left as zero and terminates that ray. The
output value is the number of unblocked rays covering each cell.

The decisive probe was the repeated vertical configuration. In train example 1,
a downward color-3 emitter at `(0, 2)` and an upward color-1 emitter at `(6, 2)`
would overlap if unobstructed, but the color-5 cell at `(3, 2)` splits the column:
the visible output has ones above and below it and zero at the blocker. In train
example 0, the leftward color-4 emitter at `(5, 7)` similarly stops at the
color-5 cell `(5, 1)`, painting only columns 2 through 7. Summing all such rays
reproduced every visible output cell exactly in a separate scratch calculation.

I considered two alternatives and rejected them:

1. connecting paired emitters with line segments — this could not explain rays
   that continue to a boundary without a paired endpoint;
2. painting raw ray overlap without blockers — this overcounted the vertical
   columns and painted through every color-5 cell.

## Revision 2 — implementation

I implemented the four direction vectors, traced each emitter ray, stopped before
color 5, and incremented an integer output grid. Remaining uncertainty is limited
to unseen malformed/ragged inputs; the visible ARC instances are rectangular and
the inferred transformation fits all three training pairs exactly.
