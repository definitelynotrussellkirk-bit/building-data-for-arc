# Solve work log

## Exposure declaration

Before this visible-only solve I had already reviewed the assigned generator and its canonical rule while repairing the task, so earlier rule exposure is **yes**. After `solve prepare` I kept the generator, Racket source, reference solutions, private labels, blind-solve notes, and earlier solution explanations closed. This work log uses only `challenge.json`, the rendered visible examples, and my own Python checks.

## Revision 0 — scaffold

The supplied `solution.py` raised `NotImplementedError`. I wrote `/tmp/test_arc_solve.py` to load the candidate and compare it with all three visible training pairs. The test failed immediately at the scaffold, establishing the red test before implementation.

## Visible pattern

Each input is a field of vertical color-8 rails on color 7. Exactly one maximal vertical rail is mixed 8/9; its color-9 cells form a block at the top or bottom end. The output restores those source 9s to 8. It then selects the unique all-8 vertical rail whose length is two greater than the mixed source rail, paints at the corresponding end, and uses one more 9 cell than the source block contained.

The three examples agree on object selection and direction: source length determines the target, the end of the source block determines which end of the target is painted, and output block length is `number of input 9s + 1`. A tempting “paint half the target” description happens to agree when the source has one 9, but query 0 visibly has three input 9s, so the count-transfer-plus-one formulation is the general hypothesis used in code.

## Revision 1 — generic rail solver

Implemented maximal vertical-run extraction, unique mixed-source selection, target-by-length selection, source clearing, and same-end painting. The solver deep-copies the grid and raises on ambiguous malformed scenes rather than silently choosing a rail. I stopped after the generic implementation passed all visible training examples; no private query answer or reference implementation was consulted.
