# Visible-only solve work log

This is a human-readable work log, not a token-level model trace. I had already
seen the task rule during generator repair, so this episode is **exposed**, not
blind. During this solve phase I used only the prepared visible examples and did
not reopen the generator, Racket source, private labels, or prior explanations.

## Revision 1

Hypothesis from the three demonstrations:

- Locate the two nonzero markers.
- They lie on one horizontal, vertical, or 45-degree diagonal lattice segment.
- Return a same-size all-zero grid.
- Paint color 8 on every strict interior point of the segment.
- Do not copy either endpoint, and the marker's original color is irrelevant.

The examples jointly distinguish horizontal, vertical, and diagonal cases and
show colors 3, 4, and 1 all map to cyan. The two visible queries are therefore a
main diagonal from `(0,0)` to `(8,8)` and a horizontal segment on row 2 from
columns 0 through 7. I implemented the general lattice-step rule rather than
hard-coding either query.
