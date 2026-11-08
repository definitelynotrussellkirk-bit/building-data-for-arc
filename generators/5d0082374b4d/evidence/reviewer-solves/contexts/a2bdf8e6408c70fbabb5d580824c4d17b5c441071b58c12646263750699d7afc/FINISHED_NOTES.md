# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Attempt 1

Observed that every non-background object is a complete rectangular frame made
of color 1.  Each frame contains exactly two nonzero, non-frame colors in its
interior, ordered left-to-right.  The output preserves the frame and replaces
all interior cells with a horizontal alternation of those two colors, beginning
with the left seed; the same row is repeated through the frame's full interior
height.  This explains widths 3 and 4 and all frame heights in the three visible
training examples.

Implementation: find 4-connected color-1 components, require each component to
be exactly a rectangular perimeter, read its two interior seed colors, and fill
the interior with the alternating motif.  Remaining uncertainty: the visible
examples do not show touching frames or seed colors on different rows; the
component/perimeter guard avoids modifying unrelated color-1 shapes.
