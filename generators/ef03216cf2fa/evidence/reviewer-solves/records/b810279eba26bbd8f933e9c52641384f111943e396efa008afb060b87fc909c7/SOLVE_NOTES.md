# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Initial visible-only analysis

Earlier exposure: none to this task's rule or generator. I used only the displayed train/test grids.

Hypothesis: each nonzero connected object is cropped. Objects are ordered by decreasing colored-cell count, with row-major source order as the tie-breaker. A crop taller than it is wide is rotated 90 degrees clockwise; square or already-wide crops keep their orientation. The normalized objects are left-aligned in a canvas whose width is the largest object bounding-box dimension, with one all-zero separator row between consecutive objects.

Evidence: in train 0 the 7-cell and 6-cell tall objects become their clockwise rotations and precede the 4-cell and 3-cell objects; in train 1 the two 5-cell objects retain their source order; all three outputs use exactly one blank separator row and width four, the maximum bounding-box side.

Remaining uncertainty: whether equal-area objects use row-major order or another stable ordering. Train 1 supports row-major/stable order, so I use that deterministic tie-breaker.
