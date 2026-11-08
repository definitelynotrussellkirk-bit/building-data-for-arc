# Solve work log

## Exposure declaration

I had earlier exposure to this task's intended rule while repairing the generator. During this fresh solve episode I consulted only the newly prepared visible challenge/README and my own Python solution; I did not consult the Racket rule, generator source, reference solutions, private labels, or the archived prior solve.

## Revision 1 — visible-example hypothesis

Across all three demonstrations, each maximal horizontal run of color 6 with length at least two receives color 8 in each in-bounds background cell immediately before and after the run. A run touching the left or right edge receives only the available cap. Isolated 6-cells stay unchanged, including two singletons that happen to be vertically adjacent. All other cells are copied.

I implemented a row scan that finds maximal 6-runs, ignores length-one runs, and paints the two possible neighboring zero cells. The visible examples deliberately include lengths 2, 3, and 4, edge-touching runs, and singleton/vertical distractors, so this hypothesis is distinguishable from cap-any-6, canonical-length-only, and interior-only alternatives.

Remaining uncertainty before check: private query correctness is intentionally hidden, but the visible demonstrations fully determine this local transformation.
