# Solve notes

This is a human-authored work log based only on the visible examples printed by
`solve_episode.py prepare`. I had earlier exposure to the task rule while repairing
the generator, so this is not a blind inference record; I did not consult a
reference implementation or private answers during this solve episode.

## Hypothesis

The two full-height color-5 columns divide each input into three panels. Within
each panel, isolate the largest 4-connected nonzero object, ignoring any smaller
same-colored distractor component. Normalize each largest object under all eight
rotations/reflections (D4). Exactly two panels contain the same canonical shape;
render that shared canonical shape in color 8 with zeros in its bounding box.

## Implementation decisions

- Split only on full-height color-5 columns, rather than assuming fixed widths.
- Find 4-connected components by color and select the unique largest component.
- Enumerate all four rotations, with and without reflection, and choose the
  lexicographically smallest normalized coordinate tuple as the canonical form.
- Count the three canonical signatures and render the one occurring twice.

The visible examples include detached singleton distractors, so selecting all
same-colored cells would be incorrect; selecting the largest connected component
matches every shown example.
