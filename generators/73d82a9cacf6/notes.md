# Working notes: 73d82a9cacf6

## Current parametric decision — review-7b6e9833ed831a81

**Reviewer ready; owner acceptance pending.** Added an opt-in native adapter
with `area_order=larger_first|smaller_first`, 2–6 independently configurable
demonstrations and 1–4 queries. The default program is byte-identical to the
canonical rule. The source generator remains SHA-256
`b8c145b02088ee9cf23ff9e5e35f3ebc07bd03f08b981c9eb9868ee181ce7d11`;
canonical approval and the retained canonical-sampler rotation finding are
unchanged. No training admission is claimed.

The extended sampler uses distinct-color objects with disjoint bounding boxes,
strong five-object demonstrations, and four input sizes through 30x30. Its
largest query has six objects and 242 painted cells, producing a 13x30 packed
output. Hole count remains primary; the parameter changes painted-area order
within equal-hole groups. Position and palette draws are independent of the
hidden setting and requested counts. Every rich pair exposes both sorting
keys, 4-versus-8-connected holes, area versus bbox/perimeter, and area versus
density. Public turns contain the same fixed demonstrations and only the
current query input, with no future-count hint.

Two observed teaching defects were repaired during this review. The initial
sampler could preserve hole-then-scan sorting in arbitrary two-demo subsets
(`teaching-v001`: 69 advisory disagreements). The allowed permutations now
mix opposite area directions inside the two tied groups, for both position and
color. Independent review then demonstrated a density shortcut fitting two
demos but failing the first query under both settings. Larger two-hole shapes
are now less dense, and the density rival is an executed regression. Original
counterexamples and red/green receipts remain under `checks/73d82a9cacf6/`.

Current verification, paths relative to `WORK/`:

- `task-tests-release/result.json`: **72/72** staged task tests passed,
  including the eight unchanged canonical tests and 64 prototype tests.
- `teaching-release/audit.json`: both settings, seeds 0 and 17, 2 or 6 demos
  and four queries; **384 protected Racket evaluations**, 32 chosen-rule
  labels, fourteen total rivals, all rejected by the first two demos; no
  disagreements across 120 cached two-demo subsets. The extra 12-seed census
  has 84 unique inputs but explicitly uses Python-only labels.
- `teaching-release/public-check.json` and `turns-check.json`: four masked
  four-query challenges and sixteen current-query-only turns passed.
- `review-dev/density-rival.json` and `density-rival-after.json`: independent
  protected before/after witness; match masks changed from `[true,true,false]`
  to `[false,false,false]` under both settings.
- `qualification/qualification.json` and `execution.json`: native qualified
  both settings at seeds 0/17, three demos and four queries per job.
- `causal/witness.json` and `replay.json`: two source-bound 30x30 cases replayed
  through protected Racket. Replacing per-object hole counts with zero changes
  sort order and final packing in both settings while preserving other keys.

The inventory is `workspace/parametric/evidence/manifest.json`; runnable
commands, grammar, rival list and evidence scopes are in the adjacent README.
The earlier negative-verifier proof binds the earlier auditor/adapter bytes;
it is retained as such, not recast as a fresh release execution. Finite rival
and seed coverage does not establish uniqueness against arbitrary programs.
After integration the owner must qualify and accept the exact live source.

## Retained canonical repair decision

Keep the generator's hole-count / decreasing-area rule, ordinary two-demonstration curriculum, semantic rivals, and selected Racket authority. Repair only the false `CANONICAL_SHORTCUTS` declaration and make that contract source-bound in the task suite.

## Root cause and repair

`CANONICAL_SHORTCUTS` is the strict inventory of named programs that fit every labeled canonical pair. The baseline declared `hole_count_only` and `reading_order`, but the retained canonical census showed fits of only 4/5 and 1/5 respectively. They are useful lesson competitors, not canonical-fitting shortcuts.

The production declaration is now intentionally empty. Both programs remain in `SEMANTIC_RIVALS` and `LESSON_COMPETITORS`, so ordinary lessons still have to refute them. The regression now loads the five labeled pairs through `reviewer_support`, evaluates every named lesson competitor plus any declared canonical shortcut, and requires the declaration to equal the set that actually fits all five pairs. This makes future additions or semantic drift fail closed instead of relying on prose.

