# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Revision 1 — diagonal one-gap completion

Observed that every added cell is the midpoint of two equal nonzero cells whose
row and column coordinates differ by exactly two.  The rule is local: only a
blank diagonal midpoint is filled.  Evidence against broader alternatives:
training example 2 leaves the color-2 endpoints four diagonal steps apart
unconnected, leaves vertically aligned color-1 endpoints unchanged, and leaves
the eligible color-7 midpoint unchanged because that midpoint is occupied by 3.

Implemented a copy-preserving scan grouped by color.  It proposes a color only
for equal-color endpoint pairs at offsets `(±2, ±2)` with a zero midpoint.  If
more than one color proposes the same unseen midpoint, the implementation leaves
it unchanged rather than imposing an arbitrary ordering; no visible example has
such a conflict.

Predicted query changes before checking:
- test 1: add 2 at `(6,2)` and 1 at `(6,5)` in zero-based coordinates; do not
  overwrite the 6 between the two 9s.
- test 2: add 9 at `(2,3)` and 7 at `(3,6)`.
