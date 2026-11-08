# Final-source exposed solve work log

This is an authored work log, not a captured model transcript. Earlier rule
exposure is **yes**: I previously inspected and repaired the canonical generator.
During this new solve I consulted only the freshly prepared public grids. I kept
the reference, generator, private labels, canonical helpers and prior solution
files closed. An earlier genuine exposed solve is retained in checks/prior-solve
because the optional period metadata was later withdrawn, changing source hash.

## Visible evidence

The four demonstration input/output dimensions are 10×10/10×10,
12×11/12×11, 11×12/11×12 and 12×11/12×11. Output shape is preserved.
In demonstration 0, row 5 has three color-5 anchors at columns 2,4,8 and the
output fills every gap from column 2 through 8. In demonstration 1, row 1 has
separate color-8 and color-9 spans; the inter-span zeros stay zero. In
demonstration 2, row 4's singleton color 6 at column 10 stays a singleton while
the three color-7 anchors delimit a filled span. In demonstration 3, row 0
shows that a span may start at the left border.

## First actual attempt

For each row, collect original positions independently for each nonzero color.
Fill original zero cells strictly between that color's first and last positions.
Preserve all original nonzero cells. Singletons have an empty fill interval.
I wrote and submitted this as revision 1. No deliberately wrong answer was
submitted, and no failed model trajectory was fabricated.

## Stopping criterion and limits

Stop after all four public examples match and both masked queries execute.
The checker withholds masked-query correctness. This is explicitly an exposed
post-repair record and supplies no claim of blind task generalization.
