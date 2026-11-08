# Exposed solve work log

Earlier exposure: yes. I had already reviewed the assigned generator before this required post-repair solve, so this is not a blind record. During this solve phase I used only the displayed examples and `solve/challenge.json`; I did not reopen the generator, Racket rule, private labels, or prior solution records.

## Hypothesis

The nonzero color other than 1 forms several rectangles represented only by four disconnected 3-cell L corners. Color-1 cells outside every such rectangle are distractors and disappear. Within each rectangle, the color-1 motif occupies one side of a horizontal or vertical centre line; the output keeps it and reflects it across the indicated centre line to complete a symmetric pair.

I identify the rectangle from the orientation and aligned outer vertex of each L corner. For each enclosed motif I test horizontal and vertical one-sidedness. When both are possible because a motif touches a centre line, the examples select the axis that creates the larger non-overlapping counterpart; a tie is resolved deterministically.

## Expected failure modes / limits

- The visible examples do not establish behavior for malformed corners, overlapping rectangles, multiple frame colors in one grid, or a motif that is equally one-sided and equally non-overlapping on both axes.
- The solver intentionally removes every color-1 cell not enclosed by a detected four-corner frame.
