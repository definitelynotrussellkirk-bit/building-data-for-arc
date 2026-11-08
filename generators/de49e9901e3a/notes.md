# Working notes: de49e9901e3a

## Current rule and authority

The selected Racket authority is unchanged (`RULE_HASH = 1f198bb08b3a`). It paints the Cartesian product of the occupied rows and occupied columns of every monochrome 4-connected object. For a 4-connected object, both coordinate projections are contiguous: every path between cells on opposite sides visits every intermediate row/column. Therefore the authority is exactly same-color bounding-box fill, not a transformation that can be sparser than the bounding box.

## Reversed design choices

The imported `1.3.1` sampler used arbitrary grown blobs and advertised nine axes, including palette, density, position, and degenerate texture controls. Several controls were inert or false, some advertised degenerates violated `self_check`, exact overrides failed, and the notes incorrectly claimed that a connected blob could distinguish occupied-row × occupied-column closure from bounding-box fill.

Version `2.0.0` instead uses a constructive four-zone layout and only four observable exact controls: `grid_h` (8..18), `grid_w` (8..18), `n_objects` (2..4), and `n_colors` (1..2). Every joint combination is constructible, including 8×8 with four objects. Public `seed`, `sample_index`, `difficulty`, and overrides are validated strictly; Boolean, float, string, negative-index, unknown-axis, and out-of-range requests are rejected.

The production curriculum now uses four canonical-profile positions out of each five sample indices and one broader position. The retained after battery measured 38/60 exact canonical profiles and 38/60 envelope hits, with support in every difficulty band. `self_check` describes the lawful input manifold and accepts all five canonical inputs; the extra teaching witness is checked separately through `SEMANTIC_WITNESSES`.

## Shortcut analysis and teaching witness

The strongest retained canonical-fitting rival is `complete_crosses_only`: fill an object only when its cells are exactly one complete occupied row union one complete occupied column; otherwise copy it unchanged. It matches all five canonical pairs because every canonical object has that cross/L/T form. The exact counterexample is `counterexamples/cross_only_shortcut.json`: its color-4 staircase must fill a 3×3 box under the authority but is unchanged by the rival. Every production draw contains a rotated/reflected staircase witness plus ordinary cross-shaped objects.

Evidence is source-bound to generator SHA-256 `79bfec066e3387eb4214742237281daa6412437bc198b753aae0c9b5f4e1841f`. The strict after battery passed all 12 stages; semantic sampling found the witness in 600/600 draws and canonical legality in 5/5 inputs; the wider census materialized 300 lessons with three demonstrations and one query each, found 1,200 unique inputs, and found no ambiguity against the declared rival in production order or any of 1,200 held-out-query rotations. These finite checks do not prove uniqueness against undeclared rules.

## Proposed parametric extension

`workspace/parametric/` contains a separate proposed prototype, not a production or catalog change. It selects one episode-level `eligible_objects` value: canonical/default `all`, or `cross_only`. The setting is deterministic from the episode seed, fixed across three demonstrations and one query, and every retained episode distinguishes the settings. `checks/parametric/verification.json` records exact Racket execution, Python parity, program hashes, two complete episodes, and opaque public challenges.

## Known limits and open findings

Generated object bounding boxes are deliberately small (2×2 through 3×3), grids contain only 2–4 objects and 1–2 colors, and the finite rival census covers the declared cross-only shortcut plus shared generic rivals rather than all possible hypotheses. Same-color objects are kept cardinally separate and bounding boxes do not overlap. The canonical Racket authority and canonical data were not edited.
## Current reviewer considerations

Source SHA-256: `79bfec066e3387eb4214742237281daa6412437bc198b753aae0c9b5f4e1841f`.

# Design decisions for `de49e9901e3a`

## D1 — Treat the authority as bounding-box fill for connected objects

**Prior choice and rationale:** The imported comments described occupied-row × occupied-column closure as potentially sparser than a bounding box and named `fill bbox solid` as a rival. The original rationale was not mathematically valid for the actual domain of monochrome 4-connected objects.

**Decision:** Keep the Racket authority unchanged and describe its effect accurately. A 4-connected path between cells in different rows/columns must pass through every intermediate coordinate, so both projections are contiguous and their Cartesian product is the full bounding box.

**Alternatives rejected:** Editing the canonical Racket rule to make the distinction real would change authority; generating disconnected components as one object would contradict the runtime's object definition; continuing the old explanation would preserve a false teaching claim.

**Probe/evidence:** Independent component/bounding-box oracle over all canonical pairs and the unchanged authority smoke/sync reports under `checks/after/`.

**Limits/failure modes:** The equivalence depends on the authority's monochrome 4-connected object extraction. It should be reconsidered if that domain changes.

## D2 — Replace arbitrary grown blobs and nine advertised axes with four constructive axes

**Prior choice and rationale:** Version `1.3.1` grew arbitrary blobs and advertised `grid_h`, `grid_w`, `palette_kind`, `n_blobs`, `palette_size`, `position_bias`, `n_distinct_colors`, `density`, and `texture`, apparently to maximize surface diversity. The baseline battery showed inert/aliased controls, illegal degenerates, override mismatches, and generation failures.

**Decision:** Use a deterministic 2×2 zone layout with exactly four truthful controls: dimensions, object count, and color count. Object boxes are disjoint, every advertised combination is constructive, and a compact 8×8 grid can hold four objects.

**Alternatives rejected:** Retaining grown blobs plus rejection sampling remained difficult to make exact at small grids and obscured which controls were actually honored. Keeping decorative palette/density axes would not change the observed structural task. A larger grid minimum would avoid layout pressure but unnecessarily narrow canonical support.

