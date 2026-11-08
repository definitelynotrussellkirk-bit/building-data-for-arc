# Solve work log

## Exposure declaration before solving

I had not opened task 703a842c8e24's generator, canonical rule, notes, solutions,
private labels, or audit records. I used only `solve-blind/challenge.json`.

## Revision 1 — row-keyed cyclic shift

Hypothesis: the first value in each row is a shift key. Keep that first value
fixed and circularly rotate the remaining row cells to the right by that value,
reduced modulo the payload width.

Evidence from the visible examples:

- In the first lesson (payload width 8), key 1 moves both colored cells one
  position right; key 2 moves the adjacent pair two positions; key 3 wraps the
  value at payload position 6 to position 1; and key 4 maps payload positions
  2 and 8 to positions 6 and 4.
- In the second lesson (payload width 7), key 8 behaves like shift 1, confirming
  modulo-payload-width behavior.
- In the third lesson (payload width 6), key 6 leaves a row unchanged, while key
  8 behaves like shift 2.
- Every nonzero payload value is preserved, including duplicates; only positions
  change. Rows transform independently.

Implementation: for each row, split `head=row[0]` and `payload=row[1:]`, compute
`shift = head % len(payload)`, and return the head followed by the payload
rotated right by `shift`.

Remaining uncertainty: none apparent for rectangular nonempty ARC grids. The
implementation also handles an empty row defensively, although that case is not
suggested by the examples.
