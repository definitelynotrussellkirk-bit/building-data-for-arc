# Current notes: a76216bfa3e8

## Production decision

Baseline version `2.0.0` scheduled marker morphology by `sample_index % 8` and source parity by `sample_index % 4`, so every default morphology identified one parity. A lawful override changed source parity without changing morphology, exposing a shortcut that the old lesson hook did not model.

Version `2.1.0` retains the eight-slot geometry/tail schedule and exact canonical rule. Marker roles now follow `0,1,1,2,2,3,3,0`, with the four-role block rotated by seed. Every four-consecutive-example window contains one repeated morphology at positions that differ in both row and column parity; all eight morphologies remain reachable across seed rotations. `lesson_identifiable` enforces the same counterfactual directly.

Current source SHA256: `87faf298e9b917bdf7e2d16c8930688002f6e35df4cc9c1fc0223e639acee0fb`. Canonical rule hash remains `33baf0d7ad4c`; exact canonical Racket text SHA256 remains `53055d806a70a3b56a8e8d901ab08d7e4b1187010957e213305af65ecd1ddc84`.

## Verification and limits

Fresh staged tests pass 12/12. Protected Racket matched the Python mirror on 29/29 cases, including four canonical pairs and one retained lawful override. The old morphology→parity rival now agrees on only 6/24 default cases; direct checks cover 24/24 lesson windows and all eight seed-rotated morphologies.

Two optional exhaustive census attempts reached the fixed 880-second stage timeout and remain incomplete; do not treat them as passing. The final attempt had no ambiguity or scoring errors in completed rows but did emit rotation-hook warnings before interruption.

## Parametric proposal

`workspace/parametric/` contains a separate, unapproved `edge_policy` prototype: canonical `clip` versus `full_only`. The retained build uses four demonstrations and four distinct queries per fixed-setting episode, exact Racket labels, visible-only public IDs, and adversarial type/export/boundary checks. Packaging this proposal does not approve the variant or admit it to training.

Next useful action: replay the focused receipts during integration; separately decide whether to qualify the `edge_policy` proposal. Do not gate the production repair on the unfinished optional census unless the census becomes resumable.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-02526caab8ea05c1:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `0d4fe803e3bc4897819aabd6f32acea8b56fe1aa8ff3215b11782ce9f8f2bed6`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Explicit owner disposition after accepted reviewer repair review-a4a864f97066006e: current repo/generators/a76216bfa3e8/generator.py SHA256 87faf298e9b917bdf7e2d16c8930688002f6e35df4cc9c1fc0223e639acee0fb. Reviewer-reported evidence: 12focused tests and29protected Racket cases. Repeated morphology now occurs at opposite row/column parities in every four-demo window. Morphology-only parity lookup no longer fits every default; optional interrupted censuses remain unpassed. No owner battery rerun, universal identifiability or training admission. The audit on 0d4fe803e3bc4897819aabd6f32acea8b56fe1aa8ff3215b11782ce9f8f2bed6 is resolved only for these repaired findings. Retained target-local evidence references: `checks/audit/8604dc774d22/probe.py` `checks/audit/8604dc774d22/verify_audits.py` `checks/audit/a76216bfa3e8/finding.json` `checks/audit/a76216bfa3e8/inputs.json` `checks/audit/a76216bfa3e8/probe.json` `checks/audit/a76216bfa3e8/probe.py` `checks/audit/a76216bfa3e8/racket.json` `checks/audit/a76216bfa3e8/summary.json` `checks/audit/a76216bfa3e8/verification_commands.json`

### Assessment or prior finding

## a76216bfa3e8

**Confirmed default morphology/parity correlation and a lawful recombination
missed by the declared-rival hook.** No illegal input or wrong reference label
was found in the scoped checks. The counterexample query uses an explicit lawful
override; the default query schedule does not emit it.

Identity: generator version `2.0.0`, SHA256
`0d4fe803e3bc4897819aabd6f32acea8b56fe1aa8ff3215b11782ce9f8f2bed6`;
executed canonical Racket rule hash `33baf0d7ad4c`; exact executed rule-text SHA256
`3da11d25f4f684e3e8311470ead5d55677dac2cdb5bfe817f4bf2dde55cb5a76`.

The source schedules marker pattern by `sample_index % 8` and source parity by
`sample_index % 4`. Consequently, each default morphology has a fixed source
parity. A rival can choose destination parity from morphology alone, ignoring
the marker's actual source-cell parity.

Scope: fresh seed 31, default indices `0..7` in all three bands, four distinct
canonical pairs, and one override query. Public `apply --check-generator-domain`
accepted **29/29** inputs and returned valid outputs. The mirror agreed with
Racket on **29/29**, and all four canonical labels matched Racket. The morphology
rival agreed with actual Racket on **24/24 default cases** but **0/4 canonical
cases**. It is therefore not a canonical-fitting shortcut.

Exact counterexample: use four ordinary medium demonstrations from
`generate(seed=31, sample_index=i, difficulty="medium")`, indices `0..3`, and
the query
`generate(seed=31, sample_index=0, difficulty="medium", marker_col_parity=1)`.
The query has a diamond marker at source parity **01**, while the default
morphology lookup predicts **00**. The override is correctly observed and both
local and public domain checks pass. The rival matches all four Racket-labeled
demonstrations, but differs from the Racket query output in **68 cells**.
`lesson_identifiable(demos, query)` nevertheless returns `[]` when supplied with
the actual public Racket labels. The hook's rival inventory omits this correlation
rival.

This confirms the existing unresolved audit at the same source hash. It is a
distribution and lesson-coverage weakness, not a claim of default query
mislabeling. Suggested disposition: decouple morphology and parity across default
lessons and witness the same morphology under differing source parities. No
repair was made here; the audit does not claim exhaustive coverage.

Evidence: `checks/audit/a76216bfa3e8/{probe.py,probe.json,inputs.json,racket.json,
finding.json,summary.json,verification_commands.json}`. The fresh probe is an
explicit adaptation of the retained unresolved probe. `finding.json` contains
the exact four demonstrations, query, actual Racket output, rival prediction,
68 differing cells, source identities, and generation arguments.

Payload commands, each exit 0:

```sh
../.review/venv/bin/python -B ../checks/audit/a76216bfa3e8/probe.py
../.review/venv/bin/python -m arcpuzzles apply a76216bfa3e8 --input ../checks/audit/a76216bfa3e8/inputs.json --check-generator-domain --timeout 120 --out ../checks/audit/a76216bfa3e8/racket.json
../.review/venv/bin/python -B ../checks/audit/8604dc774d22/verify_audits.py
```

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-02526caab8ea05c1-v0001/audit_assets.json), manifest SHA-256 `9cf5a7e2458b35a44b491a4c179c246e0f0b68cd63a3cd0db119c75c07853fe0`.
<!-- arcpuzzles-current-audit-assessment:end -->
