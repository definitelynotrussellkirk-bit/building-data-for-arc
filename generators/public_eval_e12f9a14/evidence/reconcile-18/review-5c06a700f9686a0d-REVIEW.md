# review-5c06a700f9686a0d — partial build; one explicit blocker

- **public_eval_d59b0160: reviewer-ready.** New Python/Racket canonical panel-erasure rule and native `erase` / `largest_survivor` family. All 4 supplied labels reproduced; authoring preflight passed; owner registration/acceptance pending.
- **public_eval_e12f9a14: BLOCKED.** New uniform beam-collision candidate reproduces 5/6 supplied labels in Python and protected Racket. Train[2] omits 6 predicted southeast yellow cells. No exception, answer lookup, or gold edit was added.
- Sources: `generators/<task>/generator.py`, `reference.rkt`, and `workspace/parametric/` in the source patch; original `public-parent.json` bytes unchanged.
- Complete assigned-task run: **41 passed, 1 explicitly expected failure** (the unresolved beam original). The separate copied task runners reported 21 passed and 20 passed + 1 skipped/xfail respectively.
- Bounded audits: 128 episodes / 1,280 generated pairs / 512 public turns per task. Protected Racket: 120 panel-audit evaluations; 110 beam-audit evaluations, including the retained original failure.
- Relocated checkout: **24 generated Racket labels**, 12 per task; all checked task/runtime imports came from the copied tree. The beam parent remains blocked after relocation.
- Tool tests: **6 passed** for source-drift, missing-file, symlink, duplicate-binding, unsafe-path rejection and a valid binding.
- Panel causal witness: official preflight-bound helper replay passed; ranking source panels before erasure changes **128** cells on the 30×30 case. Beam candidate causal replay changes **122** cells but is expressly not an official qualified witness.
- **Needs attention:** the beam original discrepancy prevents round completion. No owner acceptance or training admission occurred. Final review was an author self-review, not an independent agent review.

## Completed panel family: public_eval_d59b0160

The green L contains the legend. Every connected black-backed panel containing
all legend colors is erased to the orange background. Extra colors are allowed;
positions and multiplicities do not matter. Orange is structural, not necessarily
the modal color: the original third training and test scenes have more black
than orange. The first implementation's modal-background mistake failed the
original-label regression and was corrected before qualification.

The alternative first performs exactly that erasure, then ranks surviving panels
by occupied area and fills the largest survivor's zero cells green. Ties use
reading order. The sampler makes the source-largest panel an erased superset,
so a source-ranking shortcut cannot implement the alternate rule.

The family retains the exact default Racket bytes, independent 2–6 demonstration
and 1–4 query counts, four private shuffled queries before prefix selection,
matched inputs across settings, and a substantive 30×30 case. Two demonstrations
refute the tested set/existence/inversion/first-match shortcuts and the tested
source-rank/smallest/reading-order/all-survivors/no-finish variants.

Primary evidence:
- `checks/public_eval_d59b0160/preflight/{preflight,execution,original-pairs}.json`
- `checks/public_eval_d59b0160/causal/{witness,replay}.json`
- `checks/public_eval_d59b0160/audit/audit.json`
- `checks/public_eval_d59b0160-tests/result.json`
- `checks/public_eval_d59b0160/relocated.json`

## Blocked beam family: public_eval_e12f9a14

The implemented hypothesis emits colored beams through openings around 2×2
cores. Intersecting forward beams form parallel lanes moving in the sum of
their normalized directions. Rational slopes produce exact repeated-step
staircases; further collisions operate on the existing bundle. This reproduces
three of four training examples and BOTH provided test golds exactly.

The remaining mismatch is only train[2], zero-based coordinates
`(13,14), (14,15), (15,16), (16,17), (17,18), (18,19)`: model color 4 versus
provided color 8. The local 4×4 yellow emitter there is exactly the
counterclockwise rotation of train[1]'s emitter. The corresponding diagonal ray
is present in train[1]; the hypothesized southeast ray is unobstructed and has no
forward intersection in train[2]. This is strong diagnostic evidence against a
uniform local-emission interpretation, **not proof that the supplied label is
wrong**. A missing global rule could explain it.

The native candidate also supports `mark_merged`: build the piecewise trajectory
segments first, then mark gray only segments belonging to bundles with at least
two emitter colors. It has deterministic counts/prefixes, a private query bank,
30×30 stress, Python/Racket parity for generated scenes and executable rivals.
It is useful implementation work, but **not a faithful fully verified parent
reference** until the original disagreement is resolved.

The ordinary authoring preflight was run unchanged and failed with
`Official train[2] does not match reference`. No successful preflight receipt
exists for this task. Its expected-failure test is kept visible. The separate
candidate audit exits successfully when the diagnosis is reproduced, but its
JSON status is `BLOCKED_original_label_mismatch`, not `passed`.

Primary evidence:
- `checks/public_eval_e12f9a14/final-audit/audit.json` (all originals, precise failure, rotation diagnostic, source hashes)
- `checks/public_eval_e12f9a14/preflight.log` (unmodified gate rejection)
- `checks/public_eval_e12f9a14/final-audit/candidate-causal.json` (unapproved hypothesis only)
- `checks/public_eval_e12f9a14-tests/task-tests.log` (explicit xfail)
- `checks/public_eval_e12f9a14/relocated.json`

Next action is to examine that exact discrepancy and either identify the missing
general mechanism or obtain an explicit owner ruling about the authoritative
label. Do not silently correct the gold or add a one-example rule exception.

## Reusable tools and limits

Each native folder carries `audit.py` and `public_io.py`. The auditors replay
actual protected Racket, compare it with Python, test named demonstration-only
rivals, and bind exact source hashes. The exporter validates all views before
publication, detects duplicates, writes content-hash-named files in sorted order,
strips private fields and verifies saved bytes, mapping and symlink restrictions.
Only one public file is a model turn; the directory and manifest are private.

`checks/verify_relocated.py` verifies exact-source receipts and replays generated
labels from a specified copied tree. It rejects altered, missing, symlinked,
duplicate and escaping source paths. Its six regression tests are included.
This does not authenticate a maliciously rewritten receipt or grant approval.

The exploratory `ray_spike.py` is retained as exploratory evidence, not production
source; use the task-local `audit.py` for current reproducible results. Earlier
preflight/audit runs are provenance; use the explicitly named final evidence
above for current source. All supplied golds were inspected during development:
these are reproduction checks, not unseen-test performance. Audits are finite,
and the generated grammars narrower than all conceivable parent variations.
