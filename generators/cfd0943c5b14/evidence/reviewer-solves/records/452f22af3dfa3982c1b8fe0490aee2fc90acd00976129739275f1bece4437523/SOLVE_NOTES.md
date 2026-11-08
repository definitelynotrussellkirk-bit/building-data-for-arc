# Visible-only solve notes: cfd0943c5b14

This is a human-readable reasoning log for the exposed post-repair episode. I had already seen the task rule while reviewing its generator, so this is **not blind**. During this solve phase I consulted only `solve/challenge.json`; I did not reopen the generator, Racket rule, reference solution, private labels, or earlier solution explanations.

## Revision 1 — diagonal-X stencil from every nonzero cell

The four visible demonstrations support one direct transformation:

- Start with a fresh all-zero output of the same dimensions.
- Treat every nonzero input cell as a seed, regardless of its input color. This is forced by the third example, where seeds of colors 8, 3, and 9 all behave the same, and the fourth, where color 1 behaves the same.
- For each seed at `(r, c)`, paint cyan (`8`) at the seed and at its four diagonal neighbors: `(r±1, c±1)`.
- Clip positions outside the grid. The second and fourth examples show boundary/corner clipping.
- Union all stamps; overlaps remain cyan. The third example shows overlapping diagonal-X footprints.

I implemented this rule directly. No failed natural revision preceded it because the visible examples disambiguate the color, boundary, and overlap cases explicitly.
