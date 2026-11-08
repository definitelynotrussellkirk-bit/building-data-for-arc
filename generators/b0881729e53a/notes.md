# Working notes: b0881729e53a

## Intended rule and authority

The only authority is the existing Racket rule, pinned by `RULE_HASH = "b7117efbdd28"`; it was not edited. Find the unique hollow rectangular frame, enumerate every other same-color 4-connected component in row-major discovery order, select the last non-frame component, erase all external components, crop the selected component to its bounding box, and paste it unchanged at the floor-centered position in the frame interior.

## Repaired distribution defect

Version 3.0.0 scheduled a useful larger-earlier distractor, following the retained lead in `evidence/associated_notes.jsonl` from assignment `local-random-989c192558bf`. That refuted “choose the largest,” but every two-object generated scene still made the correct later component smaller, rightmost, and usually favored by a simple frame-distance rule. A test-first five-pair holdout probe in `checks/red-task-tests/` reproduced the defect: `smallest_external_object` fit all demonstrations while disagreeing on the query.

Version 4.0.0 replaces that confounded branch with a five-slot cycle: four two-object scan-order profiles followed by one single-object control. Two profiles place an earlier object on row 0 at the right and the selected object on row 1 at the left. Two profiles tie both objects on row 0 and use the later start column at the right. Across those profiles, size and color tie; touching/separation, side, shape, width, height, compactness, and frame-distance preferences are tied or reversed. `EXAMPLES_NEEDED = 4`, so a production lesson contains four demonstrations and one query. Every one-pair holdout retains at least two refuting demonstrations for each declared rival.

## Rival and counterexample evidence

`LESSON_COMPETITORS` contains 22 executable alternatives covering source copying, first/smallest/largest component, left/right, near/far, top/bottom, width/height, bounding-box area, straight/bent shape, low/high color, corner placement, and cyan-only behavior. The retained source-bound counterexample is `counterexamples/scan_order_shortcuts.json`; seed `20261008`, sample index `1`, medium. Its fresh Racket label is in `checks/counterexample-b0881729e53a/racket-final.json`, and it refutes the three shortcuts that fit all canonical pairs: smallest, rightmost, and farthest from the frame.

## Verification on final generator bytes

Final generator SHA-256: `15493318af330aba653bcc87efc34f5324527aea67ccd40b99bc1bc11d51e2de`.

- Required-rotation battery: `checks/after-final/result.json` — all 12 stages green; 12 sampled lessons, 60/60 query rotations, zero ambiguity.
- Random Racket census: `checks/lesson-census-final.json` — 300/300 lessons, 1,500 pairs/rotations, zero ambiguity against the declared rival registry.
- Declared-period census: `checks/schedule-census-final.json` — all five starts across three bands, 15 lessons and 75/75 rotations, zero ambiguity.
- Independent dynamic rival probe: `checks/selection-holdout-probe.json` — 15 cycles, 75 rotations, 22 competitors, zero ambiguous or weak-refutation entries.
- Focused portable tests: `checks/task-tests-with-counterexample-2/result.json` — 33/33 passed.

## Decisions, reversals, and limits

The prior “larger earlier distractor in every short window” choice was not removed as wrong; it was generalized because size alone did not define scan-order selection. Descriptive witnesses that had no rival-output disagreement were removed from the strict semantic contract after the intermediate failure in `checks/after/`; the corresponding generated cases remain in the distribution.

The exact override surface remains deliberately small and observable: `grid_h`, `grid_w`, and `placement`. The repair checks a finite declared rival family and one fixed five-slot schedule; it does not prove uniqueness against every imaginable program or every seed. The canonical authority, output centering, source erasure, and frame grammar are unchanged.
## Current reviewer considerations

Source SHA-256: `15493318af330aba653bcc87efc34f5324527aea67ccd40b99bc1bc11d51e2de`.

# Decisions for b0881729e53a

## D1 — preserve the canonical authority

**Choice.** Keep the Racket program and `RULE_HASH = "b7117efbdd28"` unchanged.

**Rationale.** The four canonical pairs, the baseline Python mirror, and 120 before-phase Racket applications agreed. The defect was not a wrong label; it was a generated curriculum that let simpler object selectors masquerade as the authority.

