# Working notes: ccbf7456811b

## Current design

- The issued base generator was semantically inert: every candidate motif was isolated from the color-7 target, so all horizontal-closure overlaps were zero and the advertised target-ranking branch never ran.
- The repaired base constructs target-crossing sparse marker pairs. Ordinary draws now contain at least two positive-overlap candidates, deliberately exercise the extra-cell tie-break, vary 3–5 candidate colors, and expose only truthful `grid_h`, `grid_w`, and `n` controls.
- The native episode parameter is `closure_axis = row | column`. `row` returns the canonical Racket program byte-for-byte; `column` closes the same matched candidate markers vertically before applying the same overlap/extra/color ranking and crop.
- The causal chain is: close each candidate on the selected axis -> produce per-color closed cells and overlap/extra scores -> rank and crop the winner. A protected skip-closure counterfactual changes the final output.
- Episodes support 2–6 demonstrations and 1–4 generated queries. Qualification uses four distinct private queries; public projection reveals one query per view without future inputs or a total-count hint.

## Adversarial findings repaired

1. The first two-demo lesson let both “smallest color” and “most markers” fit every demonstration for a column episode while failing a query. Role-color schedules were crossed so color and frequency are nuisance variables.
2. The minimum lesson did not teach the final color tie-break. One row tie and one column tie were moved into the two required demonstrations; reverse-color ranking is now a retained regression rival.
3. A lesson could otherwise be read as “choose the only full-overlap candidate.” A positive-but-partial overlap competitor was added to both minimum branches so overlap ranking is taught before extra-cell and color tie-breaks.

## Retained evidence and limits

- Task-local tests cover exact canonical bytes, repaired base semantics, matched settings, independent count bounds, strict numeric/grid rejection, crossed controls, tie branches, substantive boundary-touching 30×30 input, protected Racket, and the adversarial tool.
- The reusable adversarial probe checks 128 semantic seeds, 15 plausible shortcut families, all 2/6-demo and 1/4-query count corners, 1,024 episodes, and 3,328 matched input pairs; finite attacks are not a proof of universal uniqueness.
- Authoring preflight and the causal witness passed on final source bytes. Owner native qualification/acceptance and any training admission remain separate downstream gates.
