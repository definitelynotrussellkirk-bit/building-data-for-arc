# Working notes: 5ffd8d801705

## 2026-10-24 review repair

**Root cause.** Version 2.0.1 drew every 2x2 anchor from `(row, col) = (3i, 3j)`. The retained global coordinate rule, “keep a nonzero cell iff `row % 3 == col % 3`,” therefore matched every generated output while disagreeing with canonical examples. The old validator only searched for one valid window, so partial blocks and 3x3 solids were also accepted.

**Repair.** Version 2.1.0 searches arbitrary non-overlapping anchors and realizes the requested object count exactly. Every default draw contains an edge block, at least one off-lattice anchor, multiple modulo-3 anchor classes, and both checkerboard anchor parities. Colors are distinct. Impossible joint packing requests raise `ValueError` with `incompatible_axes`; unknown or mistyped controls fail closed.

**Semantic guard.** `RULE_HASH` is pinned to `c845504525a2`. `rule_mirror` implements the full selected program, including preservation of non-square nonzero cells. `LESSON_COMPETITORS` names `global_mod3` and `global_checkerboard`; `CANONICAL_SHORTCUTS` is empty because these rivals are lesson-only rather than canonical-fitting shortcuts.

**Evidence.** The source-bound suite has 21 passing tests, including all canonical pairs, shortcut witnesses, exact counts, strict validation, and eight real-Racket comparisons. Lint and the semantic audit pass. The full override matrix completes 29,700 draws with 29,101 accepted draws, 599 structured incompatibility rejections, and zero findings. Final receipts are under `WORK/checks/5ffd8d801705-{task-tests-final,lint-final,audit-final,override-after-v2}/`; TDD failures are retained in `WORK/checks/5ffd8d801705-red/pytest.log`, `WORK/checks/5ffd8d801705-canonical-shortcuts-red.log`, and `WORK/checks/5ffd8d801705-incompatible-axes-red.log`.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-82548b4b24894693:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `f1b847300b32af1743fa7bf12b369a6fc65f30e1f516d954f914b32f03274499`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Accepted2.1.0removes modulo3placement alias and tightens block ownership/validation. Reviewer reports21focused tests and source-bound Racket/semantic/override checks; no owner generator battery rerun.

### Assessment or prior finding

## 5ffd8d801705

**A1 — Reproduced generation-only positional shortcut; not a default label mismatch.**

Generator SHA256: `f1b847300b32af1743fa7bf12b369a6fc65f30e1f516d954f914b32f03274499`.
Rule SHA256: `c845504525a26b80edf3dab2cbb386786fbe51b712feadc5bbb0f4e9ee95e7e0`.
Evidence: `checks/audits/5ffd8d801705.json`.

Generated 2x2 blocks are anchored on multiples of three. A wrong program can keep foreground exactly when its global row and column residues modulo 3 agree, instead of finding each object's intended diagonal. This rival matches actual Racket on 120/120 sampled draws: bands None/easy/medium/hard, seeds 0..9, indices 0..2. There are 86 unique inputs; repeated draws are not independent evidence. No Racket execution failures were recorded in that census.

The same rival matches 0/4 canonical pairs. The saved witness is canonical train[0], a lawful canonical input accepted by the target validator; its real output differs from the rival. It is not in the sampler's restrictive lattice support. Thus a model trained mainly on generated inputs could learn the wrong coordinate rule. No claim is made that such a model was actually trained or observed failing.

**Suggested repair, not applied:** vary valid block anchors across residue classes and include canonical-like layouts that refute the absolute-position program. Add that rival to a semantic contract and check whole lessons. Target unchanged.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-82548b4b24894693-v0001/audit_assets.json), manifest SHA-256 `ee994fca1eac2e23441714e65daf8633726c128e60b4fa561d155d3cfd7ceb53`.
<!-- arcpuzzles-current-audit-assessment:end -->
