# Working notes: 329d82eaaa63

## Review `review-c5fe8719feedc568`

Baseline generator SHA-256: `08a95b43061306bff47ec65be11bc869ef30959f3ab359ebadc6c161729d65f5`.
Final generator SHA-256: `607bc195e64e6e24e646bb602def28614aa6db5e0d60cb40c861302aa9f3bc8a`.
Canonical rule hash: `c3b26f3f0fc8`.

The baseline implemented the broad visual idea but contradicted its own public contract. It lacked `RULE_HASH`, rejected a canonical one-seed input, exposed redundant or unobservable axes and ordinary negative textures, silently accepted unknown overrides, narrowed declared boundaries by difficulty, permitted repeated colours and overlapping branch geometry, and had no executable teaching contract. The selected task-local Racket source also differed textually from canonical even though execution parity held.

Version 3.0.0 keeps the canonical transformation unchanged and replaces the generator path with:

- complete grammar validation for dimensions, row placement, palette uniqueness, interior seeds, and spacing;
- three exact observable axes: `grid_h`, `grid_w`, and `n_seeds`;
- structured `incompatible_axes` errors for impossible width/count combinations;
- a deterministic four-profile schedule covering single/multi-seed and six-row/taller cases;
- a Python rule mirror used only for tests and diagnostics;
- executable semantic witnesses and seven lesson competitors, including the canonical-fitting `six_rows_only` shortcut;
- a portable reviewer probe under `workspace/probe_generator.py`.

The selected base `target_code` now exactly matches canonical text. The previous execution-equivalent source remains in `raw_code` as archival evidence; the canonical row itself was not edited.

Evidence summary: before battery 5 green, 1 advisory, 6 failed; after battery 12/12 green. Final task-local suite 54/54 passed. The production census materialized 300 lessons / 1,200 labelled pairs and checked all 1,200 query rotations with zero declared-rival ambiguity or scoring/materialization errors. A separate probe checked 320 rotations, 32 override cases, all 3 canonical pairs, and 80 diversity draws without error (78 unique inputs and outputs).

Limitations: this remains a finite declared-rival analysis, not a proof against every possible interpolating rule. The optional whole-repository pytest run timed out after 300 seconds at roughly 20% progress without displaying a failure. Masked solve-query correctness remains withheld for maintainer scoring.
## Current reviewer considerations

Source SHA-256: `607bc195e64e6e24e646bb602def28614aa6db5e0d60cb40c861302aa9f3bc8a`.

# Decisions for `329d82eaaa63`

## D1 — Preserve the canonical transformation

**Baseline choice and rationale:** The canonical Racket program alternates straight even rows and two-branch odd rows from top-row seeds. Its original authoring rationale is not recorded in the packet.

**Decision:** Keep the canonical row and runtime behavior unchanged. Use Python only as a test/diagnostic mirror.

**Alternatives considered:** Rewrite the Racket rule into a shorter program; change the task to sequential path growth; introduce collision resolution. These would add authority risk or change the task rather than repair its data.

**Probe and failure mode:** Racket rule-smoke already passed before repair. All three canonical pairs match the final mirror, and authority-sync passes. A semantic Racket edit could silently change labels, so none was made.

## D2 — Define one complete lawful input grammar

**Baseline choice and rationale:** The v2 source advertised heights roughly 5–14, widths 7–18, 2–5 seeds, distinct spacing, and many palette/texture controls, but the reason for those ranges and aliases is unknown. Its checker did not enforce the full summary.

**Decision:** Lawful inputs are 3–18 × 4–24, row-0-only, 1–8 seeds, distinct nonzero colours, interior columns, gap at least three.

**Why:** These are the widest simple bounds already advertised by the axis metadata while preserving the canonical branch geometry. Width 4 is the minimum with an interior seed; eight is the maximum number of distinct nonzero ARC colours available after excluding background while keeping a simple exact contract.

**Alternatives considered:** Keep the old narrow difficulty ranges; allow duplicate colours; permit edge clipping or branch overlap. Those choices either contradict exact override metadata or make independent seeds visually merge.

