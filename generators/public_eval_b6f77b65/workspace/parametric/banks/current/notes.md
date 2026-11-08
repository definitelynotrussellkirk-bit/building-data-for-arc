# public_eval_b6f77b65 — authored family v1.0.0

**Status: reviewer-ready public creation; not owner-registered, qualified, accepted, or training-admitted.** No source existed in this packet. The new `reference.rkt` matches all eight supplied original labels (five demonstrations and three private gold queries) under protected Racket. Public examples and gold labels are test fixtures only, never runtime generation inputs.

## Current rule and parameter

Row zero gives every color to remove; row one is a blank separator. Recover horizontal beam interiors before vertical posts so that a same-colored arriving post does not steal a beam joint. A post ending at a beam or the floor has one occluded terminal cell. Preserve that geometric endpoint, clip it at the floor, and paint beams over joints. Remove the cue-colored pieces, then settle survivors bottom-up: posts land on lower beams/posts; beams use bilateral side support or stop at a direct obstruction.

`support_rule=both_posts` is the exact authored canonical source. `either_post` changes only the lateral support criterion: a single adjacent post can hold a beam. Both settings require input-dependent settled lower geometry before higher beams can be placed. Reusing pre-removal support coordinates is not equivalent.

The endpoint convention is a **source inference**, not a known physical law. It explains the extra visible red cell in original train[1] uniformly and also passes color-permutation, padding and a separate literal endpoint-reveal test. No per-example corrections or answer tables are used. An owner should review this interpretation and the maximal-row-run beam parser before widening the grammar beyond the finite labels and admitted nested/crossing support graphs.

## Construction and repaired teaching defect

Fresh nested and crossing support graphs vary dimensions, member lengths/positions, nonzero palette, reflection and cue order. Background stays zero and gravity stays downward. Query four is a genuine 30×30 multilevel cascade with content on every boundary. Inputs are matched between settings; 2–6 demos and 1–4 independently indexed queries have stable prefixes. Safe public projection reveals one shuffled current query and no private bank/answer/program/setting/count fields.

Initially, the either-post setting's first two demos let a raw-support-coordinate rival survive, although its 30×30 query prediction was wrong. The first nested demonstration now removes its base beam, forcing lower supports to move under either rule; the second crossing graph teaches setting differences, multiple cues and endpoint occlusion. Four failing either-post regression cases were observed before this repair. The old source and a protected-Racket counterexample are retained in `workspace/parametric/evidence/raw-support-teaching-regression.json`.

## Executed evidence

The assigned task suite passes 57 tests (included in the fresh 102-test combined run). `checks/public_eval_b6f77b65/preflight/` holds all original labels and four source-bound authoring jobs: both settings × seeds 17 and 43, two demos and four queries. Fresh preflight, execution and original-pair files reproduced byte-for-byte.

`adversarial-final/audit.json`: eight episodes, 48 selected-rule label checks, 64 rival checks, 136 protected-Racket executions and 32 single-query public views. All eight declared rivals are rejected by demonstrations, with no errors or harmful survivors. The earlier `adversarial/` finding is historical and repaired, not a current passing receipt.

`sweep.json`: 640 generated scenes; 1,280 Python setting checks; 128 minimum lessons; 200 independent count requests; 160 additional protected-Racket/Python comparisons. All unremoved source graphs are stable, cue colors disappear only from the body, the cue/separator are preserved and bounds remain valid. The wrong raw-support intermediate changes 832 of the swept setting outputs. Sweep seeds are finite and explicitly recorded.

`causal/witness.json` and independent `causal/replay.json`: raw support tops replace the settled-post intermediate in a validated 30×30 canonical case, changing 51 final cells. Tampered source binding, wrong program and unchanged counterfactual output are rejected by static witness checks. This is reviewer replay, not owner acceptance.

## Reuse and next action

Use `audit_native.py audit --out NEW_DIRECTORY` or `audit_native.py witness --preflight PATH_TO_PREFLIGHT_JSON --out NEW_DIRECTORY` through `review.py run python3 generators/public_eval_b6f77b65/workspace/parametric/audit_native.py ...`. A replayable independent stability/count/Racket sweep is at `checks/public_eval_b6f77b65/sweep.py`.

Final review was author self-review; no independent reviewer was used. No current assigned-check failures remain. Arbitrary beam tilting, thick beams, cyclic support graphs and a universal grammar are outside this build. The next action is owner source/provenance and endpoint-rule review, then registration, native qualification and fresh exact-source acceptance. No shared runtime, catalog, canonical authority or training switch was modified.

Catalog-wrapper limitation: the packet suggested `review.py task-tests`, but it exits 1 with `Unknown puzzle` for this unregistered ID. The direct pytest suite and creation-specific preflight are the executed valid alternatives. No catalog/shared-runtime workaround was applied; the owner can rerun that wrapper after registration.
