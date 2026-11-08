# Solve work log

## Exposure declaration before solving

I had not opened the generator, canonical rule, reference solution, private labels,
prior notes, or any task-specific material for task `03269f74e737`. I used only
`solve-blind/challenge.json` and the generated solve templates.

## Revision 1 — partial-copy completion

The all-9 column separates a complete exemplar on the left from a wider work area
on the right. In every training pair, the output is exactly the right work area:
non-exemplar colors are preserved, while connected fragments in the exemplar's
color are completed into translated copies of the left shape.

Concrete checks from the visible examples:

- Training 1 adds the missing right arm to one plus and the missing bottom arm to
  another.
- Training 2 completes three differently truncated pluses.
- Training 3 shows the rule is not specific to pluses: the asymmetric five-cell
  exemplar is translated to complete two fragments.
- Training 4 preserves colors 7, 8, and 3 as distractors while filling only color 5.

Implementation: locate the solid separator, extract the colored prototype, split
same-colored work-area pixels into 4-connected components, enumerate translations
that contain each component, reject out-of-bounds or distractor-overwriting
placements, and fill the best valid translated prototype. The two visible test
inputs appear unambiguous under this rule. Remaining uncertainty is limited to
lessons with one-cell fragments having several equally valid translations; none
of the visible examples or queries has that ambiguity.
