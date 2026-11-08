# Working notes: 0bd65c18b34c

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/0bd65c18b34c/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->

## Current decisions

- Preserve the canonical Racket authority, canonical ledger rows, `RULE_HASH = 9cd282956b9a`, and the four-profile public axis.
- Repair `large_four_balanced` in place rather than inventing a fifth production profile. Its same-row equal-distance blue dot now behaviorally distinguishes row-major-first from the plausible topmost/rightmost rival.
- Alternate `ordinary` and `tie_break` schedule slots. The earlier period-three proposal was reversed after a held-out sole witness left two rotations ambiguous; period two keeps every three-demo support set distinguishing.
- Explicit `scene_profile` remains higher priority than the lesson schedule. The new `schedule_profile` rejects non-integer seeds, booleans, negative/non-integer indices, and unknown difficulty values.
- Keep the two-setting `tie_break` work under `workspace/parametric/` as a proposed task-local prototype. `first` is exact canonical authority; `last` changes one equal-distance comparator. It is not a production approval or training-admission claim.
- Retain `checks/main-repair/adversarial_probe.py` as a reusable bounded authority/distribution/API probe for future reviewers.

## Source-bound results

- Final generator SHA-256: `f9e74f2b1216ef76ee0ae0bf5189c6c7a8068b234334fb0df9ff559a12a738aa`.
- Authored tests: 24 passed.
- Semantic gate: 600/600 strict; 378/600 witness; all three bands; 24 enumerated fixed-seed rotations; no warnings or errors.
- Compatibility probe: 720 default draws, all four profiles, 120 distinct pairs in every sampled band/start bucket, all explicit profile/band combinations, canonical/independent parity, rejection mutations, determinism, and global-RNG isolation.
- Parametric evidence SHA-256: `3e1624722f1c4df79c1fb4e7243a7aaaede8b389d38dfc980dada4f6e25a8544`; both settings materialized with three demos and four queries.

## Supplementary tickets

- `ticket-4842252759ec5b4c`: completed one lawful `dfc4967f816f` witness; canonical Python/Racket output `[[8,8,8,0]]` refutes `top_row_only` output `[[8,8,8,8]]`.
- `ticket-fe81786dfe42fedc`: completed the pinned `defba1ab4f90` replay; source/assets/audit identities match, canonical and mirror checks are 10/10, and both public entry points still accept all 11 malformed scalar probes. This reproduces, but does not clear or broaden, the unresolved audit.

## Remaining issue and next useful action

The frozen issued task test is nonportable because it hard-codes a canonical path from `__file__.parents`. It fails before collection in the staged runtime and is intentionally unchanged. The next useful maintainer action is to update that frozen fixture to use `reviewer_support.find_root`, `canonical_path`, and `canonical_pairs`, then replay `task_tests`; no generator change is indicated by this blocker.
