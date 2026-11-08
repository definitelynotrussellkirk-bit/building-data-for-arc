# Solve notes — d62a0e470ae8

Earlier exposure: yes. I reviewed this task's generator and authority before this
required post-repair episode, but during the solve I used only the visible
challenge examples and my own Python implementation.

## Visible-example observations

- The nonzero corner cell is not copied into the output. It behaves as an
  operation key.
- Several disconnected same-color components may appear. The output always uses
  the largest four-connected component, tightly cropped; smaller components are
  distractors.
- Key 1 turns the crop 90 degrees clockwise (train 3).
- Key 2 reflects the crop left-to-right (train 4).
- Key 3 reflects the crop top-to-bottom (train 1).
- Key 4 turns the crop 180 degrees (train 2).

Hypothesis: erase `(0,0)`, enumerate same-color four-connected components, take
the unique largest, crop its bounding box from the cleaned grid, and apply the
keyed transform above. The examples distinguish all four keys and include
smaller distractor components, so this is more specific than “take the first
object” or “transform all foreground cells.”

I stopped after the first implementation passed all four visible examples. No
Racket source, generator source, reference solution, or masked label was opened
during this solve phase.
