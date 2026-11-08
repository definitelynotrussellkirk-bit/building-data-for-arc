# Working notes: `78645c33b002`

## Intended rule

Extract the colors of the complete nested filled rectangular layers from outside
to inside, reverse that order, and render them as concentric square rings. For
`K` layers the canonical output side is `2K-1`. Canonical Racket remains
unchanged at rule hash `d565393b63e9`.

## Current selected generator

- Version `3.1.0`; final source SHA-256 `1228809dbcf50ab328ba7fede9cd620f96c45dee9ed551c3d0832a91030625f5`.
- `seed` must be a literal Python `int`; `sample_index` must be a nonnegative
  literal `int`.
- `EXAMPLES_NEEDED = 3` and generated lessons use three demonstrations plus one
  query.
- Declared rival: `main_diagonal_run_compression`, which fits all eight canonical
  pairs. The retained off-center replay `(seed=93, sample_index=93,
  difficulty=medium, scene_profile=tall_offcenter)` refutes it.
- `LESSON_SCHEDULE_PERIOD = 80`. Every even default index is a guaranteed rival
  witness; odd positions preserve a 37.5% public-profile share and cover all
  remaining profiles. Every four-pair window has at least two witnesses.
- Explicit profile replay uses `DRAW_VERSION = "3.0.0"`; default curriculum uses
  the new schedule.

## Evidence and decisions

The old production sampler, measured after registering the rival, had 18/300
ambiguous lessons and 52/1,200 ambiguous rotations. Final evidence has 0/300 and
0/1,200, plus 0/240 cyclic starts and 0/960 cyclic-start rotations at schedule
seed 0. The full after battery is 12/12 green; focused repair/parametric tests are
18 passed. Exact profile support is 8/60 and envelope support is 15/60, with no
crashes.

Selected solution `target_code` text was synchronized to canonical through the
reviewed authority workflow. Archival `raw_code` was intentionally preserved;
there was no semantic rule change.

## Parametric prototype

`workspace/parametric/` proposes episode-level `ring_thickness ∈ {1,2}`.
Setting 1 is exact canonical Racket; setting 2 makes noncentral rings two cells
thick while preserving layer extraction and ordering. Both settings have complete
three-demo/one-query episodes and protected-Racket evidence. Status is proposed,
not production-approved.

## Known limits / open findings

The semantic guarantee is finite and only covers the declared diagonal rival;
other hypotheses remain possible. The schedule intentionally biases default
sampling toward off-center witnesses, though all advertised profiles remain
reachable and profile/diversity gates pass.

The inherited frozen root fixture still uses a fixed `parents[...]` path and
fails portable task-test collection. It was not edited because the assignment
forbids that; maintainer migration to `reviewer_support.find_root` is required.
Independent audit findings for `022556f7ee2c` and `325fb006a344` are recorded in
the review return and were not fixed out of scope.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-508d7a420aa7425e:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `c55efe934e66f089c08b81dc95540207696735fc6ce5579dc515fdbde78f1dfa`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Resolved by accepted source 1228809dbcf50ab328ba7fede9cd620f96c45dee9ed551c3d0832a91030625f5 based on reviewer-reported repair evidence; no owner rerun. The previously missing main_diagonal_run_compression rival/witness and lesson hook are implemented. The 80-step schedule guarantees at least two witnesses in every four-pair window; checks/schedule-period-s0.summary.json covers 240 starts/960 rotations and checks/lesson-census-final.summary.json covers 300 production lessons. New focused tests pass 18; the frozen task-test aggregate remains blocked separately. This closes only this finding, not other audit records.

### Assessment or prior finding

## 78645c33b002

**Classification: canonical-fitting shortcut with a reproduced generated counterexample; semantic-contract gap, not a demonstrated distribution failure.**

A simple rival fits all **8/8 canonical pairs**: run-length-compress the input’s NW-to-SE main diagonal, then emit a square whose concentric rings follow that palindromic color sequence. For the canonical inputs, the compressed diagonal is exactly the output diagonal, so the rival reconstructs every canonical output without locating the nested rectangles in two dimensions. The complete canonical check is `checks/audit/78645c33b002/canonical_shortcut_check.json`.

The current production generator does emit a lawful counterexample. Seed `93`, sample index `93`, difficulty `medium`, override `scene_profile="tall_offcenter"` reproduces the retained `27×22` input. It passes the target validator, belongs to the documented generator domain, and replaying the production generator matches the saved input exactly (`checks/audit/78645c33b002/comparison.json`). The true nested layer sequence is `[3,7,8,9,0]`, but the compressed main diagonal omits the off-center innermost zero region and yields `[3,7,8,9,8,7,3]`. The rival therefore emits a `7×7` result, while the supported Racket authority emits the correct `9×9` result with center color `0`.

The authoritative output was obtained with:

```text
python3 run_with_racket.py python3 -m arcpuzzles apply 78645c33b002 --input ../checks/audit/78645c33b002/input.json --out ../checks/audit/78645c33b002/racket.json
```

The command exited `0`; the report records generator SHA-256 `c55efe934e66f089c08b81dc95540207696735fc6ce5579dc515fdbde78f1dfa`, executed rule hash `d565393b63e9`, input/output hashes, and a valid output. The rival output and exact generation coordinates are adjacent in `checks/audit/78645c33b002/`.

Static lint, defect lint, and override-contract stages all passed for this target. The strict semantic stage failed because the generator declares no `strict_canonical_like`, semantic witness/rival contract, or `lesson_identifiable` hook (`checks/audit-78645c33b002-semantic/checks/78645c33b002_after_semantic_gate.log`). Because the generator already emits the necessary off-center witness, I did **not** find evidence that its raw distribution can never teach the intended rule. The actionable gap is that no executable lesson contract guarantees complete lessons actually include a witness that defeats the diagonal shortcut.

