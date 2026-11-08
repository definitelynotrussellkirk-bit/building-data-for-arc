# Solve work log

## Exposure declaration

This is the required post-repair solve. I had already inspected this task's generator, canonical examples, and rule behavior during the repair, so earlier rule exposure is **yes**. During this solve episode I used only the newly prepared `solve/challenge.json` and local analysis of its visible train pairs. I did not reopen the generator, Racket rule, reference solutions, prior solve explanation, or private query labels.

## Revision 1

Across all four visible examples, every changed cell is a `0 -> 3` transition. Each changed zero has immediate horizontal neighbors `7` and `7`, including overlapping chains such as `7,0,7,0,7`. Zeros in vertical alignments, zeros flanked by color 6, longer orange gaps, adjacent orange markers, isolated markers, and all nonzero cells remain unchanged.

Hypothesis: copy the input and recolor exactly each center of a horizontal `[7, 0, 7]` slice to `3`. Scan the original input rather than the evolving output so overlapping targets are detected from the source scene.

The rule is local, deterministic, shape preserving, and explains every visible difference with no extra edits. Remaining uncertainty is limited to masked-query scoring; the visible examples are internally decisive.
