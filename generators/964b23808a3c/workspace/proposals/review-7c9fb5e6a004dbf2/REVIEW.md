# Maintainer brief — `964b23808a3c` v3.0.2
Defect → repair: strict-scalar entry points accepted bool/float/string seeds and indices, and `sample_index=-1` silently selected the final profile; `generate` and `schedule_profile` now reject these aliases before profile or RNG logic.
Final generator SHA-256: `c586f09adde529195a8467eb499005004a68546e46a4b10b3e80617f02d431e5` (baseline `c8437cf46718d553fcf6f856c3b0abf428a09e7debf9f370a224f6135d5f52c7`).
Before → after battery: 11/12 green with 33 blocking strict-scalar warnings → 12/12 green, including defect lint 0 findings.
Task-local portable tests: 111/111 passed, 0 failed/errors/skipped, exit 0.
Lesson policy: 3 demonstrations + 1 query from each consecutive four-profile window; production census 1,200/1,200 pairs with 0 ambiguity/errors.
Query policy: arbitrary hold-one-out rotation is required; 1,200/1,200 rotations had 0 ambiguity/errors, and the required-rotation semantic gate passed.
Parametric extension: **proposed prototype**, four selector × segment-owner settings, each with exact Racket execution and a 3-demo/1-query distinguishing episode; it is not production-approved.
Remaining blocker: none for the canonical repair; wider seed/rival coverage and a production API decision remain before any parametric promotion.
Reference Racket authority: unchanged; rule hash remains `c7e69da25375`, and the default prototype program is byte-for-byte identical to the selected authority.
Acceptance: routine

## Scope and source binding

Assignment `review-7c9fb5e6a004dbf2` selected the approved original ARC family `training:17b80ad2`. I used the current source and its review index as the authority; prior return `review-feb73249509b92e2:v0001` was only a lead. The repair is confined to the selected task: `generator.py`, task-local tests, notes, and `workspace/parametric/`. No shared runtime, canonical row, base rule, or audit target source was edited.

The final generator version is `3.0.2`. The version bump intentionally gives lawful generated examples a new deterministic RNG namespace; the four-profile schedule, declared axes, task law, and selected Racket rule are unchanged.

## Finding table

| ID | Task / path | Finding and evidence | Patch status | Final result |
| --- | --- | --- | --- | --- |
| G1 | `964b23808a3c/generator.py` | Coercible seed/index values and negative indices were accepted. Before evidence: `checks/before/checks/964b23808a3c_before_defect_lint.log`. | Fixed with strict entry validation and 11 focused regression cases. | After battery 12/12 green; defect lint 0 findings; portable tests 111/111. |
| P1 | `964b23808a3c/workspace/parametric/` | Original family lacked runnable nearby rule variants. Evidence: `checks/parametric/selector-segment-seed17/receipt.json`. | Added isolated proposed prototype and focused tests; canonical dispatch untouched. | Four settings, four exact program hashes, all three alternatives refuted by each episode's demos and distinguished on its query. |
| A1 | audit target `ce40117f40f9` | Reproduced permissive validator/ignored override defects and a 300/300 southeast positional shortcut. Evidence: `checks/audit/current/ce40117f40f9/probe.json`. | Audit only; target unchanged. | Reproduced on assigned source hash. |
| A2 | audit target `f2e717c7c250` | `n_keys=1` and `n_keys=3` both yielded two keys in all 30 explicit calls; contract hooks are missing. Evidence: `checks/audit/current/f2e717c7c250/probe.json`. | Audit only; target unchanged. | Reproduced on assigned source hash. |
| S1 | `solve-blind/`, `solve/` | Required visible-only solve records. | No generator patch derived from masked labels. | Blind draw: revision 2 passed 5/5 visible examples. Final-source exposed solve: revision 2 passed 3/3 visible examples. Masked labels remain unknown. |

## G1 — canonical repair

### Root cause

`generate` passed its arguments directly into `gen_ctx`, while `schedule_profile` and `_profile_spec` coerced `sample_index` with `int(...)`. Python therefore treated booleans as integers, accepted integral and nonintegral floats/strings, and used negative indexing before modulo normalization. The before battery measured 33 strict-scalar warnings across three difficulty probes; `sample_index=-1` selected the dense profile rather than failing.

### Repair

`_validate_entrypoint(seed, sample_index)` now requires exact built-in integers (`type(value) is int`) and a nonnegative sample index. Both public entry paths validate before profile selection or RNG setup, and the coercions were removed. Eleven parameterized cases cover five invalid seed forms and six invalid index forms through both `generate` and `schedule_profile`.

