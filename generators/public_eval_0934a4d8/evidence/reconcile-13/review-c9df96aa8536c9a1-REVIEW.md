# Review — `review-c9df96aa8536c9a1`

Source version: frozen packet `c92b8ecc2cc925485ebd8692e72adf2681d1f9d920d94673f2e2ff050b6b8b48`.
Completion: both assigned public-evaluation families are complete as reviewer-ready **prototypes**.
Owner status: neither family is registered, natively qualified, accepted, or admitted by this return.
`public_eval_21897d95`: missing rule/build → general arrow-transfer Racket rule, ordinary generator, two-setting native adapter, tests, and evidence.
`public_eval_0934a4d8`: missing rule/build → general occluded-mosaic Racket rule, ordinary generator, two-setting native adapter, tests, and evidence.
Fresh staged task gates: `21897d95` 23/23 passed; `0934a4d8` 22/22 passed; both report zero staged source drift.
Both authoring preflights passed under protected Racket and replayed every supplied training label and author-private test label.
Bounded audits covered 12 seeds × 2 settings, four private queries, first-query presentation coverage, privacy invariance, and 16 checked one-query exports per family.
Reference-rule changes are new task-local `reference.rkt` files; no catalog, canonical authority, approval, or shared runtime was changed.
Remaining owner action: reconcile source, register provenance, run unchanged native qualification, and accept each family separately.

## `public_eval_21897d95`

### Defect → repair

The packet supplied the immutable public parent but no executable general rule or native family. The repair infers a unique disjoint exact cover of all color-1 T markers, inpaints marker hosts, recovers connected rooms, traces each T stem to its first different room, transfers either the colored center or host color, and applies the isolated L-corner quarter-turn. The exact-cover stage rejects the accidental false T in official training pair 3.

The episode parameter is `payload=center_override|host_only`. Inputs are matched across settings; two demonstrations contain colored centers that distinguish the settings; all episodes retain exactly four private queries and include a 30×30 stress query.

Source hashes:

- `generator.py`: `de8519fe80d43e4feef73f4cc2e46d738db3e4557b9c43a5211842ae54d935ba`
- `reference.rkt` / `canonical.rkt`: `2ed74fc1c9f84ba34eef1736183c8b51ae09f162807260b6f92ea1e544b1ed91`
- `adapter.py`: `01e0a6ed1d34b6420d4f9694e6f5a96c11e8be6c7144b3e650241e13c8d785ee`
- `family.py`: `901f058c80e4818ac1aee6b6559bbf7350b51c0ea70fe74639b7d4ab7b11b511`

Primary evidence: `checks/public_eval_21897d95/preflight/preflight.json`, `checks/public_eval_21897d95/causal/replay.json`, `checks/public_eval_21897d95/adversarial.json`, `checks/public_eval_21897d95/public-export-check.json`, and `checks/public_eval_21897d95-tests-final/result.json`.

## `public_eval_0934a4d8`

### Defect → repair

The packet supplied the immutable public parent but no executable general rule or native family. The repair locates the unique off-center horizontal and vertical symmetry axes from visible zero-conflict reflections, identifies the solid color-8 rectangle, maps each hidden cell to a visible mirror/transpose source, and returns only the restored rectangle.

The episode parameter is `source_priority=mirrors_first|transpose_first`. Generated mosaics share the same mirror symmetries but are intentionally not transpose-symmetric, so two demonstrations identify the setting; all episodes retain exactly four private queries and include a 30×30 stress query.

Source hashes:

- `generator.py`: `e031b3199ab7f810f7dcd4cd3ec3c70201276d0db0f82fb00d693c064d469b98`
- `reference.rkt` / `canonical.rkt`: `c47a24836f66e4ab1e41a4342c12a92486affe8ad83d5bccad621b1eb5a89664`
- `adapter.py`: `ec7dfdc8e83164db68fdecdb315b8ba1cf61d78b2018c82e7e466d47a64397b8`
- `family.py`: `2deb4cddacfe720f58409eb51fe9f632d2f8904cfe0fa0d484292ad2cc3a5a2c`

Primary evidence: `checks/public_eval_0934a4d8/preflight/preflight.json`, `checks/public_eval_0934a4d8/causal/replay.json`, `checks/public_eval_0934a4d8/adversarial.json`, `checks/public_eval_0934a4d8/public-export-check.json`, and `checks/public_eval_0934a4d8-tests-final/result.json`.

## Review assessment

A separate read-only author pass found no Critical or Important issue; its source-binding audit is `checks/final-self-review.json`. No subagent reviewer was available, so this is weaker than an independent fresh-context review. One deferred minor remains: Python performs stricter rejection on malformed, out-of-family inputs than the Racket programs; official parents and every admitted/generated episode are covered by source-bound execution.
