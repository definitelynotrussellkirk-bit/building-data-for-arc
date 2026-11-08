# Working notes: 1b7cbdffd485

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## Current parametric decision (review-a437e4dcd0444214)

- Keep the canonical row-major first-hit program byte-for-byte as
  `output_order=first_seen`; add `reverse_first_seen` as the sole alternative.
- A first attempt varied scan order. Its minimum two-demo lesson was rejected:
  the row-major setting could be observationally identical to `always_row`.
  More generally, on a fully colored grid the top-left color makes the reverse
  orientation disagreement impossible: `max(top_row) <= max(leftmost_row)` and
  `max(leftmost_col) <= max(top_row_col)`, so row-major vertical dominance plus
  column-major horizontal dominance would imply a strict inequality cycle.
- The replacement family retains the source dependency: first-hit triples are
  computed from each input, then their spans and ordered colors determine the
  final vector. The two mandatory lessons contain one exact tie/column case and
  one horizontal/row case, so fixed-orientation and strict-tie shortcuts fail
  without increasing the minimum demonstration count.
- The bounded self-audit covers numeric order, frequency order, column-major
  order, four fixed-orientation/order combinations, and two strict-tie rules.
  Scope is finite, not a universal uniqueness claim.
- Reviewer status is `ready` only after current-source native qualification;
  owner acceptance remains pending after integration.