## Retained canonical verification

- RED: `checks/73d82a9cacf6-shortcut-red/result.json` — 1 failed, 7 passed; the failure reported `hole_count_only=[T,F,T,T,T]` and `reading_order=[T,F,F,F,F]`.
- Final task suite: `checks/73d82a9cacf6-release/result.json` — 8/8 passed.
- Default semantic contract: `checks/73d82a9cacf6-semantic-release/result.json` — passed; all 5 canonical inputs accepted, 308/600 strict-profile hits (51.3%, floor 45%), and every sampled witness/rival claim held.
- Selected authority: `checks/73d82a9cacf6-authority-release/result.json` — execution parity passed; no Racket source changed.
- Final generator SHA-256: `b8c145b02088ee9cf23ff9e5e35f3ebc07bd03f08b981c9eb9868ee181ce7d11`; rule hash remains `1d1a8e3f7274`.

## Remaining limitation

The optional strict query-rotation stress in `checks/73d82a9cacf6-semantic-after/result.json` found 6 ambiguous rotations out of 36 and 12 corresponding hook warnings. With `EXAMPLES_NEEDED=2` and alternating single-profile pairs, holding out the lone pair of one profile can leave two same-profile demonstrations. Ordinary production lessons themselves passed 12/12; arbitrary query rotation is a stronger assembly policy and is not declared by this generator. Raising the lesson size to three would remove this structural ambiguity but increase demonstration cost by 50%, so that change is deferred until a downstream assembler explicitly requires arbitrary rotations. `LESSON_SCHEDULE_PERIOD` is likewise undeclared, so exhaustive-period enumeration is not claimed.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-b54a22ef974974cb:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `3bfbea4de6a955f6bd81a1fed39ba001a0a95a6368467b8ac7eaf2bc6587a9cc`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Accepted b8c145b02088ee9cf23ff9e5e35f3ebc07bd03f08b981c9eb9868ee181ce7d11 removes the two false CANONICAL_SHORTCUTS declarations while keeping executable lesson rivals. Reviewer reports8tests, five canonical cases and selected authority parity. Separate rotation ambiguity remains actionable.

### Assessment or prior finding

## 73d82a9cacf6

**Finding: invalid canonical-shortcut declarations.** Generator SHA-256 `3bfbea4de6a955f6bd81a1fed39ba001a0a95a6368467b8ac7eaf2bc6587a9cc` declares `hole_count_only` and `reading_order` in `CANONICAL_SHORTCUTS`, but neither fits every labeled canonical pair. A five-pair census found `hole_count_only` fits 4/5 and `reading_order` fits 1/5. Both fail canonical pair index 1.

The retained Racket application for pair 1 uses executed rule hash `1d1a8e3f7274`, matches the canonical expected output, and disagrees with both declared shortcuts. Evidence:

- `checks/audit/73d82a9cacf6/canonical_shortcut_fit_census.json`
- `checks/audit/73d82a9cacf6/input.json`
- `checks/audit/73d82a9cacf6/racket.json`
- `checks/audit/73d82a9cacf6/declared_shortcut_outputs.json`
- `checks/audit/73d82a9cacf6/analysis.json`

The portable task tests passed 6/6 in `checks/audit/73d82a9cacf6-combined/`, but the combined audit’s semantic stage was interrupted by the wrapper/transport before a verdict. The explicit canonical census and Racket reproducer are sufficient to establish the declaration defect; the interrupted preset is not reported as a pass.

**Suggested owner action:** Keep `hole_count_only` and `reading_order` as lesson competitors if useful, but remove them from `CANONICAL_SHORTCUTS` unless the declaration is narrowed to a canonical subset—which the current contract does not support.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-b54a22ef974974cb-v0001/audit_assets.json), manifest SHA-256 `10c13368470088279e09d8a26b245111b6d7b7304ca3782828afaedeaba36b13`.
<!-- arcpuzzles-current-audit-assessment:end -->
