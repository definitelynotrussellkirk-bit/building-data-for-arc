# Working notes: 6d33e42a400d

## Current rule and source

Copy the connected source terrain across the paired sparse-marker/source-anchor lines, recoloring the reflected copy with the sparse marker color. Generator version is `2.0.0`; current generator SHA-256 is `dd721b3da2bf4fc979fa7eacdb864f051bea2dae0be2cdb7e8f65449780a5012`; canonical rule hash is `d5de5966b074`.

## Review repairs

- Enforce exact integer `seed`, exact nonnegative integer `sample_index`, and `difficulty in {None,easy,medium,hard}`.
- Declare executable rivals for preserving source color and copying only marker-aligned cells.
- Declare sparse deterministic witnesses on `public_h8/orientation=0` and `public_v8/orientation=0`; they cover every band without altering generation.
- Require three demonstrations to refute each declared competitor before one query.
- Synchronize selected base-record `target_code` to canonical `program_solution`; canonical Racket source is unchanged and archival `raw_code` is preserved.

## Evidence

- Final battery: 12/12 green (`checks/after/result.json`).
- Focused tests: 31/31 green (`checks/focused-tests/result.json`).
- Lesson census: 300/300 lessons, 1,200 production pairs, 1,200 rotations, zero declared-rival ambiguity or errors (`checks/lesson-census-final.summary.json`).
- Profile floor: 20/60 exact and 20/60 envelope, with all six canonical inputs accepted.

## Parametric prototype

`workspace/parametric/` proposes episode-level `copy_color_role={paint,source}`. `paint` is byte-exact canonical; `source` changes only the reflected-copy color. The sampler and inputs are parameter-independent, one private value is fixed per episode, and all labels/counterfactuals are Racket-executed. Evidence has 2 episodes, 8 episode labels, 8 counterfactual labels, 8 query rotations, and zero ambiguity. This is proposed evidence, not production approval.

## Known limit / blocker

The frozen baseline fixture `tests/test_generator_6d33e42a400d.py` uses a fixed-depth canonical-data path and fails staged portable preflight before pytest collection. It was intentionally not edited per packet policy, so completion is blocked even though both new portable test modules pass.

Finite rival tests do not prove universal identifiability. The census found advisory generic output-mutation candidates; these are not considered domain-valid rules without a provider-level review (`checks/question/searched-rival-witness.json`).

## Decision history

No prior return was used as the lead. The current packet's baseline battery drove the repair. The first broad semantic-witness implementation was narrowed to deterministic profile/orientation slices after it caused redundant Racket evaluation; this changed measurement cost only, not generated data or semantics.
## Current reviewer considerations

Source SHA-256: `dd721b3da2bf4fc979fa7eacdb864f051bea2dae0be2cdb7e8f65449780a5012`.

# Decisions: 6d33e42a400d

## D1 — Reject malformed scalar calls at the public boundary

**Choice.** Require exact integers for `seed` and nonnegative `sample_index`; require `difficulty` to be `None` or one of the three exact band strings.

**Reason.** The baseline defect linter reproduced 48 invalid calls that were silently coerced or routed into the medium band. A generator contract should fail deterministically before RNG or profile selection rather than treating booleans, floats, strings, negative indices, or unknown bands as valid data.

**Alternatives rejected.** Coercing with `int(...)` would preserve ambiguity and accept booleans. Falling back to medium for unknown difficulty would hide caller mistakes and contaminate band-specific datasets.

**Probe.** Twelve parameterized regression cases in `tests/test_review_repairs.py`; final defect lint is green.

## D2 — Use two task-domain rival rules

**Choice.** Declare `copy_in_source_color` and `copy_only_marker_coordinates` as both semantic rivals and lesson competitors.

**Reason.** They represent the two most plausible errors visible from the task presentation: confusing source versus paint color, and treating sparse marker positions as the only cells to copy rather than using them to define a line/role.

**Alternatives rejected.** A no-op, constant output, or arbitrary cell deletion is easy to refute but adds little training value. Changing reflection direction or line gap would mix geometry recognition with the specific semantic choices this generator needs to teach.

**Probe.** Every declared rival is executable, differs from canonical on its witness, and is refuted in all 300 production lessons and all 1,200 held-out query rotations.

## D3 — Keep semantic witnesses sparse and deterministic

**Choice.** Bind the color-role witness to `public_h8` orientation 0 and the full-terrain witness to `public_v8` orientation 0.