**Probe and limits:** `self_check`, exhaustive `_valid_column_sets` tests, canonical acceptance, and the full override matrix cover the grammar. The domain intentionally excludes collisions and edge truncation.

## D3 — Retire misleading axes

**Baseline choice and rationale:** `palette_kind`, `palette_size`, `position_bias`, `density`, `n_distinct_colors`, and `texture` existed, including degenerate textures. Their original rationale is unknown; several were aliases, singletons, ignored, or outside ordinary lawful data.

**Decision:** Expose only `grid_h`, `grid_w`, and `n_seeds` as exact axes. Palette sampling and column choice remain internal keyed randomness.

**Alternatives considered:** Make every old axis genuinely observable; keep diagnostic/negative textures. That adds complexity without teaching a new part of the rule, and ordinary negative samples would fail the selected input contract.

**Probe and failure mode:** The final override audit is green, unknown keys fail, and an independent probe checks 32 boundary/joint cases. Removing old names is deliberately loud rather than silently accepting stale callers.

## D4 — Make width/count dependency explicit

**Decision:** If only width is explicit, choose a feasible default count; if only count is explicit, expand the default width enough to realize it. If both are explicit and impossible, reject with a structured `incompatible_axes` tag.

**Why:** Exact requests must remain exact. Silently clipping a requested seed count or width would turn an override typo into apparently valid data.

**Alternatives considered:** Declare every impossible pair in a static table; resample forever; silently reduce the count. The numeric feasibility relation is simpler and more complete than a static enumeration.

**Probe and limits:** Boundary tests cover `(4,1)` and `(24,8)` plus impossible pairs. The relation is specific to gap-three interior placement.

## D5 — Use a four-profile teaching schedule

**Baseline choice and rationale:** Difficulty bands independently sampled dimensions and usually 2–5 seeds. There was no stated lesson-level rationale.

**Decision:** Cycle through canonical single, canonical multi, broad single, broad multi. A lesson uses three demonstrations and one query.

**Why:** The official pairs are all six rows high, so `six_rows_only` fits 3/3 canonical examples. Crossing height and multiplicity guarantees that the lesson teaches continuation and all-seed behavior rather than relying on chance.

**Alternatives considered:** Pure random sampling; six or more profiles; always use canonical dimensions. Pure randomness leaves shortcut survival; more slots are unnecessary for the identified rivals; canonical-only data cannot refute fixed-height behavior.

**Probe and limits:** The large census covers 300 production lessons, all 1,200 query rotations, and all start residues used by the sampler. It does not enumerate every imaginable schedule or rival.

## D6 — Declare executable rivals and witnesses

**Decision:** Declare identity, straight columns, left-only branch, right-only branch, skip-single, first-seed-only, and six-rows-only programs. Bind witnesses for single seed, multiple seeds, taller height, and visible odd-row branching.

**Why:** A textual claim that a lesson is “varied” is weaker than testing whether a concrete wrong program fits every demonstration and changes the query.

**Alternatives considered:** Only compare with identity; enumerate arbitrary synthesized programs. The first is too weak; the second is not affordable or complete. The chosen set targets plausible errors exposed by canonical and baseline structure.

**Probe and limits:** `six_rows_only` is explicitly verified to fit all 3 canonical pairs. All declared rivals are refuted in every sampled final lesson/rotation. Undeclared hypotheses remain possible.

## D7 — Synchronize selected authority text, preserve archival source

**Baseline choice and rationale:** The base solution carried execution-equivalent selected and archival Racket source, but their role distinction was unclear and active exact-text sync failed.

**Decision:** Set selected `target_code` to exact canonical text, keep old source unchanged in `raw_code`, and label both roles.

**Alternatives considered:** Change canonical to match the archival text; delete the archival source. Changing canonical needlessly increases authority scope; deleting it loses provenance.

**Probe and failure mode:** Before authority-sync failed; after authority-sync and rule-smoke pass. The canonical file hash is unchanged.

## D8 — Build tests and a reviewer probe before relying on the repair