**Patch status:** audit only; unchanged.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-508d7a420aa7425e-v0001/audit_assets.json), manifest SHA-256 `b0e40b79f486c844d2686dbd680c810a638ebe10dc56871c0f7dc07b1af7a42a`.
<!-- arcpuzzles-current-audit-assessment:end -->
## Current reviewer considerations

Source SHA-256: `1228809dbcf50ab328ba7fede9cd620f96c45dee9ed551c3d0832a91030625f5`.

# Decisions for `78645c33b002`

## D1 — Preserve the canonical rule and parameterize ring thickness separately

**Prior choice/rationale:** the canonical generator had a fixed one-cell ring
rule; no current rationale for omitting parameter evidence was recorded.

**New choice:** keep production fixed at the canonical authority and build a
separate prototype with `ring_thickness ∈ {1, 2}`, chosen once per episode.
Setting 1 is byte-identical to canonical Racket; setting 2 changes output size and
layout while preserving the original nested-layer extraction and ring-rendering
reasoning.

**Alternatives rejected:** target/output recoloring was too cosmetic, while
reversing layer order would change the central relationship rather than expose a
small nearby behavior. Input size, placement, and sampling-weight changes were
also rejected because they do not change the executed rule.

**Probe/evidence:** two complete episodes, both settings, six distinguishing
demonstrations, and 16 protected-Racket executions are recorded under
`checks/parametric/episodes-final/`. This is bounded prototype evidence, not an
approval or all-seed claim.

## D2 — Model the strongest canonical-fitting shortcut explicitly

**Prior choice/rationale:** no executable semantic rival was declared. A retained
older audit suggested diagonal extraction, but it targeted generator SHA
`c55efe934e66f089c08b81dc95540207696735fc6ce5579dc515fdbde78f1dfa`,
not the pinned source.

**New choice:** declare `main_diagonal_run_compression`, connect it to a concrete
witness, and make `lesson_identifiable` reject lessons where it survives all
three demonstrations and changes the query.

**Why this rival:** it fits all eight canonical labeled pairs, is substantially
simpler than full rectangle-layer extraction, and fails exactly when an
inner off-center layer misses the NW–SE diagonal. The new source-bound witness
is retained in `counterexamples/main_diagonal_run_compression.json`.

**Limit:** the registry is finite. Passing it does not establish unique induction
against unlisted hypotheses.

## D3 — Use an 80-step curriculum schedule instead of rejection sampling

**Intermediate evidence:** after registering the rival but before schedule
repair, a 100-per-band census found 18/300 ambiguous production lessons and
52/1,200 ambiguous rotations.

**New choice:** every even default index emits a deterministic shortcut witness;
odd positions retain a 37.5% public-profile share and cycle all remaining
profiles. Every four-pair lesson window therefore has at least two witnesses,
including under any single held-out query rotation.

**Alternatives rejected:** per-lesson rejection sampling would make replay and
coverage harder to audit; forcing all inputs to one witness profile would erase
canonical/profile diversity; a single witness per lesson would fail when that
pair became the query.

**Measured result:** 300/300 production lessons and 1,200/1,200 rotations passed
the final census. All 240 fixed-seed period starts and 960 rotations passed the
separate enumeration.

**Failure mode/limit:** the default sampler is now intentionally biased toward
`thin_offcenter`; schedule seed 0, not every possible seed policy, was fully
enumerated. Profile-floor and diversity probes were retained to expose collapse.

## D4 — Make scalar boundaries literal and deterministic

**Prior choice:** Python truthy/subclass behavior let booleans through as ints and
accepted floats, strings, and negative sample indices.

**New choice:** require `type(seed) is int`; require `type(sample_index) is int`
and `sample_index >= 0`. Nine regression cases cover `True`, `False`, floats,
strings, and `-1`.

**Reason:** invalid scalars can alias replay streams and violate the public
contract. The narrow checks remove ambiguity without changing any lawful draw.

## D5 — Preserve explicit-profile replay streams

**New choice:** separate source `VERSION = "3.1.0"` from `DRAW_VERSION = "3.0.0"`.
The default schedule changes, but explicit `scene_profile` overrides use the
pre-repair stream labels and replay the retained off-center counterexample.

**Reason:** curriculum repair should not silently invalidate exact profile-based
reproducers. The override stage and focused replay test cover this boundary.

## D6 — Synchronize selected authority text, not archival history

**Prior state:** the selected `target_code` entries had execution parity with the
canonical program but differed in exact formatting.

**New choice:** apply the reviewed proposal only to those selected fields. Leave
`raw_code` untouched as archival evidence. No canonical row or Racket semantics
changed; `RULE_HASH` remains `d565393b63e9`.

**Alternative rejected:** rewriting archival fields would erase provenance;
changing the rule hash to bless formatting drift would be false authority repair.

## D7 — Keep the frozen fixture failure visible

**Choice:** do not edit `tests/test_generator_78645c33b002.py`. It is frozen by the
assignment and fails only after the portable stage relocates it, because its
fixed `parents[...]` root guess points beneath the task.

**Replacement coverage:** new tests use `reviewer_support.find_root`,
`canonical_pairs`, and `load_selected_generator`, and 18 focused tests pass.

**Consequence:** the owned generator repair is green, but aggregate completion is
`blocked` until a maintainer migrates the inherited fixture.

## D8 — Do not alter unrelated audited generators

The random audits reproduced defects in `022556f7ee2c` and `325fb006a344`.
Assignment scope requires evidence only, so no source for either target was
changed. Their exact current hashes, inputs, Racket outputs, and findings are in
`AUDIT.md` and `checks/audit/`.
