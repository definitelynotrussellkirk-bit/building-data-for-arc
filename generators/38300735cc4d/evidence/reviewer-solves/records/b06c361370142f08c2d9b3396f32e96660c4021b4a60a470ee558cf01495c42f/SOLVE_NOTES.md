# Visible-only solve: 38300735cc4d

These are concise hypothesis and experiment summaries, not a token-level trace.
Sources consulted: this folder's README.md and challenge.json, plus the blind
solve and return-tool directions in WORK/DUTIES.md and WORK/RETURN-GUIDE.md.
No generator, Racket rule, canonical data, reference solution, private answer,
prior solution explanation, or audit record was consulted. Earlier rule exposure: no.

## Revision 1

Hypothesis: for each nonzero color occurring exactly twice in the entire input,
connect its two cells if they share a row or column and every intervening cell is
zero. Fill the intervening cells with that color. Preserve everything else.

Visible evidence:

- Demonstrations 0 and 3 show clear horizontal and vertical pairs connected.
- In demonstration 1, the two 3 cells are blocked by 5 and the two 1 cells are
  blocked by 4; neither span is filled. The clear 8 pair is filled.
- Demonstrations 1 and 2 retain colors with three occurrences. In demonstration
  2, the three 6 cells share a column, so alignment alone is insufficient.
- Demonstration 4 retains the two 4 cells because they are not axis-aligned,
  while filling the aligned 9 and 5 pairs.

Implementation evaluates eligibility against the original input and writes to a
copy, preserving the original grid. Crossings between two newly drawn spans are
not distinguished by these visible examples; no wider-domain claim is made.

Planned probe: use the official visible-example check on this first genuine
attempt. This tests the joint occurrence-count, alignment, and obstruction
conditions against all five demonstrations. No artificial failed revision was
created.
