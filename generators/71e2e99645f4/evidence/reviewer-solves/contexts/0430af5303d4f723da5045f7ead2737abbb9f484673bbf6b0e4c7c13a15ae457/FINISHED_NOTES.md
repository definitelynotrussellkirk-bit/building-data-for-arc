# Solve work log

## Exposure declaration before solving

I had already inspected this task's generator and canonical rule while repairing
it, so this is **not blind**. During this solve episode I used only the visible
examples printed by `solve prepare` and did not reopen the generator, Racket
source, canonical data, reference solutions, or private query labels.

## Revision 1 — exact section-signature classifier

The visible inputs are all `4×14`. Columns 4 and 9 are all-zero dividers, leaving
three `4×4` sections starting at columns 0, 5, and 10. Each output is `3×3`, and
one output row corresponds to one input section.

Across the three visible examples I observed four exact zero signatures:

- no zeros gives a row of `2`;
- the central four cells (rows 1–2, local columns 1–2) give `8`;
- the bottom four cells (rows 2–3, local columns 1–2) give `4`;
- the middle cells on both vertical edges (rows 1–2, local columns 0 and 3)
  give `3`.

The fill color changes between examples but does not affect the class. I encoded
those four signatures directly and repeat each class three times. For the visible
queries this predicts section classes `(2,4,3)` and `(2,8,3)` respectively.

I stopped after one implementation because it explains every visible pair
without an unsupported fallback. Unknown signatures raise instead of silently
inventing a label.
