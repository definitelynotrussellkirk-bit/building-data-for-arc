# Solve work log

## Earlier exposure

I had already inspected this task's generator and canonical Racket rule during the assigned repair, so this is **not blind**. During this solve phase I kept those sources, prior solution explanations, and private labels closed and used only the newly prepared visible examples.

## Revision 1 hypothesis

Across all three visible examples, exactly one cell changes from blue (`1`) to red (`2`). The changed object is always an isolated horizontal blue component of length 9, and the changed cell is its center.

The examples independently rule out several simpler alternatives:

- Train 0 leaves a horizontal blue length-4 component unchanged, so parity matters.
- Train 0 leaves a vertical blue length-3 component unchanged, so orientation matters.
- Train 0 and Train 1 leave bent blue objects with a horizontal run of length 3 unchanged, so the rule must classify the whole 4-connected component rather than each row-run.
- Train 1 and Train 2 leave a non-blue horizontal length-3 component unchanged, so source color `1` matters.
- Train 1/2 leave blue singletons unchanged, so an odd size alone is insufficient.

Hypothesis: find each 4-connected same-color component of color `1`; when the whole component is a single contiguous row, has odd length, and has length at least 3, replace its middle cell with `2`. Preserve everything else. I implemented component traversal rather than row-run scanning specifically to handle the visible bent-object counterexample.

Remaining uncertainty before checking: all positive visible objects have length 9, so the lower bound of 3 is inferred from the explicit negative singleton and the usual simplest odd-line generalization; the visible data do not contain a positive length 3/5/7 example in this sampled lesson.
