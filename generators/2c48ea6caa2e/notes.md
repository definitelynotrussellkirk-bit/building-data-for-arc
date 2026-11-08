# Working notes: 2c48ea6caa2e

## Intended rule

Find the bounding box of blue (`1`) cells. Preserve every blue cell. For each
zero cell inside that box, paint red (`2`) exactly when its complete row or
complete column contains at least four blue cells; every other cell is zero.
The canonical Racket `RULE_HASH` remains `1a8db7bae695`.

## Current generator decisions (v4.0.0)

- Preserve the four complete published masks and their D4 orientations; bounded
  zero padding is the nuisance transformation.
- Add `threshold_witness_9x9`, a minimal lawful mask containing a row/column
  count of exactly four in a nine-cell span. It refutes the plausible but wrong
  “strict bbox majority” rule that fits all eight linked canonical pairs.
- Use a four-step teaching schedule with threshold witnesses and published-mask
  anchors. Exact-profile anchors provide 15/60 pooled exact/envelope support in
  the pinned profile-floor census and at least one exact hit per band.
- Exclude only `frame_7x9` from *default anchor slots*: its exact same-canvas
  orbit has only 12 variants and caused the 300-draw diversity test to stop at
  280 unique grids. It remains available in ordinary generation and every exact
  override.
- Reject non-integer/bool `seed` and `sample_index`, and reject negative sample
  indices, before constructing the generation context.

## Semantic evidence and limits

The declared `bbox_majority` rival fits every canonical pair. The retained
counterexample is
`counterexamples/majority_threshold_counterexample.json`; its intended output
was executed through canonical Racket authority in
`checks/majority-threshold-apply.json`. The final semantic battery observed the
witness in 299/600 draws. A 300-lesson census (100 per band, three ordered demos
plus one query) found 0 production ambiguities and 0 ambiguities in 1,200 query
rotations against that declared rival. This finite rival set is not a proof of
unique induction against every possible rule.

## Proposed parametric extension

`workspace/parametric/` is a separate, unapproved prototype. It chooses fixed
threshold 3, 4, or 5 once per episode; 4 is the canonical default. Three complete
episodes were executed through their exact retained Racket programs, and every
one of the three demonstrations in each episode refuted both alternative
thresholds. Evidence: `checks/parametric/evidence.json`. The diagnostic mask
family is deliberately narrow and does not establish identifiability against
undeclared rivals.

## Authority synchronization

The selected `target_code` in both linked base solution records was synchronized
to the exact canonical formatting. Archival `raw_code`, semantics, and rule hash
were unchanged; the reviewed proposal is `checks/authority-sync-proposal.json`.
## Current reviewer considerations

Source SHA-256: `f7067d936b4c678af79558bb2ff683fe991d0b5b0d9c51ed1e730faa0b5aa833`.

# Decisions for 2c48ea6caa2e

## Scope and evidence policy

No prior return was used as the repair lead. I treated the packet’s pinned selected baseline, linked canonical rows, current focused tests, and freshly generated before-check evidence as authoritative. Historical files were consulted only when named by a current diagnostic or needed to understand the selected authority layout. The canonical Racket semantics were not changed.

## D1 — Keep the original object and composition structure

**Choice.** Preserve the blue occupancy masks, fixed colors, blue bounding box, and the row-or-column composition. Keep global D4 transforms and zero padding as nuisance variation.

**Original rationale.** The four unique linked canonical inputs differ in dimensions and mask geometry but share the same complete-blue-mask role and fixed threshold-4 law. Their exact masks are stronger evidence of the source manifold than a broad procedural “broken frame” grammar.

**Alternatives considered.** Randomly synthesize arbitrary borders, sample independent row and column fragments, recolor semantic roles, or add unrelated distractors.

**Probes.** Every linked pair was checked by an independent Python mirror and the canonical Racket authority; every D4 transform of each complete mask was tested. The final focused suite also enumerates every declared profile, orientation, and padding override in every band.

**Failure modes avoided.** Arbitrary frame synthesis could admit masks that no longer express the canonical broken-frame pattern, recombine row and column clues independently, or introduce count distributions that teach a different rule. Role recoloring would be cosmetic rather than a meaningful rule parameter and could conflict with fixed output semantics.

**Limit.** The canonical generator remains intentionally conservative: it spans the published masks plus one diagnostic near-neighbor, not all imaginable blue bounding-box patterns.

