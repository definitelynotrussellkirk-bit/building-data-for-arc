# Solve work log

## Exposure disclosure

Before this fresh solve episode I had already inspected this task's generator while repairing its curriculum and had seen that a canonical reference exists. I did **not** consult the Racket rule, reference solution, private query labels, or earlier solution notes during this solve. The implementation and checks below were derived from the visible examples in `solve/challenge.json` only.

## Revision 1 — diagnostic stub

Hypothesis/probe: preserve the prepared `NotImplementedError` stub for one check so the solve harness proves that it is executing this file and does not accidentally accept an unimplemented program. The visible-only check returned an execution error and 0/4 visible examples, as expected. This was a diagnostic probe, not a proposed solution.

## Revision 2 — nested-component containment depth

Visible observation: every nonzero object is a hollow rectangular frame. The outputs keep every occupied cell in place while changing the outermost frame from color 1 to 2, the next contained frame to 3, and successively deeper frames to 4, 5, and 6. The examples with canvas margins and off-center/inset frames show that color is attached to frame nesting, not distance from the canvas edge or a recentered reconstruction.

Implementation: find four-connected nonzero components; compute each component's bounding rectangle; define its depth as the number of other component boxes that strictly contain it; recolor all cells of that component with `2 + depth`; leave zero cells unchanged. This formulation handles translated, non-square, and unevenly spaced frames without assuming a fixed gap.

Alternatives considered: sorting only by frame area would fit the examples but encodes ordering rather than the visible containment relation; coloring by canvas distance would fail inset/offset examples; redrawing centered frames would move cells and contradict the preserved output geometry. Remaining uncertainty is limited to unseen malformed inputs where nested frames touch and merge into one four-connected component; no visible example suggests such inputs.