**Decision:** Add source-bound tests first, observe 45 failures on the baseline, then implement. Add a separate CLI probe and test its absence as RED before creating it.

**Why:** This proves the regressions distinguish the old and new contracts and leaves future agents an executable audit rather than only prose.

**Alternatives considered:** Depend solely on the shared battery. The battery is broad but task-local tests can express exact semantic invariants and preserve root-cause reproductions.

**Probe and limits:** Final isolated task suite is 54/54. The repository-wide suite timed out after 300 seconds, so only scoped tests and the battery are claimed green.

## D9 — Curriculum composition annotation

**Decision:** Do not mark any optional ARC-DESIGN composition axis as present.

**Why:** Row parity affects where paint appears, but there is no task-defined cue, interacting subrule, or intermediate state that clearly meets the optional composition definitions. Omitting the annotation preserves `unknown` instead of inflating coverage.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/329d82eaaa63/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-565c1a422d0e35f2:v0001`. Disposition: **no_issue**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `607bc195e64e6e24e646bb602def28614aa6db5e0d60cb40c861302aa9f3bc8a`. At disposition, audited bytes match the current source.

### Current decision

The retained exact-source audit explicitly reported no issue after54tests and bounded exact-axis checks. No universal coverage or owner rerun is inferred.

### Assessment or prior finding

## 329d82eaaa63

**No issue found** after checking the current source SHA-256
`607bc195e64e6e24e646bb602def28614aa6db5e0d60cb40c861302aa9f3bc8a`.

The portable task suite passes 54/54. An additional read-only probe enumerated
all 2,688 `(grid_h, grid_w, n_seeds)` combinations: 1,456 feasible combinations
materialized exactly and passed validation; all 1,232 impossible combinations
raised the documented structured `grid_w`/`n_seeds` incompatibility, with no
unexpected acceptance or rejection. It also checked 320 held-out query rotations
(20 seeds × 4 bands × 4 query positions) against the declared competitors and
found no ambiguity.

Evidence:
- `checks/audit/329d82eaaa63/probe.json`
- `checks/audit/329d82eaaa63/task-tests/`

**Limit:** this is finite testing against the declared grammar and rivals, not a
proof against undeclared hypotheses. Audit-only target left unchanged.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-565c1a422d0e35f2-v0001/audit_assets.json), manifest SHA-256 `ed2d9805a460e9a2bc95107877b4fd3e22fea2d7c509b0d3bf1fbda57dd618b4`.
<!-- arcpuzzles-current-audit-assessment:end -->

## Parametric prototype review-1235967f8e2a064a (2026-10-24)

Decision: leave the approved production generator and canonical rule authority unchanged. Add an opt-in task-local family whose episode-fixed `branches` setting is `both` (the byte-identical canonical default), `left`, or `right`; every setting receives the same sampled top-row seed inputs and differs only in the odd-row branch policy.

The adapter exposes independent 2–6 demonstration and 1–4 query counts. Retained episodes use four distinct queries, including a 30×30 query with eight separated seeds. `episode_io.py` is a reusable strict sequential exporter: one opaque hash-named public file per query, no settings/seed/program/answer/index/total-count hint, atomic publication, duplicate-visible refusal, and saved-bundle verification.

Evidence: `workspace/parametric/evidence/current/report.json` records 18 protected-worker jobs and 270 protected-Racket evaluations; `WORK/checks/329d82eaaa63-qualification-final/qualification.json` records native finite-setting qualification; `WORK/checks/final/independent-check.json` adds seeds 0–31, count-boundary, prefix-stability, shared-input, pairwise-distinction, and retained-bundle checks. The source binding remains generator SHA-256 `607bc195e64e6e24e646bb602def28614aa6db5e0d60cb40c861302aa9f3bc8a`, rule hash `c3b26f3f0fc8`.

Limit: this is bounded prototype/qualification evidence, not variant acceptance, universal identifiability, measured learning gain, or training admission. Next useful owner action is semantic review of the parameter grammar followed, only if desired, by a separate exact-source acceptance decision.