**Probe/evidence:** The final override gate accepted 24,030/24,030 exact draws across 267 cases with zero findings; `test_all_exact_controls_are_observable_at_smallest_joint_case` covers 8×8, four objects, and both color counts.

**Limits/failure modes:** The layout's four zones cap production at four objects and deliberately avoid overlapping bounding boxes. This is documented rather than advertised as a broader domain.

## D3 — Use a four-of-five canonical-profile curriculum

**Prior choice and rationale:** The imported difficulty ranges drifted away from canonical dimensions and did not reliably cover exact canonical profiles. Its exact rationale was not recorded.

**Decision:** For sample indices whose residue modulo five is not four, strongly anchor one of the four canonical `(height, width)` profiles with two objects and two colors. The fifth residue uses broader difficulty-weighted dimensions/object counts. The full public domains remain reachable because the draw includes every legal value and exact overrides dominate.

**Alternatives rejected:** Always using canonical profiles would restrict diversity; a weak random mixture failed the profile floor; hard-coding one profile per difficulty would couple semantics to difficulty and miss canonical variation.

**Probe/evidence:** `checks/after/checks/de49e9901e3a_after_profile_floor.json` measured 13/20 easy, 13/20 medium, and 12/20 hard exact hits (38/60 total), with zero canonical rejections and support in all bands. Diversity retained 300 unique sampled inputs/outputs in the battery, and the wider census found 1,200 unique pair inputs.

**Limits/failure modes:** This is a weighted curriculum, not a uniform sampler. Exact-profile evidence uses dimensions and distinct-color count, not every visual statistic of the canonical pairs.

## D4 — Teach against the strongest canonical-fitting shortcut on every draw

**Prior choice and rationale:** The old sampler only required some nonrectangular object, which refuted identity but did not address a rule that completes only the particular cross/L/T shapes seen canonically.

**Decision:** Make the first object a rotated/reflected five-cell 3×3 staircase; make remaining objects ordinary one-row/one-column crosses. Declare `complete_crosses_only` in all rival hooks and retain the exact JSON counterexample.

**Alternatives rejected:** Randomly hoping for a non-cross object made lesson quality probabilistic. Using only staircases would erase canonical visual continuity. A more complex rival library was unnecessary until a concrete canonical-fitting competitor was identified.

**Probe/evidence:** Canonical rival fit is 5/5. The semantic gate found the non-cross witness in 600/600 draws. The 300-lesson census found no declared-rival ambiguity in production order or 1,200 query rotations. The counterexample is covered by task tests.

**Limits/failure modes:** This refutes one strong named rival and the shared generic rivals; it is not a proof that no other compact program fits a lesson. The repeated staircase family may itself become a recognizable motif.

## D5 — Separate legality from lesson coverage

**Prior choice and rationale:** During repair, `self_check` initially required the non-cross teaching witness. That caused the canonical inputs to fail even though they are lawful for the authority.

**Decision:** `self_check` and `strict_canonical_like` validate only the legal input manifold. `SEMANTIC_WITNESSES` separately requires the non-cross object for generated teaching evidence.

**Alternatives rejected:** Expanding legality to every arbitrary authority input would make profile checks too weak; retaining the witness in `self_check` would falsely reject canonical authority data.

**Probe/evidence:** A red regression test first reproduced canonical rejection; after separation, all five canonical inputs pass and semantic witness coverage remains 600/600.

**Limits/failure modes:** Future witnesses must remain separate from legality unless they are genuinely necessary for every valid task input.

## D6 — Enforce a strict public scalar and override contract

**Prior choice and rationale:** The imported generator delegated controls to `gen_ctx` and accepted unknown/inert keys and noncanonical scalar types. No strict public contract was documented.

**Decision:** Require exact Python integers (not Boolean/float/string) for `seed`, `sample_index`, and integer axes; require nonnegative sample indices; accept only `None/easy/medium/hard`; reject unknown and out-of-range overrides.

**Alternatives rejected:** Implicit coercion creates collisions and silently changes schedule behavior. Ignoring unknown keys hides caller mistakes and makes override evidence meaningless.

**Probe/evidence:** Focused red/green tests cover bad scalars and keys. Defect lint, ordinary lint, and the override stage are green in the final battery.

**Limits/failure modes:** This intentionally breaks callers that previously relied on coercion; they should pass explicit valid values.

## D7 — Keep the rule-varying experiment separate as a proposed prototype

**Prior choice and rationale:** The canonical production API is fixed to one authority, while the assignment requested assessment of small meaningful rule parameters.

**Decision:** Add task-local `workspace/parametric/` with one episode-level parameter, `eligible_objects ∈ {all, cross_only}`. `all` is the original/default canonical behavior. The hidden setting is selected deterministically once per seed and reused for all three demonstrations and the query. Inputs guarantee observable disagreement.

**Alternatives rejected:** Varying color, size, or layout would alter inputs but not the executed rule. Adding the parameter to production would violate the current authority boundary. A threshold/count parameter was less faithful to the family's core object-closure distinction.

**Probe/evidence:** `checks/parametric/verification.json` executes exact Racket for both settings, records program hashes `3e3106…e28b` and `0df3c8…fb10`, verifies Python parity, and shows all three demonstrations plus the query disagree with the alternative in both retained episodes. Public challenge JSON omits hidden settings, programs, and query answers.

**Limits/failure modes:** Only two settings and two retained seeds are evidenced. The prototype is proposed, not approved or runtime-integrated, and it does not modify the canonical generator or Racket rule.

## Stopping decision

The canonical repair, requested prototype, post-repair visible-only solve, and two assigned audits are complete. The remaining limitations are finite rival coverage and the deliberately narrow small-object production family; neither blocks routine acceptance because they are explicit, tested, and do not contradict the advertised contract.