## D2 — Reject non-integer sampling coordinates exactly

**Choice.** Require `type(seed) is int`; require `type(sample_index) is int` and `sample_index >= 0`.

**Original rationale.** The baseline had no explicit scalar contract. Python booleans and integral-looking floats were silently accepted through arithmetic and random seeding.

**Alternatives considered.** Coerce strings/floats with `int(...)`, accept `bool` as an `int`, or leave validation to downstream code.

**Probes.** The red test exercised booleans, floats, strings, `None`, and negative indices. Baseline defect lint reported 33 accepted-invalid-scalar warnings across difficulty settings. The green test requires deterministic exceptions and final defect lint is clean.

**Failure modes avoided.** Silent truncation, aliasing `True` with seed `1`, nondeterministic caller mistakes, and schedule indexing with negative values.

**Limit.** Large integers remain legal; the generator relies on deterministic hashing/random seeding rather than imposing an arbitrary numeric range.

## D3 — Add a minimal fixed-threshold witness, not a new generic grammar

**Choice.** Add `threshold_witness_9x9`, formed by changing one empty cell of the published 9×9 mask so one column has exactly four blue cells. Keep the canonical rule threshold fixed at four.

**Original rationale.** The strongest plausible rival—strict majority of the blue-bbox row/column span—fits all eight linked labeled pairs. A 9×9 bbox gives the rival threshold five, so a row or column with exactly four blue cells separates it from the intended law.

**Alternatives considered.** Add arbitrary random masks; alter a published output label; lower the canonical threshold; or rely on a prose warning without generated support.

**Probes.** `repo/generators/2c48ea6caa2e/counterexamples/majority_threshold_counterexample.json` records the exact disagreement. `checks/majority-threshold-apply.json` re-executes the canonical Racket authority; the intended output differs from the rival at five cells. The semantic census found the witness in 299/600 draws across all bands.

**Failure modes avoided.** A witness outside the generator validator, a Python-only oracle, an accidental semantic authority change, or a rare witness that never enters complete lessons.

**Limit.** This witness refutes one declared canonical-fitting rival. Other undeclared hypotheses may still exist.

## D4 — Use a four-step teaching schedule

**Choice.** Default schedule: `canonical_profile_anchor`, `threshold_witness`, `published_variation`, `threshold_witness`. Lessons use three demonstrations and one query, so every three-consecutive-example window contains a fixed-threshold witness.

**Original rationale.** Independent random sampling could produce complete lessons containing only published masks, leaving bbox-majority indistinguishable even if witnesses exist somewhere in the marginal distribution.

**Alternatives considered.** Pure random profile choice; witness only at one residue in a longer period; force every example to be the witness; or increase demonstrations beyond the existing three.

**Probes.** The task-local lesson hook checks the declared rival on materialized demonstrations and labeled queries. Battery smoke: 12 lessons and 48 rotations, no ambiguity. Production census: 100 lessons per band, 300 total, no ambiguity; diagnostic rotations: 1,200/1,200 no ambiguity.

**Failure modes avoided.** Correct individual labels but unteachable lesson assembly, query-position dependence, and a witness frequency claim that does not imply lesson coverage.

**Limit.** The larger census samples production seeds and treats rotations diagnostically. It does not prove all seeds or undeclared rivals. `LESSON_SCHEDULE_PERIOD` was not declared, so no fixed-seed residue enumeration claim is made.

## D5 — Preserve exact canonical-profile support with anchor slots

**Choice.** Put exact published-shape/profile samples in deterministic anchor positions while retaining normal D4/padding variation elsewhere.

**Original rationale.** The baseline battery showed 0/60 exact and 0/60 envelope canonical-profile hits, despite accepting canonical inputs. The review gate requires direct distribution support, not only validator compatibility.

**Alternatives considered.** Declare a profile-floor opt-out, remove padding, or make all samples exact canonical copies.

**Probes.** Final profile floor: 15/60 exact and envelope hits—easy 4/20, medium 9/20, hard 2/20—with zero crashes. Override tests show all orientations and padding profiles remain observable.

**Failure modes avoided.** A validator-only generator that never emits source-like grids; or overcorrection that collapses diversity to four copied inputs.

**Limit.** Exact-profile hits match height, width, and color count, not necessarily exact byte identity; the source masks are nevertheless explicitly retained and tested.

