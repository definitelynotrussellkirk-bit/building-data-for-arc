# Solve work log

## Prior exposure declaration

I had already inspected this task's generator and canonical rule while repairing it, so this is an exposed post-repair solve rather than a blind solve. After `prepare`, I did not reopen the generator, Racket source, reference solutions, private labels, or earlier solution explanations. I used only the visible presentation produced by `prepare` and this work log.

## Revision 1 — color-ranked markers become periodic bands

The visible outputs replace sparse marker cells with full horizontal rows or full vertical columns. I inferred that the two lowest nonzero colors are the active markers: visible training example 2 contains colors 2, 5, 7, and 9, but only 2 and 5 appear in the output, so the larger-color dots are distractors rather than additional phases.

For the selected markers, compare absolute row and column separation. The output uses horizontal bands when the row separation is the smaller positive separation (or the markers share a column); otherwise it uses vertical bands, with equality going to columns. On the active axis, each marker fixes one phase. Those two phases repeat every twice their separation, while positions before the earlier active-axis coordinate remain blank. Every active phase fills the complete perpendicular row or column.

The solver implements that hypothesis directly and deliberately ignores all nonselected markers. Remaining uncertainty before checking: the visible set supports color-first selection and the strict row/column tie rule, but prior exposure means this record is not independent evidence that I discovered those details without source knowledge.
