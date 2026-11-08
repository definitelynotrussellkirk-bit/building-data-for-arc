# Exposed, visible-only solve work log

This is an assistant-authored work log, not a token-level model trace. Earlier
exposure: yes. I reviewed and repaired this generator and read its reference rule
before preparing this episode. During the solve phase I opened only the public
challenge and solve instructions; no generator, rule, reference implementation,
private labels or prior solution notes were consulted.

## Revision 1

The five displayed demonstrations retain hollow objects, discard solid objects,
and draw one 4x4 outline per retained object. Different-sized frames in examples
1 and 3 become equal-sized tokens; repeated frame colors retain multiplicity.
The visible placements support choosing the output axis from the ranges of frame
top-left coordinates, sorting along that axis, with equality giving a row.

Wrote a standalone connected-component solution using only Python's standard
language features. It contains no imports from the generator or reference tools.
Checking the first genuine attempted solution; no deliberate failures or teaching
negatives were manufactured. Query correctness will remain unknown locally.
