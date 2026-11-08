# Solve work log

## Exposure declaration before solving

I had already read and tested this task's generator and canonical rule during the repair, so this is **not blind** and must finish with `earlier-exposure yes`. During this episode I consulted only `solve/challenge.json`, this solution file, my notes, and the visible-only checker. I did not reopen the generator, Racket source, reference solutions, or private labels.

## Revision 1 — exactly-two axis-aligned bridge

Visible-example observations:

- In train 1, color 3's two vertical endpoints, color 5's two horizontal endpoints, and color 2's two vertical endpoints are filled inclusively. Color 6 has three occurrences and is not filled despite alignment. Color 7 has two diagonal occurrences and is unchanged. The singleton 8 is unchanged.
- In train 2, exact horizontal/vertical pairs 4, 5, and 6 are filled. Three-occurrence color 8 and diagonal exact pair 3 are unchanged.
- Train 3 confirms the same behavior with one horizontal and one vertical exact pair.

Hypothesis: collect every nonzero color independently. Only a color occurring exactly twice is eligible; fill the inclusive straight segment when the two cells share a row or a column. Leave diagonal pairs, singletons, and colors with any other multiplicity unchanged.

Implementation: copy the grid, index positions by color, and paint only eligible row/column ranges. This deliberately does not connect every aligned pair among a triple and does not invent an L-shaped path for diagonal endpoints.

Remaining uncertainty before checking: none material on the visible examples; the main ambiguity is whether endpoint count or pairwise alignment dominates, and the three-occurrence/diagonal negatives resolve both.

Visible-only check result: revision 1 executed successfully and passed all 3/3 visible training examples. I stopped after this single genuine revision because every observed positive and negative case is explained by one compact rule; further revisions would be manufactured rather than evidence-driven. Masked-query correctness remains intentionally unknown.
