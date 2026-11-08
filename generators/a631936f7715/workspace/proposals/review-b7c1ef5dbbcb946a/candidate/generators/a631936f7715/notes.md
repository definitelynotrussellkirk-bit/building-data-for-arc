# Working notes: a631936f7715

## Current selected generator

- Version: `1.8.0`
- Generator SHA-256: `965a662deb1bad237758745f2b18ad53eda6f8d0bf3c8d3d4febaa74b1e18d30`
- Declared `RULE_HASH`: `8097fabedcc2` (unchanged)
- Intended rule: on orange (`7`), find maximal 4-connected magenta (`6`) components. Recolor a labeled component with its one orthogonally adjacent label color, erase labels and solo markers to `7`, and leave unlabeled components as `6`.

## Repairs in review-6210ca385d85e852

1. Added strict request validation before permissive generation helpers: exact integer seed/index, nonnegative index, known difficulty, known override axes, no explicit `None`, exact integer ranges, and valid enum values.
2. Declared the existing lawful degenerates `no_components`, `no_labels`, and `full_grid` through `LAWFUL_DEGENERATE_TEXTURES`.
3. Declared an executable 8-connectivity rival and diagonal-contact witness, plus `lesson_identifiable`.
4. Added `EXAMPLES_NEEDED=3` and a four-phase schedule. Residues 0 and 2 are 4-vs-8 witnesses, ensuring every one-pair query rotation leaves a witness in the three demonstrations.
5. Labeled every witness component after the first single-label version triggered a <5% transformation-drift warning on a 14×14 canvas.
6. Retained the minimal source-bound witness in `counterexamples/connectivity-teaching-witness/` and covered it with focused tests.

## Verification

- Task tests: 46/46 pass (`checks/task-tests-final/`).
- Strict battery: 11/12 green (`checks/after-final-census/`); only inherited exact-text authority drift remains.
- Profile floor: exact 10/60, envelope 21/60, per-band exact 2/2/6.
- Override gate: 60,750 draws, zero findings, unknown key rejected.
- Fixed schedule: 12 lessons / 48 rotations, no ambiguity (`checks/lesson-census-period-s0.json`).
- Wide sampler: 300 lessons / 1,200 rotations, 1,200 unique inputs, no ambiguity (`checks/lesson-census-random-100.json`).

## Parametric prototype

`workspace/parametric/` proposes episode-level `component_connectivity ∈ {4,8}`, default 4, while label lookup remains orthogonal. It passed 16 exact Racket executions over two complete 3-train/1-test episodes; every pair distinguished the settings. This is proposed only, not selected execution or approval.

## Known limits / open finding

- The lesson schedule is visibly period 4 and intentionally witness-heavy; finite censuses passed, but they do not prove universal identifiability against undeclared rivals or all seeds.
- Active canonical and selected authority text differs only in formatting under current diagnostics. Execution parity passes, but exact-text `authority_sync` remains red. The assignment forbids editing shared files; use `checks/authority-sync-proposal.json` as a maintainer-owned follow-up and preserve archival `raw_code`.


## Current external prototype reconciliation

The task-local prototype is now version `1.1.0`. Public files use opaque `challenge-<sha256>.json` names from the shared `public_challenge_bytes` / `public_challenge_id` contract, so the digest covers exactly the visible demonstration and query-input bytes written; setting-linked programs and complete episodes are separated under a private artifact tree. The verifier exposes independent `--n-train` / `--n-test` controls and retained evidence exercises 3 demonstrations plus 4 distinct queries for each setting. Demonstrations alone leave exactly one declared candidate, then all 14 pair labels are checked against both exact Racket programs (28 executions).

The sampler now enumerates a bounded support without replacement: 210 ordered color triples × 8 dihedral transforms = 1,680 unique inputs. Larger requests fail instead of cloning pairs. Focused tests cover private-metadata/query-answer invariance of the public name, visible-content sensitivity, independent counts, full-support uniqueness, and public/private writer separation. The selected canonical generator, rule hash, approval, and prior retained evidence remain unchanged; the variant is still proposed and unapproved. Fresh evidence: `WORK/checks/parametric-reconcile-final/`.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-1760770181476aa0:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `e2bc3fc23cc2ce1a45bf454bbbf2a94ada75a591ff868b2aac23a19e40680f41`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Current generator SHA256 965a662deb1bad237758745f2b18ad53eda6f8d0bf3c8d3d4febaa74b1e18d30 explicitly validates palette_kind/texture membership before RNG. generators/a631936f7715/tests/test_generator_contract.py::test_declared_overrides_reject_invalid_types_and_values includes both exact typo reproductions. Reviewer-reported final46tasktests pass in working and fresh replay; final60750override draws reportzero findings andunknown-keyrejection. This resolves only the old invalid categorical override aliasing finding on e2bc3fc23cc2ce1a45bf454bbbf2a94ada75a591ff868b2aac23a19e40680f41. No owner test rerun; authority formatting blocker and other audit findings are unaffected.

### Assessment or prior finding

## a631936f7715

**Disposition: reproduced existing unresolved override-contract defect.** Generator SHA-256 `e2bc3fc23cc2ce1a45bf454bbbf2a94ada75a591ff868b2aac23a19e40680f41` was left unchanged. The task's existing review index already contains source-bound reports of this issue; this audit independently reconfirmed it on the current bytes rather than claiming a new defect.

Both declared categorical controls silently accept an out-of-domain value. Across seeds **0..4**, sample index **0**, bands **easy/medium/hard**, and the two invalid calls `palette_kind="typo"` / `texture="typo"`, all **30/30** calls succeeded, all **30/30** returned `self_check == []`, and all **30/30** grids were byte-identical to the same-axis `"broad"` control. `_build_palette` uses a catch-all `else` for the broad palette, while `generate` passes the override string directly instead of validating it against the declared domains.

The representative `palette_kind="typo"` input is lawful as a grid, and the supported Racket application returned a valid output bound to rule hash `8097fabedcc2`; the defect is that the requested control is invalid but accepted and silently reinterpreted. The combined audit preset also reports no task-local tests and no executable semantic contract, but those are separate from this direct reproducer.

Evidence:

- `checks/audit/a631936f7715/probe.py` and `probe.json` — portable 30-case reproducer, exact controls, AXES declarations, source hash, and counts.
- `checks/audit/a631936f7715/input.json` and `racket.json` — representative invalid override input plus authoritative output and rule/generator hashes.
- `checks/audit/a631936f7715/execution.json` — exact commands, exits, and artifact hashes.
- `checks/audit/a631936f7715-combined/` — findings-only audit preset and missing-contract evidence.

Suggested repair: reject unknown keys and validate `palette_kind`/helpful `texture` membership before `_build_palette`; retain explicit conflict checks for mixed palette directives. Add direct-call tests proving invalid enum values fail closed instead of aliasing `broad`.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-1760770181476aa0-v0001/audit_assets.json), manifest SHA-256 `372239b51e2b3766689f0906fad4c4fba140f4bedc5c9af8b2c08786c4e8cc82`.
<!-- arcpuzzles-current-audit-assessment:end -->

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/a631936f7715/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->
