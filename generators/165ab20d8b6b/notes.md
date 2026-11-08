# Current notes: `165ab20d8b6b`

## Intended rule and authority

For every nonzero 4-connected blob, erase its original cells and paint every **zero** cell touching the blob in one cardinal direction with the blob’s color. The selected canonical Racket rule remains authoritative. It was not edited; `RULE_HASH = "63879e6d755e"` pins the verified authority.

## Current generator

Version `3.0.0`; final reviewed SHA-256 `c5165b18f58600303789179fe83d96c0b3bc54004f88d6f4e771ed6ba004b58d`.

Lawful generated inputs have:

- background 0;
- dimensions 8..14 by 9..16;
- 1..4 distinctly colored, interior, 4-connected blobs;
- blob sizes 2..8 and colors sampled without replacement from 1..9;
- nonempty, pairwise-disjoint zero orthogonal shells, giving every output cell one owner.

Exact controls are `grid_h`, `grid_w`, `n_blobs`, and `scene_profile`. All legal values work in all difficulty bands. Unknown, mistyped, and out-of-range controls fail loudly. `observe_overrides` reconstructs every control from pixels.

## Reversed baseline decisions

Version 2.1.0 advertised nine axes, but palette/count/density/position controls were unused or aliases, difficulty silently narrowed integer domains, and degenerate textures returned grids that violated `self_check`. Those axes were removed rather than preserved as inert metadata. Rejection-based `grow_blob` placement was replaced by constructive backtracking with shell ownership.

The old validator limited blobs to size 2..4 and rejected a canonical size-5 object. The current structural validator accepts all four canonical inputs and ordinary lawful shapes up to size 8.

## Profiles and teaching schedule

- `canonical`: only ordinary 3..5-cell shapes, no enclosed hole.
- `broad`: contains a size-2 domino.
- `hole_witness`: contains a size-8 3x3 ring with an enclosed zero center.

Default profile order is `hole_witness, canonical, hole_witness, broad`; `EXAMPLES_NEEDED = 3`, followed by one query in the production lesson assembly. Thus every single held-out rotation retains at least one hole witness among the demonstrations.

The strongest recorded canonical shortcut is `external_shell_only`: paint only shell cells in exterior-connected background. It fits all four canonical examples but fails on the ring center. The exact authoritative counterexample is under `counterexamples/external_shell_only_case.json`, and the generator emits it via `scene_profile="hole_witness"` and twice per four profile positions.

## Verification state

- Before battery: 6 green, 1 advisory, 5 failed.
- After battery: 12/12 green.
- Focused/portable task tests: 65/65 passed.
- Lesson census: 300 lessons, 1,200 rotations, 1,193 unique inputs, zero ambiguity/errors against the declared rival.
- Canonical Racket source/data unchanged; rule smoke and authority synchronization pass.

## Known limits and open questions

- Disjoint shells are a deliberate generator-domain restriction; collisions and adjacent blobs are not taught.
- The finite census checks declared rivals and sampled starts, not every possible alternate rule.
- Difficulty currently changes ordinary shape texture only; all exact axis domains are shared across bands.
- Catalog approval/train-safety remains unchanged and unverified.
## Current reviewer considerations

Source SHA-256: `c5165b18f58600303789179fe83d96c0b3bc54004f88d6f4e771ed6ba004b58d`.

# Decisions: `165ab20d8b6b`

## D1 — Replace the nominal nine-axis surface with four honest controls (R1)

**Prior choice.** Version 2.1.0 declared `grid_h`, `grid_w`, `palette_kind`, `n_blobs`, `palette_size`, `position_bias`, `n_distinct_colors`, `density`, and `texture`. The rationale was not recorded. In the source, several were never consumed, `texture` was partly an alias and partly a route to invalid degenerate grids, and difficulty branches silently narrowed otherwise advertised integer ranges.

**New choice.** Advertise only `grid_h`, `grid_w`, `n_blobs`, and `scene_profile`. Each is recoverable from pixels by `observe_overrides`; all legal values work in every band; invalid/unknown controls are rejected.

**Alternatives rejected.** Implementing all old controls would add palette metadata with little task relevance and preserve overlapping aliases. Marking them diagnostic would leave a misleading public API. The full before/after override reports are the reusable probe.

**Limit.** Palette is still varied internally from colors 1..9, but it is intentionally not an exact public control.

## D2 — Use constructive packing and disjoint output shells (R4)

**Prior choice.** `grow_blob` plus bounded retries placed blobs but did not explicitly own shell-shell overlap. The recorded rationale was only “isolated interior blobs.”

**New choice.** Enumerate dihedral shape variants and backtrack over placements while forbidding blob/blob, blob/shell, and shell/shell intersections. This guarantees a unique owner for every painted cell and makes all documented extreme combinations constructive.

**Alternatives rejected.** More rejection attempts would remain probabilistic and make boundary overrides flaky. Allowing shell collisions would require a declared color-priority rule not evidenced by the canonical task.

**Failure modes and limits.** The sampler intentionally does not cover adjacent blobs or colliding shells. That is a documented domain boundary, not evidence that the Racket rule is undefined there.

## D3 — Preserve and recurrently emit canonical-scale support (R2)

**Prior choice.** Default dimensions were 9..12 by 10..13 with 2..3 blobs of size 2..4, while `self_check` rejected canonical size-5 components. No rationale for that mismatch was recorded.

