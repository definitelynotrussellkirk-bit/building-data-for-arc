# Exposed post-repair solve: a06827026857

## Exposure declaration

I reviewed the generator and Racket authority during the preceding repair.
I therefore remember the intended transformation; this is an exposed solve,
not an independent blind inference. Since preparing this episode I have opened
only its public preparation output. I have not consulted generator source,
the Racket rule, prior solutions, or private labels during this solve.
These notes are an authored work log, not a token-level reasoning trace.

## Visible observations

Example 0: Input 8 rows x 10 columns; output 8 rows x 10 columns.
Example 1: Input 15 rows x 16 columns; output 15 rows x 16 columns.
Example 2: Input 9 rows x 9 columns; output 9 rows x 9 columns.
Query inputs are 16x9 and 9x9; query output dimensions and answers are unknown.

Examples 0 and 2 preserve only four corners of each solid 3x3 square, retaining
the original color. Example 1 distinguishes several rival interpretations:
its 3x4 color-2 rectangle keeps both complete outer rows, not just its four
bounding-box corners. Its two color-8 objects remain separately represented,
so a single bounding box per color is insufficient. The extra color-8 cell
at (1,13) disappears rather than being copied through.

## Hypothesis and implementation, revision 1

Find every nonzero monochrome 3x3 neighborhood in the original input. Paint
the four corners of every such neighborhood onto a blank grid. Read only the
input while finding matches, so overlapping neighborhoods are all considered;
combine their output corners. This explains the wider rectangle's retained
outer rows and the discarded appendage in example 1.

I implemented the rule using neighborhood centers and wrote to a separate
output grid. I did not create a deliberately wrong revision. I will check this
first genuine attempt with the visible-only checker; success means visible
agreement and executable query predictions, not verified hidden answers.
