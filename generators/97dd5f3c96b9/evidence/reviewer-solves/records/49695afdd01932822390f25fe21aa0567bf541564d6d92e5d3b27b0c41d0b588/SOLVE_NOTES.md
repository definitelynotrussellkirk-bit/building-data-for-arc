# Solve work log

## Exposure before solving

I had not opened the task's generator, canonical rule, reference solution, private query labels, prior solution explanations, or any generator assigned for repair. I saw only the visible examples printed by `python3 review.py blind prepare` and the public solve files.

## Revision 1 — connect matching endpoints

**Observation.** Every nonzero color occurs exactly twice. In each training example, the two cells of a color lie on one shared row or one shared column. The output preserves all existing cells and fills the zero cells between those endpoints with the same color. Examples include color 3 across row 1 in train 0, color 5 down column 6 in train 0, and all three independent segments in trains 1 and 2.

**Hypothesis.** Group nonzero cells by color. For each group of exactly two cells, fill the inclusive horizontal segment when the rows match or the inclusive vertical segment when the columns match. Leave any unsupported configuration unchanged rather than inventing a diagonal rule.

**Probe.** Before implementation, a local visible-example harness failed with the template `NotImplementedError`. After implementation, I ran the same harness against every public training pair. The review checker is the authoritative visible-only check.

**Query prediction.** Query 0 should fill color 6 vertically in column 0 from rows 0–4, color 5 horizontally on row 7 from columns 5–7, and color 8 across all of row 8. Query 1 should fill color 7 vertically in column 0 from rows 3–7, color 8 vertically in column 4 from rows 5–7, and color 4 horizontally on row 8 from columns 2–7.

**Alternatives considered.** Filling bounding rectangles or extending lines to borders contradicts the training outputs; only cells between paired endpoints are added. No failed semantic revision was needed because the same rule explains every visible pair without exceptions.

**Remaining uncertainty.** The visible data does not show malformed inputs, colors with more or fewer than two endpoints, or diagonal endpoint pairs. The implementation conservatively ignores those cases.
