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

- Task tests: 50/50 pass (`checks/task-tests-final/`).
- Strict battery: 11/12 green (`checks/after-final-census/`); only inherited exact-text authority drift remains.
- Profile floor: exact 10/60, envelope 21/60, per-band exact 2/2/6.
- Override gate: 60,750 draws, zero findings, unknown key rejected.
- Fixed schedule: 12 lessons / 48 rotations, no ambiguity (`checks/lesson-census-period-s0.json`).
- Wide sampler: 300 lessons / 1,200 rotations, 1,200 unique inputs, no ambiguity (`checks/lesson-census-random-100.json`).

## Parametric prototype

`workspace/parametric/` proposes episode-level `component_connectivity ∈ {4,8}`, default 4, while label lookup remains orthogonal. Current evidence covers two complete 3-demonstration/4-query episodes, 28 exact Racket executions, and eight queries identifiable from demonstrations against the declared rival. This remains proposed only, not selected execution or approval.

## Known limits / open finding

- The lesson schedule is visibly period 4 and intentionally witness-heavy; finite censuses passed, but they do not prove universal identifiability against undeclared rivals or all seeds.
- Active canonical and selected authority text differs only in formatting under current diagnostics. Execution parity passes, but exact-text `authority_sync` remains red. The assignment forbids editing shared files; use `checks/authority-sync-proposal.json` as a maintainer-owned follow-up and preserve archival `raw_code`.


## Current prototype reconciliation

The selected `review-4f9d5c2115d03373` exporter and CLI remain in place. The
useful finite sampler from `review-b7c1ef5dbbcb946a` is merged into prototype
`1.2.0`: 210 ordered color triples × eight dihedral transforms give exactly
1,680 distinct inputs, with larger total demonstration/query counts rejected.
The incoming exporter is unselected because the existing writer already keeps
its manifest private, refuses existing destinations, and validates every row
and duplicate visible payload before creating output.

The previous random sampler produced only 1,064 / 1,043 / 1,062 unique inputs
from 1,680 draws at seeds 0 / 20261023 / -98765. Focused regressions reproduced
that defect before the sampler change. Current focused tests pass 14/14,
including all 1,680 inputs at those three seeds, grammar and Python rival checks,
combined-count overflow, asymmetric 2/5 and 5/2 counts, exact visible-byte IDs,
private-field invariance, and the existing Racket/export checks. A separate
current-source verification labels two 3-demonstration/4-query episodes through
both exact Racket programs: 28 executions, 14 distinguishing pairs, and eight
queries identified from demonstrations against the declared rival.

Current receipts and exact source hashes are linked by
`workspace/parametric/evidence/manifest.json`. The prior manifest and exact
prototype/verification/docs/tests bytes are retained separately in
`workspace/parametric/evidence/source-snapshots/selected-4f9d5c2115d03373/`.
Inherited results remain reviewer-reported evidence for those old bytes only.
The incoming return is corroborating/proposed material; the merge is owner
reconciliation, not exact native integration of the full incoming patch.

Limits: the prototype remains proposed and unapproved, without production API
or training admission. The finite support is one 7×7 template, not the entire
lawful task domain; seeds only rotate its ordering and repeat modulo 1,680.
Changed sampling gives new seed-specific artifacts. Racket parity covers the
retained 14 pairs, while the full-support checks use the Python mirror. No
production battery or authority-formatting follow-up was rerun, and existing
canonical generator/rule bytes remain unchanged.

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
