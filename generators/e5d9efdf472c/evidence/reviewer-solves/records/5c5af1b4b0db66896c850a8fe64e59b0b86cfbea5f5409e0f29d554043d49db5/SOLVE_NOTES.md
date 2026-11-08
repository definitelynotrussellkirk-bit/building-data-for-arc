# Blind solve notes — e5d9efdf472c

## Revision 1 — intended solve

Observed invariant across all four demonstrations:

- Exactly two magenta (`6`) cells share a row or a column.
- The output preserves every existing cell and replaces the zero cells strictly
  between those two `6` endpoints with azure (`8`).
- The other nonzero color is a distractor. It is never used as an endpoint,
  even when two cells of that color happen to occur (training examples 3–4).

Planned rule: find the two `6` cells; if horizontally aligned, fill the open
horizontal interval with `8`; if vertically aligned, fill the open vertical
interval with `8`. Preserve nonzero cells defensively rather than overwriting
an unexpected crossing object.

Visible predictions:

- Test 1: fill row 5, columns 2–6 (zero-indexed), between `(5,1)` and `(5,7)`.
- Test 2: fill column 3, rows 1–4, between `(0,3)` and `(5,3)`.

No generator, reference rule, private label, prior solution, or task-specific
notes were consulted.