**Rejected alternative.** Reinterpret the task as “choose the smallest/rightmost/nearest object.” Those alternatives fit the old generated scenes but are contradicted by the authority and by the retained counterexample.

## D2 — generalize the old distractor schedule instead of deleting it

**Prior choice.** Version 3.0.0 put a larger earlier distractor into short lesson windows. This correctly refuted “choose the largest.”

**New choice.** Version 4.0.0 uses a five-slot cycle with four two-object scan-order profiles and one single-object control. The two-object profiles tie object size and color, use both left-selected and right-selected layouts, tie or reverse distance and bounding-box preferences, and reverse straight/bent shape roles.

**Reason.** The red regression in `checks/red-task-tests/` showed that the prior choice still made “choose the smallest,” “choose the rightmost,” and simple distance rules observationally equivalent to row-major-last selection.

**Failure modes checked.** First/last, size, side, distance, row/bottom edge, width, height, bounding-box area, shape, color, source copying, paste corner, and cyan-only behavior are executable rivals. The finite registry is not a proof against every possible program.

## D3 — make every legal one-pair query rotation teachable

**Choice.** Set `EXAMPLES_NEEDED = 4` and `LESSON_SCHEDULE_PERIOD = 5`: four demonstrations and one query, with any of the five positions allowed to be held out.

**Rationale.** A three-demonstration window could not robustly retain both scan-order modes and all feature reversals after an arbitrary holdout. Five profiles let every holdout keep at least two refuting demonstrations per declared rival.

**Evidence.** `checks/schedule-census-final.json` exhausts all five starts at seed 0 across easy/medium/hard: 15 lessons and 75/75 rotations, zero ambiguity. `checks/lesson-census-final.json` adds 300 random lessons and 1,500/1,500 rotations, also with zero ambiguity.

**Limitation.** The fixed-start enumeration is exhaustive only over the declared period at one seed; the random census samples rather than proves all seeds.

## D4 — prefer controlled ties and reversals over arbitrary clutter

**Choice.** Use two explicit geometric constructions:

1. An earlier object starts on row 0 at the right; the selected object starts on row 1 at the left.
2. Both equal-size/color triominoes start on row 0; the right object is later only by start column.

**Rationale.** These constructions isolate row-major order and make the counterfactual visible. Random extra objects would increase diversity without guaranteeing that a particular shortcut is refuted.

**Rejected alternatives.** More colors, more objects, or arbitrary noise were not added. They would enlarge the grammar and complicate validation without addressing the identified confounds.

## D5 — retain a small exact override surface

**Choice.** Keep only `grid_h`, `grid_w`, and `placement` as advertised exact axes.

**Rationale.** All three are directly observable and form a fully Cartesian matrix. Shape-role and layout are curriculum-controlled because exposing them independently could destroy the per-window teaching guarantees.

**Evidence.** The final override stage passed every advertised combination; exact-control tests are included in the 33 focused tests.

## D6 — remove weak witness declarations, not generated cases

**Intermediate failure.** `checks/after/` failed strict semantic validation because three descriptive witness entries had no associated rival-output disagreement. They described distribution coverage but could not function as semantic discriminators.

**Choice.** Remove those entries from `SEMANTIC_WITNESSES`; retain the underlying generated cases and ordinary focused assertions.

**Rationale.** Inventing a rival merely to satisfy the contract would overstate semantic evidence. The final strict battery in `checks/after-final/` passes with witnesses that actually distinguish outputs.

## D7 — retain a source-bound counterexample

**Choice.** Add `counterexamples/scan_order_shortcuts.json` and test it against the canonical mirror and the three shortcuts that fit all canonical pairs.

**Evidence.** `checks/counterexample-b0881729e53a/racket-final.json` is a fresh Racket execution on final generator bytes. The input passes `self_check`; canonical output differs from smallest, rightmost, and farthest selectors.

## Self-review

The repair could have introduced a new “choose bent,” width, height, or bottom-edge heuristic because the first prototype reversed only size and side. The final profiles deliberately tie or reverse those features, and the dynamic probe in `checks/selection-holdout-probe.json` reports zero weak-refutation entries across 22 actual declared rivals and all 75 cyclic holdouts.
