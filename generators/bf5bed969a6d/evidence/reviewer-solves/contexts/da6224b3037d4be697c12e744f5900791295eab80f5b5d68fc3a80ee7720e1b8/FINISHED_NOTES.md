# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Revision 1 — diagnostic red check

- Earlier task-specific Racket-rule exposure before this solve: none.
- I intentionally ran the untouched starter once as a diagnostic probe.  The
  checker reported an execution error and 0/3 visible examples, confirming the
  check would catch the missing implementation rather than silently accepting it.

## Revision 2 — centered stencil copies

- Observation: color 2 is a small connected shape.  Every other non-zero color
  outlines a rectangular frame.  The output removes color 2 and adds exactly one
  copy of that shape in each frame's own color.
- Placement probe: normalize the color-2 shape to its bounding box, then center
  it in each frame's interior using the floor offset on odd slack.  This explains
  all three visible examples, including a 3×2 stencil in a 5×3 interior and a
  3×3 stencil in a 5×4 interior.
- Implementation choice: infer each frame from the bounding box of one non-zero
  color.  Paint only background cells.  This preserves an already visible frame
  outline if two frames intersect; the first query contains such an overlap, and
  the visible examples do not reveal an overwrite order.
- Remaining uncertainty: the masked query may instead require one frame color to
  overwrite another at a stencil/outline intersection.  Preserving existing
  non-background cells is the conservative rule because the transformation only
  adds marks to empty frame interiors in every visible pair.
