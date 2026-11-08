# Solve work log

## Prior exposure

Before this blind solve I had not opened this task's generator, Racket rule,
notes, reference solution, private query outputs, or prior audit evidence. I had
only read the packet-wide directions and the visible examples printed by
`python3 review.py blind prepare`.

## Revision 1 — unobstructed vertical joining

**Observation.** Repeated nonzero colors occur in one column. In examples 0, 1,
and 3, every zero between the two equal-colored markers becomes that color. A
singleton remains unchanged. Example 2 supplies the important negative case:
color 8 has equal endpoints in column 6, but a different-colored 5 lies between
them, and no 8 cells are added.

**Hypothesis.** For each color within each column, fill the vertical interval
between consecutive matching markers only when the whole interval contains
zeros or that same color. Any different nonzero cell blocks that connection;
markers and all unrelated cells are preserved.

**Implementation.** Group nonzero coordinates by `(color, column)`, sort rows,
and paint each unobstructed interval between consecutive occurrences. This also
handles more than two same-color markers without assuming a fixed count.

**Visible probes.** A local training-example harness first failed on the supplied
`NotImplementedError`, then passed all four visible examples after this revision.
The blocked 8/5/8 interval in training example 2 is retained unchanged.

**Remaining uncertainty.** The examples only show vertical pairing, so I did not
add a horizontal analogue. They also do not distinguish “connect consecutive
markers” from a rule defined only for exactly two markers; the consecutive form
is the smallest safe generalization that preserves all visible behavior.
