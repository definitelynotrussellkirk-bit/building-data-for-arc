# Post-repair visible-only solve: 28268c57c367

## Exposure declaration
This is NOT blind. I read the rule and generator during the preceding repair.
For this phase I opened only `solve/challenge.json`, not generator code, rule
source, previous solution explanations, reference solutions or private labels.
These notes are an authored work log, not a token-level model trace.

## Visible observations
There is a full-height column of 5s in each input. In examples 0 and 2, each
colored source extends across zeros to its right up to, but not including,
that wall; columns to its right are unchanged.

The middle demonstration supplies the decisive details. Its row `1009000500`
becomes `1119111500`: 9 is preserved, while blanks beyond it become 1, not 9.
Its row `1530000500` becomes `1531111500`: both the isolated 5 and the later
3 are preserved, and the fill crosses the isolated 5. The row `0000050500`
does not change: an isolated 5 is not itself a source. Colored cells right of
the wall are retained without projection.

## Revision 1
Find the full-5 wall. For each row, find its first nonzero, non-5 cell left of
the wall. Replace only originally zero cells after this source and before the
wall by that source's color. Keep all other cells unchanged. This is the
smallest rule accounting for these three visible demonstrations. No artificial
failed revision is added. Validate on visible examples and submit the genuine
attempt; query correctness is withheld and must remain unknown here.
