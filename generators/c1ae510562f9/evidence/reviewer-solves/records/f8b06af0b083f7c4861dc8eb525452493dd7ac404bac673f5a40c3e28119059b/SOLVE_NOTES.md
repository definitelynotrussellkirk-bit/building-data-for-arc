# Post-repair visible-only solve — c1ae510562f9

This is a concise model-authored work log, not a token-level conversation trace.
Earlier rule exposure: YES. I repaired this generator and read the reference
before this phase. This episode is therefore exposed, not a blind solve.
After preparation I kept generator source, Racket source, prior explanations,
canonical data and private query labels closed. The attempt uses only the new
visible challenge and its own Python. The episode is bound to final source
222f258f552a3286f47aff98fc8a89c3439e1e50243553e57fc9968507d41f1c.

## Revision 1

Visible inputs have shapes 9×9, 13×6, 14×13 and 14×12; each visible output
is 3×3. Their gray cells outline open-top containers. The outputs contain
respectively 4, 8, 9 and 6 cyan cells. Their visible order follows the top row
left-to-right, then the right edge downward, then the bottom row right-to-left.
The eight-cell output leaves the center zero, identifying the spiral route.

The candidate rule counts wholly zero rows strictly inside the side walls and
above the gray floor. It excludes exterior padding and rows containing even
one cyan cell. A local visible-only probe measured counts 4, 8, 9 and 6 and
verified that the complete predicted grids match all four outputs. The probe
also measured the leading-empty run, which is zero on partially filled examples
1 and 3, despite their outputs containing eight and six cells. This refutes
counting only top headroom. Results are saved in visible_probe.json.

Implemented a fresh Python solve(grid), computing gray bounds, applying the
whole-row predicate and walking a clockwise spiral procedurally. This is the
first actual solve attempt; no false failed revision or teaching negative was
created. Query correctness remains withheld for independent maintainer scoring.
