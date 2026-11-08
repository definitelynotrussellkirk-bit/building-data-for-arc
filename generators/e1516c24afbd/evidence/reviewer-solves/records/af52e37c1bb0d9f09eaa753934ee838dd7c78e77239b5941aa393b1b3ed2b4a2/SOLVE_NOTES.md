# Solve notes

The visible examples all have an even number of rows and an output with half the input height and the same width. I split each input into equal top and bottom panels and compared aligned cells.

Hypothesis: output `(r,c)` is color 2 exactly when the top-panel cell and the aligned bottom-panel cell are both background 0; every other occupancy combination maps to 0. This explains all visible positives and negatives:

- train 1 row 0 has aligned pairs `(0,0)`, `(8,4)`, `(0,0)`, giving `2,0,2`;
- train 2 has only two both-zero alignments, matching its two 2s;
- train 3 distinguishes one-sided zeros from both-zero cells.

Implementation directly evaluates that aligned Boolean condition. No reference source was consulted during this solve. I had earlier rule exposure from the generator-review phase, so this is an exposed post-repair solve rather than a blind solve.