## D6 — Exclude `frame_7x9` only from default anchor selection

**Choice.** Keep `frame_7x9` in `SCENE_PROFILES`, normal generated variation, and exact override enumeration, but do not select it for default anchor slots.

**Original rationale.** The 7×9 profile on its canonical 9×13 canvas has a small 12-state orbit after symmetry equivalences. Adding deterministic anchors caused the final diversity test to land at exactly 280 unique samples where the gate required more than 280.

**Alternatives considered.** Lower the diversity threshold, delete the profile, add arbitrary noise, or broaden padding even in exact anchors.

**Probes.** Collision analysis isolated the profile/anchor combination. After the narrow exclusion, diversity passed. Exhaustive override tests still reach `frame_7x9` for every D4 orientation and padding profile in every band.

**Failure modes avoided.** Hiding a real diversity failure by weakening a test, losing a published profile, or corrupting exact canonical anchors with synthetic noise.

**Limit.** The default anchor distribution is not uniform over all four published profiles; normal sampling and overrides retain full profile reachability.

## D7 — Synchronize selected authority text while preserving archival source

**Choice.** Apply the hash-pinned authority-sync proposal to the two selected `racket_target.target_code` fields. Preserve `racket_target.raw_code` unchanged.

**Original rationale.** Baseline authority sync showed one normalized semantic group but two exact selected-authority hashes. The canonical program and selected target code solved the same pairs, yet exact active text divergence blocked the gate.

**Alternatives considered.** Change the canonical program, overwrite archival raw source, ignore exact divergence because normalized hashes matched, or refresh `RULE_HASH` without changing semantics.

**Probes.** `checks/authority-sync-proposal.json` records the dry run. Final rule smoke, Racket lint, and authority sync pass. The normalized hash and `RULE_HASH=1a8db7bae695` remain unchanged; final diagnostics explicitly classify archival raw forms as preserved divergences.

**Failure modes avoided.** Losing provenance, changing semantics under a formatting repair, or masking divergence by editing approval metadata.

**Limit.** Archival `raw_code` remains exact-text divergent by design and must not be mistaken for the selected execution authority.

## D8 — Prototype threshold as the one meaningful small rule parameter

**Choice.** Build a separate episode-level parameter `threshold ∈ {3,4,5}`, canonical default `4`, chosen once per episode. Materialize exact Racket programs for each value and keep all prototype code under `workspace/parametric/`.

**Original rationale.** Threshold directly changes the executed transformation while preserving object roles, spatial relation, row/column counts, bounding-box restriction, colors, and output geometry. It is the nearest meaningful semantic variation in the original family.

**Alternatives considered.** Output color, orientation, padding amount, mask identity, row-only versus column-only, or independent row/column thresholds.

**Why rejected.** Output color is largely cosmetic; orientation/padding/mask identity are input nuisance axes, not rule parameters; row-only/column-only or separate thresholds alter the family’s core `OR` composition too strongly for this small extension.

**Probes.** `checks/parametric/evidence.json` contains three complete episodes, exact program text and hashes, Racket/Python parity, and rival comparisons. Every demonstration and query under thresholds 3, 4, and 5 differs from both alternatives. Public episode files omit hidden settings and query labels.

**Failure modes avoided.** Resampling a hidden rule per pair, Python-only labels, ambiguous demonstrations, or silently changing the selected production authority.

**Limit.** The prototype covers three deterministic episodes and the two alternative threshold values only. It is proposed, not integrated or approved.

## D9 — Freeze generator bytes before the exposed solve

**Choice.** Run the post-repair visible-only solve only after final generator verification, and make no generator change afterward.

**Original rationale.** Solve evidence must bind to the exact returned generator, otherwise a passing solve can describe stale lesson behavior.

**Alternatives considered.** Reuse an earlier solve or edit the generator after solving without regenerating the episode.

**Probes.** `solve/summary.json` records generator SHA-256 `f7067d936b4c678af79558bb2ff683fe991d0b5b0d9c51ed1e730faa0b5aa833`, one passing visible revision, earlier exposure `yes`, and reference consulted `no`. The final source hash matches the battery and focused test runtime manifests.

**Failure modes avoided.** False “fresh solve” claims, stale generation provenance, and reference leakage during the solve lane.

**Limit.** This is an exposed reviewer solve, not a blind model evaluation; masked query labels remain unscored in the packet.
