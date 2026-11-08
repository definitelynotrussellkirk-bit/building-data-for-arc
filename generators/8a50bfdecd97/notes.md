# Current notes: 8a50bfdecd97

Final selected generator version `4.2.0`, SHA-256 `865a9c6ee624589662779b0e0230c0aa6426a3a213184ddd1d2bbed200fcf3b7`. Canonical Racket rule hash `f2d83965d9c2` is behaviorally unchanged; selected `target_code` was synchronized to canonical formatting while archival `raw_code` remains provenance.

## Intended rule

Background is 7. Two disconnected color-4 three-sided brackets occupy diagonal corners. One bitmap uses a single color outside `{4,7}`. Its same-side bracket determines top/bottom destination alignment; the opposite-side bracket's open interior determines columns. Copy only occupied bitmap cells to the missing corner and erase all source bitmap cells to 7.

## Current distribution

`scene_profile` has four canonical-scale public families and nine generalized bitmap families. Public-family defaults may be reflected, recolored, and source-relocated while preserving observable family identity. Explicit overrides remain exact.

A four-pair lesson uses three demonstrations and one query. `LESSON_SCHEDULE_PERIOD = 2`: even indices draw from six profiles with an interior-zero bitmap, odd indices from seven solid-bitmap profiles. Thus every four consecutive pairs contain two transparent witnesses; any single held-out query leaves at least one demonstration refuting the filled-bounding-box shortcut.

## Executable semantics

Declared rivals:

- `copy_instead_of_move`, refuted by source erasure;
- `solid_bbox`, refuted by transparent bitmap interiors.

`strict_canonical_like`, witnesses, rival bindings, and `lesson_identifiable` are executable. Final strict battery is 12/12 green. Final census: 300 lessons, 1,200 pairs, 1,148 unique inputs, 1,200 query rotations, zero ambiguity for declared rivals. These are finite checks, not universal identifiability.

## Decisions and reversals

- Rejected permissive seed/sample-index handling; exact integer/nonnegative validation is now enforced.
- Rejected direct repetition of the four public inputs; lawful variants meet profile support while retaining diversity.
- Reversed independent random profile draws after the first census found 26 production and 76 rotation ambiguities; parity scheduling now supplies two sparse witnesses per lesson.
- Repaired inherited canonical-data tests to use portable `reviewer_support` APIs.

## Prototype

`workspace/parametric/` proposes episode-level `source_action = move|copy`, default `move`. It is separate from production and approval. Final evidence is `checks/parametric/source-action-v2/`.

## Known limits

The sampler covers a designed family of bracket/bitmap scenes, not every input the broad Racket program can execute. Generic label-mutation search leaves a few advisory ambiguous rotations outside the declared competitors. The parity guarantee is tied to consecutive four-pair lesson assembly; any materializer change requires renewed period and rotation checks.
## Current reviewer considerations

Source SHA-256: `865a9c6ee624589662779b0e0230c0aa6426a3a213184ddd1d2bbed200fcf3b7`.

# Decisions: 8a50bfdecd97

Final generator SHA-256: `865a9c6ee624589662779b0e0230c0aa6426a3a213184ddd1d2bbed200fcf3b7`
Canonical rule hash: `f2d83965d9c2` (behavior unchanged)

## D1 — Preserve the canonical move rule

**Original rule.** Detect the non-{4,7} bitmap; use the same-side bracket for vertical alignment and the opposite-side bracket interior for horizontal alignment; stamp only occupied bitmap cells at the missing corner; erase the source to 7.

**Decision.** Keep the Racket behavior unchanged. Synchronize only selected `target_code` formatting through the authority tool and preserve archival `raw_code` as provenance.

**Alternative rejected.** Changing Racket to accommodate sampler or test failures would hide generator defects. Final rule smoke and authority sync establish parity on the unchanged rule.

## D2 — Validate external controls at the boundary

`seed` and `sample_index` now require exact integers, excluding booleans; `sample_index` must be nonnegative. Difficulty and override names/values are checked before any keyed draws.

**Failure addressed.** Baseline defect lint reported 33 accepted-invalid-scalar warnings.

**Limit.** This validates the public generator contract, not arbitrary internal helper calls.

## D3 — Raise canonical support with lawful variants, not repeated labels

**Prior distribution.** Nine generalized pattern profiles produced only 8/60 canonical-profile hits.

**Decision.** Add four public anchor families and transform them with lawful reflections, palette changes, and source relocation. Preserve the source family in `observe_overrides` by recognizing dimensions plus shape mask.

**Rejected alternative.** Repeating the four exact public grids would improve the profile count while reducing training value and risking a duplicate-heavy corpus. The chosen variant strategy yields 21/60 exact hits while retaining 98% unique inputs in the final diversity sample.

**Limit.** Generated support remains a designed neighborhood of the canonical family, not all grids accepted by the Racket program.

## D4 — Make the two most plausible shortcuts executable

The task now declares and tests:

1. `copy_instead_of_move`, refuted by source erasure;
2. `solid_bbox`, refuted by transparent bitmap interiors.

`strict_canonical_like`, `SEMANTIC_WITNESSES`, `SEMANTIC_RIVALS`, `LESSON_COMPETITORS`, `WITNESS_RIVALS`, and `lesson_identifiable` form a source-bound contract. These are finite rivals, not an exhaustive hypothesis space.

## D5 — Schedule two transparent witnesses in every four-pair lesson

**Initial choice.** Randomly select any profile for every pair.

**Failure.** The first 300-lesson census found 26 production ambiguities and 76 held-out-query ambiguities for `solid_bbox`; in those lessons the only transparent bitmap could be the query.

**Decision.** Declare `LESSON_SCHEDULE_PERIOD = 2`. Even sample indices draw from six transparent profiles; odd indices draw from seven solid profiles. Every four consecutive indices contain two from each pool, so holding out any one pair leaves at least one transparent demonstration.

**Verification.** A focused regression exhausts multiple bands, seeds, and cyclic starts; strict battery period enumeration passes; the final 300-lesson census and all 1,200 rotations refute both declared rivals.

**Limit.** The guarantee assumes the current 3-demo/1-query consecutive assembly. A different lesson materializer must rerun the census rather than inherit the claim.

## D6 — Keep explicit overrides exact

When `scene_profile` is supplied, all thirteen values remain legal regardless of parity. The schedule constrains only default draws. Final override checking accepted 1,260/1,260 draws over 14 cases and three bands.

## D7 — Repair portable tests rather than weaken staging

The inherited test's repository-relative canonical path failed in the isolated runtime. It now locates roots and canonical pairs through `reviewer_support`. Selected-source tests also distinguish canonical selected text from preserved archival text. This keeps the portability gate meaningful.

## D8 — Add a separate `source_action` prototype

**Parameter.** `source_action ∈ {move, copy}`, fixed once per episode; default `move` is canonical.

**Invariant reasoning.** Bitmap identification, bracket roles, destination alignment, colors, and transparent stamping do not change. Only source erasure varies.

**Evidence.** One retained episode per setting, four query rotations each, exact Racket receipts, and a cross-setting witness. Every rotation refutes the alternate setting from demonstrations.

**Status.** Proposed prototype only. It is not selected production code, catalog authority, or training approval.

## D9 — Retain failed evidence and bounded limitations

The failed random-schedule census is retained in compressed form plus its companion summary. The final census proves only the declared rivals over its seeds and rotations. Generic label-mutation search leaves a handful of advisory ambiguities; these are recorded rather than promoted to unsupported defects.
