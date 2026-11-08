# Post-repair visible-only solve log

This is a human work log, not a token-level model trace. I had already worked on
this task's generator before this episode, so the final exposure declaration is
**yes**. During this solve phase I read only `solve/challenge.json` and did not
consult the generator, Racket source, private labels, reference solutions, or the
earlier blind-solve explanation.

## Visible-example analysis

Hypothesis: split the yellow (`4`) cells into 4-connected components. Count the
distinct outer grid borders touched by each component. Recolor the whole
component cyan (`8`) iff it touches **exactly two** borders; leave every other
component unchanged.

Visible checks:

- Train 0: the long vertical component touches top and bottom and changes; the
  top-right component touches top and right and changes. Interior components do
  not change.
- Train 1: the top-right corner component changes, while the full bottom-row
  component touches left, bottom, and right (three borders) and stays yellow.
  This rejects an “at least two borders” rule.
- Train 2: the full middle-row component touches left and right and changes even
  though it is not a corner object. This rejects a “corner objects only” rule.
- Train 3: the full left-edge component touches top, bottom, and left and stays
  yellow; the lower-right component touches bottom and right and changes.

Predicted tests:

- Test 0: recolor the two bottom-corner components; retain the top-only strip and
  interior block.
- Test 1: recolor the top-right component and the full-width middle component;
  retain the top-only component and both interior components.

No revision was needed after these mutually discriminating examples.
