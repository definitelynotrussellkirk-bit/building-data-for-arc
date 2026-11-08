# Solve work log

## Exposure before solving

I had not opened the task's generator, Racket rule, reference solution, private
labels, audit records, or earlier explanations. I used only the visible grids
printed by `python3 review.py blind prepare` and `challenge.json`.

## Attempt 1 — seeded compartment fill

**Hypothesis.** Colors 9 and 5 form closed frames and internal divider walls.
Every other nonzero color is a seed inside one 4-connected zero compartment.
The output paints the whole compartment with the seed color while preserving
walls, dividers, exterior background, and unseeded compartments.

**Evidence from the demonstrations.** In train 0, the color-1 seed fills the
upper-left compartment and the color-3 seed fills the lower-left compartment.
In train 1, the color-4 seed fills only the lower-right compartment. In train 2,
the color-6 and color-4 seeds independently fill their respective compartments,
even though the divider locations and compartment sizes differ.

**Implementation.** Traverse every 4-connected component after treating 5 and 9
as blocked cells. If the component contains exactly one distinct nonzero color,
replace all of its zero cells by that color. Components with no seed or multiple
seed colors are left unchanged. The distinct-color guard is a conservative
choice for an unseen ambiguous case.

**Remaining uncertainty.** The visible lessons do not show two differently
colored seeds in one compartment. Leaving such a component unchanged avoids
inventing a priority rule.
