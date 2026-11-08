# ARCpuzzles public-evaluation creation review

- Assignment: `review-945cfc6f8bd8569a`; both assigned public parents now have full reviewer-ready prototype families.
- `public_eval_45a5af55`: authored the missing canonical Racket rule, deterministic strip generator, matched-input `full`/`longest_run_core` adapter, tests, finite-rival audit, public projection, and causal witness.
- `public_eval_e87109e9`: authored the missing canonical Racket bounce rule, deterministic thick-cursor generator, matched-input `header`/`opposite` adapter, tests, finite-rival audit, public projection, and causal witness.
- Protected-Racket authoring preflight passes every supplied labelled train/test pair and all declared generated settings for both tasks.
- Staged task tests pass: 29/29 for `45a5af55`; 32/32 for `e87109e9`.
- Each bounded adversarial pass covers 192 episodes and 1,472 labelled pairs with no harmful surviving declared rival.
- Each public-export probe covers 16 sequential one-query views, 16 privacy-invariance checks, and 16 positive controls; independent saved-file checks pass.
- Root `reference.rkt` and task-local `canonical.rkt` are byte-identical in each family.
- Status: reviewer-ready prototypes only. Owner registration, source review, unchanged-source native qualification, fresh acceptance, and any training admission remain pending.
- Final whole-delta review was an author self-review because no independent reviewer/subagent tool was available; no Critical, Important, or Minor issue was found.

## `public_eval_45a5af55`

The canonical rule removes the duplicated terminal cap from a uniform-row strip and folds the effective color sequence into concentric square frames. The parameter branch locates the earliest longest constant-color run, retains that input-dependent suffix, and folds only the selected inner core. Generated episodes use 2–6 demonstrations and four distinct private queries, preserve identical inputs across settings, and make both settings identifiable from the first two demonstrations.

Primary evidence:

- `checks/public_eval_45a5af55/preflight-ready/preflight.json`
- `checks/public_eval_45a5af55/preflight-ready/execution.json`
- `checks/public_eval_45a5af55/preflight-ready/original-pairs.json`
- `checks/public_eval_45a5af55/task-tests-ready/result.json`
- `checks/public_eval_45a5af55/causal-ready/witness.json`
- `checks/public_eval_45a5af55/causal-ready/replay.json`
- `checks/public_eval_45a5af55/adversarial-ready.json`
- `checks/public_eval_45a5af55/public-probe-ready/report.json`

## `public_eval_e87109e9`

The canonical rule decodes four header markers, moves the square color-8 brush toward each axis-aligned target, turns according to the marker side, and redirects a turned run along each encountered original rectangle's uniquely farther protruding side. Missing or diagonal targets use the observed straight-up fallback; all routes use the unchanged original field, so trails may cross. The parameter branch reverses the header's left/right interpretation while preserving matched inputs.

Primary evidence:

- `checks/public_eval_e87109e9/preflight-ready/preflight.json`
- `checks/public_eval_e87109e9/preflight-ready/execution.json`
- `checks/public_eval_e87109e9/preflight-ready/original-pairs.json`
- `checks/public_eval_e87109e9/task-tests-ready/result.json`
- `checks/public_eval_e87109e9/causal-ready/witness.json`
- `checks/public_eval_e87109e9/causal-ready/replay.json`
- `checks/public_eval_e87109e9/adversarial-ready.json`
- `checks/public_eval_e87109e9/public-probe-ready/report.json`

## Shared tooling

`checks/tools/public_creation_probe.py` is a reusable source-bound public-view probe for future public-evaluation families. It verifies the retained preflight binding, projects one query at a time in independently shuffled order, checks private metadata and future-query invariance, exercises positive controls, and writes deterministic public-only files. Its focused tests pass in `checks/tools/public-creation-probe-tests-ready-command.json`.

## Limits and next action

The finite-rival audits establish only the declared rivals and retained seeds, not universal semantic uniqueness. The public preflights are deliberately not owner qualification. The owner should reconcile any concurrent source for these parent IDs, register exact source/provenance under `ee_45a5af55` and `ee_e87109e9`, accept the source review, refresh the native inventory, and run unchanged native qualification plus fresh acceptance separately for both tasks.
