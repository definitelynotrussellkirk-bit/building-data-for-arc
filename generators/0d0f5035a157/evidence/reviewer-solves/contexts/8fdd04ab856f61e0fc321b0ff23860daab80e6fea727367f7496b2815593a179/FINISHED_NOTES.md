# Solve notes

## Visible evidence

I used only `solve/challenge.json` during this solve phase.  In all three
training pairs, each output has the same shape as its input.  Rows do not
interact: every output row contains exactly the input row's nonzero values in
the same left-to-right order, moved into a contiguous prefix, with zeros filling
the remaining suffix.

Examples that distinguish details:

- Training 1 final row keeps `5,9,8,4,1,7`; the values are not sorted, so the
  operation is stable compaction rather than color ordering.
- Training 2 includes rows that begin nonzero but contain later gaps, so the
  rule applies to every row rather than only rows with a leading zero.
- Training 3 contains a seven-value row, so the rule is not limited to small
  row payloads.

## Hypothesis

For each row independently, remove every zero, retain the remaining values in
original order, place them from column zero, and append enough zeros to restore
the original width.

## Implementation and stopping reason

`solution.py` implements that transformation directly.  No competing
hypothesis fits the visible examples as simply, and the examples already test
order preservation, leading-zero and internal-gap placements, singleton rows,
empty rows, and a dense row.  I therefore made one ordinary solve attempt.

This is an exposed post-repair solve: I had seen the task rule earlier while
reviewing the generator, but I did not consult a reference source during this
solve phase.
