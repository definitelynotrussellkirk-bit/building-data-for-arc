# Native overlap-guided object recovery

`overlap_policy=intersection` returns the exact canonical Racket source. `recover_top` first executes that intersection, finds its unique largest four-connected component, then recovers the entire top-panel object containing that overlap. Output retains panel dimensions and paints the recovered object cyan (8). The production generator and selected canonical authority remain unchanged.

A: exact canonical Boolean intersection followed by four-connected component extraction. Intermediate: the unique largest connected overlap and its coordinates. B: use those coordinates to select a containing original top component and render all its cells. Total overlap per parent is deliberately not equivalent: a larger parent contains eight disconnected singleton overlaps while the selected parent has six or seven connected overlaps. A wrong intermediate from eight-connectivity or aggregate overlap selects the wrong top object.

Inputs retain zero background, one full-width 5 divider, equal panels with distinct non-{0,5,8} colors and all four 00/10/01/11 states. Normal panels are 4–9 by 14–24. The maximal stress input is 29x30, with 14x30 panels; equal panels plus one divider force odd input height, so a 30th row would break the grammar. The stress scene contains five separated objects, scale-two shapes, a fragmented-overlap distractor, boundary contacts and background-only bottom distractors across the canvas.

Exact integer seeds, independently requested 2–6 demos and 1–4 queries are supported. Six demo inputs and four query inputs are setting-neutral and independent of requested counts. The complete query bank is privately shuffled before taking a prefix. `public_turn` reveals only demo pairs and the current query input. Public exports hash only those visible bytes and are physically emitted in hash order. Stored episode metadata, directory listings, settings, rules, answers and source-order indices stay controller-private.

The first self-review reproduced two executable shortcuts: ignore parents after the third, and recover only when an overlap component has six cells. Both fit the first two original demos and failed a query. The revised second demo has five parents, a fifth-parent winner and seven connected overlap cells. It rejects both without adding a third demonstration. Before and after protected-Racket labels are retained under evidence/current; the same failing query inputs are preserved. Top color 3 is present in the first demo, retaining the production palette-role repair.

Run from the packet outer directory:
```sh
python3 review.py run python3 generators/ba5056d6102e/workspace/parametric/audit.py --out generators/ba5056d6102e/workspace/parametric/evidence/current/audit --seeds 20
python3 review.py task-tests ba5056d6102e --phase after --out ../checks/ba5056d6102e-tests
python3 review.py run python3 ../checks/ba5056d6102e/replay_regressions.py
```
The audit uses the same-checkout protected evaluator also used by native qualification, records its runtime identity, and executes both setting programs and total executable rivals. It never calls Racket inside adapter.generate. Its Python sweep counts repeated prefix requests, not independent scenes. The separate literal-fixture replay checks all eight panel-wise D4 transforms under both settings. Finite checks are not universal uniqueness, all-seed correctness or training-benefit proofs. Exact-source owner acceptance and training admission remain separate.

The authoring evaluator resolves both library (`shared/runtime`) and isolated task-test (flat `arc_repl`) layouts inside the same root. The initial staged run failed the same-checkout guard; that failure is retained, and the final stage verifies the repaired resolution without weakening the guard.
