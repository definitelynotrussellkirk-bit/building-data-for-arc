# Solve work log

Earlier exposure: none. Before this solve I did not inspect the task's generator,
canonical rule, private labels, prior solutions, notes, or audit evidence. I used
only the visible examples in `challenge.json` / `README.md`.

## Revision 1 — repeated-shape hypothesis

Across every visible pair, the gray cells form several disconnected objects. Three
objects have exactly the same translated shape and are recolored blue; the lone
one-off distractor remains gray. The repeated shape varies by lesson (2×2, 2×3,
3×2), so fixed dimensions are not the rule.

I considered "recolor every filled rectangle," but rejected it because the
unchanged 1×2 distractors are themselves filled rectangles. I also considered
"recolor the largest objects," which fits these examples but throws away the
stronger repetition signal.

Implementation: find same-color 4-connected components, normalize every component
by translating its top-left cell to `(0, 0)`, choose the `(color, shape)` group
with greatest frequency (larger area breaks a frequency tie), and recolor all
members of that group to blue (`1`). Four-connectivity is deliberate: the two
diagonal stray cells in train example 2 remain separate singleton distractors,
while the three 3×2 blocks still form the unique most frequent/larger repeated
shape.

Probe: a visible-example unit test was written first and failed on the original
`NotImplementedError`; after implementing the repeated-shape rule it passes all
three training pairs. Remaining uncertainty: an unseen lesson with two equally
frequent same-area shapes would be underdetermined by these examples, but the
visible lessons consistently contain one repeated target family and one defect.
