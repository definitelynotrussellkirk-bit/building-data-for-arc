# public_eval_4e34c42c — authored family v1.0.0

**Status: reviewer-ready public creation; not owner-registered, qualified, accepted, or training-admitted.** No canonical implementation existed in this packet. The new `reference.rkt` matches all four supplied labels (two demonstrations and two private gold queries) under protected Racket. Production generation never imports those fixtures.

## Current rule and parameter

Recover separate four-connected multicolor fragments against the true modal background. Treat background inside an observed fragment rectangle as a real constraint and the space outside that rectangle as unknown. Translate compatible fragments to maximize colored overlap, requiring a completely matched monochrome component from at least one fragment. Resolve score ties by union area, displacement and lexicographic offset; repeatedly merge and crop the reconstruction.

`finish_rule=assemble` returns `reference.rkt` exactly. `assemble_then_bridge` uses the reconstructed drawing as an intermediate: a color with exactly two aligned occurrences is extended across its empty row/column span. Raw scattered fragment coordinates cannot substitute for reconstructed endpoints.

Fresh scenes vary glyph count and size, links, partial/full overlaps, redundant subsets, background and signal palette, D4 orientation, placement and dimensions. Inputs are identical across settings. Separate deterministic streams support 2–6 demonstrations and 1–4 independent prefix-stable queries; query four is 30×30 with foreground touching all boundaries. The controller materializes a full private query bank, permutes it using a setting-independent presentation seed, and emits only one current query without answer, program, settings, index or total-count metadata.

## Found and repaired

A minimum lesson initially had only horizontal relay examples, so a horizontal-only rival matched both demonstrations but changed a vertical query. Demonstrations now alternate orientation parity, exposing both horizontal and vertical bridges within the first two examples. `workspace/parametric/evidence/horizontal-only-regression.json` retains the Racket-labeled pre-repair counterexample; the four-seed regression was observed failing before repair and passing afterward.

## Executed evidence

`checks/public_eval_4e34c42c/preflight/` contains original-label verification, four authoring jobs (both settings × seeds 17 and 43) and exact source binding. A fresh replay reproduced preflight, execution and original-pair bytes identically. The final assigned suite passes 45 tests (also included in the 102-test combined run).

`adversarial/audit.json`: eight episodes, 48 selected-rule label checks, 72 rival checks, 232 protected-Racket executions and 32 public single-query views. There are zero harmful survivors or evaluation errors. Some nonactivated/on-domain-equivalent mutations remain bounded-equivalent; this is not universal program uniqueness. `sweep.json`: 640 fresh scenes match independently constructed mosaics; all 200 demo/query count requests preserve prefixes.

`causal/witness.json` and `causal/replay.json`: replacing reconstructed endpoints with raw endpoint coordinates changes 22 final cells. Three malformed witness variants (source binding, program and unchanged counterfactual output) are rejected. Reviewer replay is not owner acceptance.

## Reuse and limits

From the packet's outer folder, use `python review.py run python3 generators/public_eval_4e34c42c/workspace/parametric/audit_native.py audit --out ../checks/public_eval_4e34c42c/fresh-audit`. Use the same driver with `witness --preflight ../checks/public_eval_4e34c42c/preflight/preflight.json --out ../checks/public_eval_4e34c42c/fresh-causal`. Output directories must be new. A replayable Python sweep is retained at `checks/public_eval_4e34c42c/sweep.py`.

The admitted construction is translation-only and unambiguous; arbitrary ambiguous or disconnected collages are not promised. The greedy tie policy is a deterministic authoring decision, not evidence of the intended rule on unseen ambiguous parents. Final review was author self-review, not an independent reviewer. No current assigned-check failures remain. Next useful action: owner source/provenance review, registration, native inventory/qualification and exact-source acceptance; do not activate training from preflight alone.

Catalog-wrapper limitation: the packet suggested `review.py task-tests`, but it exits 1 with `Unknown puzzle` for this unregistered ID. The direct pytest suite and creation-specific preflight are the executed valid alternatives. No catalog/shared-runtime workaround was applied; the owner can rerun that wrapper after registration.
