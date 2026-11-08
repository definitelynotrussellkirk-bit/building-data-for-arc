# Post-repair solve notes

This is an exposed solve: I had already inspected the task generator and authority during repair work. During this solve episode I used only `solve/challenge.json` and did not reopen the generator, Racket rule, reference solutions, or private labels.

## Hypothesis 1

Treat each nonzero same-color 4-connected component as a separate object. Replace each object by a horizontal run of its color whose length is the object's cell count. Order runs by decreasing object size, use ascending color as the tie-break, and insert one zero between runs.

Evidence from the visible pairs:

- Train 1 contains a size-5 color-9 object, a size-2 color-7 object, and a disconnected size-1 color-9 object. Its output preserves the two color-9 components as separate runs and orders them 5, 2, 1.
- Train 2 has size-2 objects of colors 6 and 7; the output places color 6 before color 7, identifying the tie-break.
- Train 3 confirms decreasing size on a two-object scene.

Predicted tests:

- Test 1: size-6 color 5, separator, size-2 color 5.
- Test 2: size-5 color 4, then tied size-3 colors 3 and 7 in ascending-color order.

I implemented this rule directly with a 4-neighbor flood fill. No diagnostic or deliberately wrong attempt was needed because the visible examples separately expose component identity, size ordering, and the color tie-break.