The change does not narrow lawful ARC inputs or alter the Racket transformation. It only makes the public generator contract fail closed for values that the shared defect lint already classifies as invalid. The final-source validator, profile floor, overrides, semantic contract, grammar, Racket lint, and authority synchronization all remained green.

## Verification

- **Before battery:** `checks/before/result.json`, exit 1. Eleven stages were green; defect lint reported 33 strict-scalar warnings.
- **After battery:** `checks/after/result.json`, exit 0. All 12 stages were green on final generator SHA `c586f09a…d431e5`.
- **Portable task tests:** `checks/task-tests/result.json`, exit 0, 111 tests passed with no failures, errors, or skips. This is the authoritative completed task-test receipt.
- **Required rotations:** `checks/required-rotations/result.json`, exit 0; the strict semantic gate passed with `--require-rotations-identifiable`.
- **Large lesson census:** `checks/lesson-census-final.summary.json` binds the final generator and canonical rule. Across 100 lessons per band, it materialized 300 lessons, 1,200 pairs, 1,200 hold-one-out rotations, and 1,062 exact unique inputs, with zero ambiguity, hook warnings, materialization errors, or scoring errors.
- **Fresh patch replay:** the candidate return source patch SHA `1938ce646a1b0dbb0d8004550d65dff0426adc4890a9241220f459451855211a` passed `git apply --check` and `git apply` in a fresh 345-file declared-runtime closure; all ten changed paths and the final generator hash matched. Fresh portable tests there passed 111/111, exit 0. Evidence: `checks/handoff/candidate/summary.json` and `checks/handoff/candidate/replay.json`.
- **Superseded diagnostic:** a redundant portable retry was terminated by the outer execution transport after its pytest progress reached the end; its `CheckInterrupted` receipt is retained under `checks/task-tests-final/` and is not counted as a pass. A direct bounded pytest run printed `111 passed in 29.38s`; the completed portable receipt above remains the source of the reported exit code.

Finite declared-rival testing is not a proof against arbitrary hypotheses. The census covers the production sampler, three bands, and each hold-one-out position for the materialized four-pair bundle; it does not enumerate every seed or every possible program.

## P1 — proposed parametric rule family

The prototype preserves the original reasoning pipeline—scan each column's ordered nonzero markers, decide whether color 5 activates the column, and paint marker-delimited intervals—but exposes two bounded semantic parameters chosen once per episode:

- `selector_mode`: canonical `ends_in_5` versus `contains_5`;
- `segment_mode`: canonical `current` versus `previous` marker ownership.

The four exact Racket program hashes are:

| Setting | SHA-256 |
| --- | --- |
| `ends_in_5 / current` (canonical default) | `2c8f8aa67ae8104f49348542b8fc365527f316c292c87dd8a6c08a0dfd9cc1a0` |
| `ends_in_5 / previous` | `4aab9ea987a1db8272d1cafaa6dbef8c2b43c6d9e0f729ba40eb167e2fd1ed20` |
| `contains_5 / current` | `4789e772d70350cb9037520d81cee6e25f93fa7ff5600cdce9d6e057264593a5` |
| `contains_5 / previous` | `2f08eda6b3d853de1c3940856fbd73ff477d156f81654b9dea0c37328252a8ac` |

Seed 17 evidence materializes one complete 3-demo/1-query episode for every setting. For all four episodes, every alternative setting disagrees with at least one demonstration and also predicts a different query output; the exact Racket outputs match the Python mirror. Public files contain only labeled demonstrations and unlabeled query inputs. Parameters, program text, rival outputs, and query labels stay in private retained evidence.

This is **proposed prototype evidence**, not approval. It covers four bounded settings at one evidence seed. Promotion would need broader seed coverage, a shared per-episode rule interface, and an explicit decision on whether such hidden semantics belong in exported training data.

## Solve records

The independent blind draw `084de7b050a1` was completed before opening the assigned generator: a deliberate skeleton diagnostic failed, then the substantive reflection solver passed all 5 visible examples on revision 2. The record declares no earlier exposure and no reference consultation.

The assigned task's post-repair episode is bound to the final generator SHA. A deliberate skeleton diagnostic failed, then revision 2 passed all 3 visible examples. Earlier rule exposure is declared `yes`; reference consultation during the solve is `false`. These are human work logs and executable revisions, not token-level model traces, and no masked-query correctness is claimed.

## Self-review and remaining limits

The strict-scalar repair introduces no semantic shortcut: it runs before generation and cannot alter any lawful grid's transformation. The version bump does remap valid random draws, so the final batteries, lesson census, and solve were all regenerated against the final bytes rather than inheriting baseline evidence.

The canonical generator is ready for routine intake. Parametric variants remain isolated and unapproved; audit targets remain unchanged and require separate owners.
