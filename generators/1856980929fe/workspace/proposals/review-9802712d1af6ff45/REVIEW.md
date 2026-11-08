# Review result — 1856980929fe

Task source remains version `3.0.0`; source SHA-256 is `280eb13ac248a89c3542aeef297db1de4fa59e245c19004f68f1da18dcd87822`.
Defect: a lawful five-demo lesson failed to reject “expand only the first two seed rectangles.”
Repair: added the exact `first_two_seeds` rival and `third_seed` witness; the retained counterexample is now named by `lesson_identifiable`.
Canonical `generate`, `VERSION`, Racket source, and `RULE_HASH=77504f6c55fa` are unchanged.
Focused selected-task suite: **55/55 passed**.
Curriculum probe: 300 lessons / 1,800 valid unique inputs; 7 raw shortcut windows, 7 guarded, **0 unguarded**.
Proposed `branch_mode={both,left,right}` prototype: 3 episodes × (5 demos + 4 queries), fixed setting per episode.
Exact evidence: 27/27 Racket↔Python labels, 4/4 canonical-default pairs, 12/12 identifiable queries, 31/31 retained Racket replay.
Adversarial pass: 19/19 sampler/type/coverage/ID/symlink/path/tamper/source/stale-file/privacy checks passed.
Remaining limits: finite source-bound sampling; prototype is not production-approved, calibrated, or training-admitted.
Routine result; no remaining source-bound failure found in the changed scope.

## Canonical semantic repair

The retained seed-2/easy window at sample indices `11..16` has demonstration seed
counts `[1,1,2,2,2]` and a three-seed query. Before the patch the wrong rule fit
all demonstrations and changed the query while the gate returned no finding. The
repair declares that rule and maps it to a witness that detects whether the third
seed contributes to the canonical fan.

The updated reusable probe distinguishes raw rival survival from semantic-gate
failure. Seven sampled windows still have insufficient raw demonstrations, which
is expected input to `lesson_identifiable`; every one is now explicitly rejected.
Evidence: `checks/canonical/1856980929fe-first-two-repair-probe-v2.json`.

## Proposed parametric extension

`workspace/parametric/prototype.py` materializes byte-exact canonical `both` plus
`left` and `right` branch variants, executes all retained labels through bundled
Racket, enforces unique pairwise-distinguishing inputs, exposes separate demo and
query counts, and writes visible-only content-addressed challenges. The companion
verifier checks generator/prototype/program source bindings, safe integer Racket
literals, IDs, sorted uniqueness, symlink/path containment, exact private/public
file sets, public/private separation, and optional full Racket replay.

Runnable instructions and exact four-query command:
`repo/generators/1856980929fe/workspace/parametric/README.md`.
Retained private manifest:
`checks/parametric/1856980929fe-branch-mode-v2/private/manifest.json`.
Post-write replay:
`checks/parametric/1856980929fe-branch-mode-v2/private/racket-reverify.json`.
Bounded attack report:
`checks/parametric/1856980929fe-branch-mode-adversarial-v2.json`.

## Supplementary tickets

`ticket-b2a0ea7c455eea68` (`api_boundary`) completed: `omitted_count=0` generated a
valid grid and round-tripped through `observe_overrides`; `omitted_count=True`
raised the advertised `TypeError`. Evidence:
`checks/tickets/ticket-b2a0ea7c455eea68/api_boundary.json`.

`ticket-28f0a43a22ec8259` (`nvarc_visual`) completed with verdict `ok`: the locked
blind prediction matched pair 4 exactly, and the same 4-connected-component rule
matched pairs 5–29, for all 30 supplied pairs consistent. Prediction/reveal proofs
remain under `checks/tickets/ticket-28f0a43a22ec8259/nvarc/`.