**Reason.** The first implementation allowed both predicates to fire on nearly every sampled grid, turning the semantic gate into hundreds of redundant Racket calls. Profile/orientation slices preserve deterministic coverage in every difficulty band while keeping the gate bounded.

**Failure mode considered.** A slice could be too rare and silently disappear from a band. `test_semantic_witnesses_are_sparse_but_cover_every_band` samples 200 deterministic profile-floor draws per band and requires each witness to appear at least once but no more than 20 times.

**Distribution effect.** None. Witnesses inspect returned grids; they do not gate, resample, or alter generation.

## D4 — Require three demonstrations for lesson identifiability

**Choice.** `EXAMPLES_NEEDED = 3`; the lesson hook checks the three demonstrations against every declared competitor, with one remaining query. Rotation evidence holds out each of the four pairs in turn.

**Reason.** This matches the intended export shape and provides enough independent examples to teach both color role and full terrain extent. The small battery and 300-lesson census show both production and arbitrary query-position support against the declared rivals.

**Limit.** This is finite rival testing, not a proof against every conceivable hypothesis. Generic searched mutations remain advisory until a domain-valid provider establishes that they are meaningful rules.

## D5 — Synchronize selected authority text only

**Choice.** Replace only `/racket_target/target_code` in the two selected base records with exact canonical `program_solution`; preserve `raw_code` byte-for-byte.

**Reason.** Baseline authority sync showed three source-text groups but execution parity across all three. The selected active authority must be exact; the archival source must retain history. The automatic helper correctly refused a token-changing edit, so an explicit manual review was recorded.

**Alternatives rejected.** Editing canonical Racket would change authority unnecessarily. Replacing archival `raw_code` would erase provenance. Accepting execution parity alone would leave the strict selected-source gate red.

## D6 — Parameterize copy color, not geometry

**Choice.** Add a proposed episode-level `copy_color_role` parameter with exactly two values:

- `paint`: canonical default;
- `source`: reflect the same terrain but preserve source color.

**Reason.** This is a small, interpretable rule parameter that preserves the task's reasoning pattern, geometry, sampler, and canonical default. It yields a genuine counterfactual that is visibly distinguishable from demonstrations.

**Input constraints.** None beyond the existing lawful generator domain. Inputs are generated independently of the parameter and are identical when the same seed is evaluated under both values.

**Episode policy.** One private value is fixed for all four pairs. Public data contains three labeled demonstrations and one unlabeled query; private files retain the parameter, program, and query answer.

**Alternatives rejected.** Varying line gap, marker count, depth, or orientation changes scene geometry rather than the rule. Reversing reflection direction risks creating a different family or out-of-bounds behavior. A boolean `recolor` flag was rejected in favor of an explicit role-valued parameter that remains extensible and readable.

**Evidence.** `checks/parametric/copy-color-role-v1/` contains Racket-backed public/private episodes, both source hashes, production and all-query-rotation scoring, and a self-verification receipt.

**Status.** Proposed only; it is not wired into canonical generation or training admission.

## D7 — Preserve the frozen fixture and report blocked

**Choice.** Do not edit `tests/test_generator_6d33e42a400d.py`, even though its fixed-depth canonical path prevents portable collection.

**Reason.** The packet expressly identifies it as a frozen fixture and assigns migration to the library maintainer. Rewriting it would make the return look green by modifying evidence outside the allowed reviewer-owned test lane.

**Consequence.** `completion_state` is `blocked`; the 31 focused tests are reported separately and not mislabeled as an aggregate task-test pass.

## D8 — Treat generic searched rivals as a tooling lead, not a task defect

**Choice.** Retain the first witness and aggregate counts, but do not reject lessons on generic output mutations such as `first_color_only` without domain validation.

**Reason.** The 300-lesson census found 193 advisory lesson/rotation findings and 399 candidate occurrences, while every declared task-domain rival was refuted. A measured output mutation may fit by coincidence and need not correspond to a coherent ARC rule.

**Probe retained.** `checks/question/searched-rival-witness.json` records seed `1067786295`, easy lesson index 0, held-out query index 2, and the ambiguous generic candidate.

## D9 — Prior review lead

No prior return was used as the repair lead. The immutable baseline battery, current source, canonical examples, and this packet's direct Racket checks determined the changes; retained historical evidence was not used during either visible-only solve.
