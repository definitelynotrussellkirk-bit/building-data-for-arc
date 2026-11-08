# Solve work log

## Exposure declaration before solving

I had already seen and worked with the task's canonical rule during the generator-review phase. Therefore this is not a blind solve (`earlier-exposure=yes`). During this solve phase I did not reopen the generator, Racket source, reference solutions, private labels, or earlier solution explanations; I used only the prepared visible examples and my own implementation.

## Revision 1

Hypothesis from the visible examples: find each same-color 4-connected nonzero component independently, record `(area, color)`, sort by decreasing area and then increasing color, and concatenate one run per component with run length equal to its area.

Evidence in the visible examples:

- Train 1 has two disconnected color-3 components, of areas 6 and 3. The output contains two separated color-3 runs around the area-5 color-2 and area-4 color-8 runs, disproving aggregation by total color frequency.
- Train 2 has area-5 components of colors 3 and 8. Color 3 precedes color 8, showing the ascending-color tie-break.
- In every example, output length equals total nonzero input area and the output is a single row.

Implementation: breadth-first search over 4-neighbors, then sort by `(-area, color)`. The empty fallback is `[0]`, though no visible example is empty.