**New choice.** Use dimensions 8..14 by 9..16 and 1..4 blobs, while scheduling the four canonical dimension profiles and ordinary 3..5-cell shapes regularly. `strict_canonical_like` delegates to the lawful structural contract, so all four canonical inputs are accepted.

**Alternatives rejected.** A canonical-only sampler would be too narrow; a broad-only sampler would fail the profile floor and lose direct support near the source examples.

**Probe.** `checks/after/checks/165ab20d8b6b_after_profile_floor.json` plus the canonical test in `tests/test_generator.py`.

## D4 — Add three structurally observable scene profiles (R1, R3)

- `canonical`: every blob has 3..5 cells and no enclosed zero hole.
- `broad`: contains a size-2 domino, separating it from canonical.
- `hole_witness`: contains a size-8 3x3 ring with an enclosed zero center.

The profiles are intentionally defined by visible structure, not hidden metadata. A profile can therefore be verified after generation. Broader random “texture” names were rejected because they were inert, overlapping, or invalid under the task contract.

## D5 — Teach against the strongest canonical shortcut on a deterministic schedule (R3)

**Observed rival.** “Paint only shell cells in exterior-connected background” fits all four canonical demonstrations because none has an enclosed zero region.

**New schedule.** The four profile positions are `hole_witness, canonical, hole_witness, broad`; lessons use three demonstrations and one query. Every holdout position therefore leaves at least one enclosed-hole witness in the demonstrations. The explicit case is in `counterexamples/external_shell_only_case.json`.

**Alternatives rejected.** Purely random witness sampling can starve small lessons. One witness per four examples fails when that example is the query. Two witnesses are the minimum simple schedule that survives every single holdout.

**Limit.** This guarantees refutation of the declared rival for the generated four-pair schedule. It is not a proof against undeclared hypotheses or arbitrary external lesson assembly.

## D6 — Keep Racket as authority; add a pure Python mirror only for review (R5)

The canonical Racket rule and canonical data were not edited. `RULE_HASH = "63879e6d755e"` pins the selected authority. `rule_mirror` is used by focused tests and semantic probes, while authoritative counterexample labels come from `arcpuzzles apply --reference canonical`.

An alternative of editing the Racket source was rejected because rule smoke and authority sync already matched all canonical pairs; the defects were in input distribution and contracts.

## D7 — Fail closed on malformed inputs and controls (R1, R2)

`self_check` now validates rectangular ARC grids, dimensions, component count, unique connected color ownership, component sizes, border clearance, cross-color contact, nonempty shells, and shell disjointness. Override validation rejects unknown keys, booleans masquerading as integers, wrong types, and out-of-domain values.

A permissive “best effort” API was rejected because it caused the baseline to report exact controls that were not exact and to return invalid degenerate examples.

## D8 — Use independent reconstruction in tests (R4, R5)

The task-local suite contains independent component/shell and exterior-background implementations rather than asserting only against generator helpers. It first failed on the baseline contract and then passed after the repair. The portable selected-task stage copied and executed the same final source and tests.

**Limit.** The independent Python rule and the Racket smoke tests cover the generated/canonical domain; they do not exhaust every possible ARC grid.

## D9 — Interpret the lesson census conservatively (R3, R5)

The 300-lesson, 1,200-rotation census is accepted as evidence that the production sampler refutes the named rival over the sampled starts and bands. Its 1,193 unique inputs are exact normalized hashes. It is not described as universal induction, and the report’s own limitations are retained.

No approval or train-safety status was changed from `unverified`.

## Native parametric admission — review-fddcc66c90d9a247

The task now has a source-bound native family under `workspace/parametric/`.
The default `neighborhood=cardinal` returns the exact canonical Racket bytes
(`63879e6d755ec49c6fcad80495bd4e114b52ce0b1cfb66a73ce25d8246df5d08`).
The alternate `neighborhood=moore` keeps same-color four-connected component
extraction, input-zero filtering, output blanking, and per-object color ownership
fixed, but derives each shell from all eight neighboring offsets instead of the
four cardinal offsets. The approved production generator remains byte-identical
at `c5165b18f58600303789179fe83d96c0b3bc54004f88d6f4e771ed6ba004b58d`.

The adapter accepts 2..6 demonstrations and 1..4 queries independently. Both
settings receive identical inputs, prefixes do not depend on requested totals,
and public projection exposes one query without hidden settings, Racket source,
answers, future inputs, or total-count hints. Four private queries are retained;
the last is a substantive 30x30 scene with six differently colored components,
more than 100 foreground cells, enclosed shell topology, and foreground contact
on every boundary.

Every scene includes an enclosed-hole ring and irregular components. The first
two demonstrations are constructively retried until both settings refute the
declared finite rivals: the opposite neighborhood, diagonal-only shells,
retaining source cells, exterior-only shells, bounding-box shells, fixed output
color, and color-blind component merging. The reusable `self_audit.py` checks
this finite teaching set over 64 seeds, minimum/maximum demonstration counts,
matched inputs, count prefixes, protected-Racket parity, 30x30 density and
boundary floors, and exact content-addressed public exports. These checks do not
claim universal program uniqueness or measured model improvement.

The sequential causal account is: Step A extracts each input-dependent colored
component and derives its zero-valued shell under the episode neighborhood;
Step B paints those derived shell coordinates with the component color on a
blank grid. The qualification witness replaces the correct cardinal-shell
intermediate with the eight-neighbor shell while keeping component records and
painting logic fixed, producing a different protected-Racket final grid.
