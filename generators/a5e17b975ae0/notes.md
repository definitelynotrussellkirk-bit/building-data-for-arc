# Working notes: a5e17b975ae0

## Review 2026-10-04

### Baseline finding

Version 2.0.1 generated only simple color-9 frames and omitted the canonical color-5 chamber partitions. Its public controls were not source-bound or observably honored, no rule hash or executable semantic contract was declared, no canonical profile was hit by the distribution gate, and `self_check` accepted destructive geometry/role mutations. The immutable before battery retained at `checks/before/` finished with 7 green, 2 advisory, and 3 failed stages.

### Repair

Version 3.0.0 was rebuilt around the actual canonical manifold:

1. Exactly two detached hollow 9-frames are drawn with an outer zero margin.
2. A true four-way 5-divider in the left frame guarantees multiple seedable and unseeded regions.
3. The right divider is one of three pixel-recoverable profiles: `cross_gap`, `dual_cross`, or `cross_tee`.
4. `single`, `separate`, and `partitioned` seed profiles place one or two distinct keys in separate open regions.
5. A five-slot deterministic schedule covers the five canonical size/palette profiles. `easy`, `medium`, and `hard` use offsets 0, 1, and 2 so the difficulty argument is live without creating a different rule family.
6. Every advertised override is validated, drawn through keyed provenance, and recoverable with `observe_overrides`; unknown axes and invalid values fail closed.
7. `self_check`/`strict_canonical_like` validate frame geometry, ownership of walls and seeds, region occupancy, margins, colors, and keyed/unkeyed teaching structure.
8. The unchanged Racket authority is pinned as `ced8e283e2c4`. The Python `rule_mirror` is only a local test/census mirror.
9. Executable rivals `identity` and `ignore_color5`, their witnesses, and `lesson_identifiable` make lesson ambiguity testable.

### TDD evidence

- Initial task contract: `87 failed, 10 passed` — `checks/task-tests-red/`.
- First coherent implementation: `97 passed` — `checks/task-tests-green-1/`.
- The full battery then exposed byte-identical difficulty bands. A new regression failed `5` cases before the fix — `checks/dead-bands-red/` — and passed after schedule rotation — `checks/dead-bands-green/`.
- Final portable task suite: `102 passed` — `checks/task-tests-final/`.
- Final battery: all 12 stages passed — `checks/after-final/`.

### Distribution and lesson checks

- Production census: 100 lessons per band, 300 lessons total, 1,200 query rotations, 1,200 unique materialized inputs, 0 ambiguous rotations, and 0 hook/scoring errors — `checks/lesson-census.json`.
- Exhaustive schedule-start probe: 25 seeds × 4 bands/default × 5 cyclic starts = 500 lesson windows and 2,000 query rotations; 0 ambiguities and 1,500 unique inputs — `checks/cyclic-lesson-probe.json`.
- The finite checks cover the declared identity and ignore-5 rivals. They do not prove uniqueness against every imaginable rule.

### Rejected alternatives

- **Keep the v2 random-frame sampler and add occasional 5 walls:** rejected because it would leave canonical support probabilistic, controls unobservable, and malformed frame/chamber combinations difficult to validate.
- **Use difficulty-specific geometry ranges:** rejected because the first candidate made bands dead or created distribution shifts unrelated to the transformation. Band rotation keeps the same five profiles while making the argument observable.
- **Advertise more axes (frame count, arbitrary palettes, divider density):** rejected as unneeded and likely to create dead controls or leave the canonical domain.
- **Change the Racket rule to match the old sampler:** rejected; the canonical rule was already consistent across all examples and the defect was in input generation.

Imported associated notes remain in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `f6aa8282a799c77a75b3f696ac10a79e24ab406b6c1259fcad7defdd643188d4`.

# Decisions for a5e17b975ae0

## D1 — Keep the canonical Racket authority unchanged

**Decision.** Preserve the selected rule and pin `RULE_HASH = "ced8e283e2c4"` in the generator.

**Evidence and rationale.** The before battery's rule-smoke and authority-sync stages were already green, and canonical inspection showed a coherent rule: non-wall key colors flood their original 4-connected zero regions while colors 5 and 9 block traversal. The mismatch was that generator v2.0.1 did not emit the color-5 partition structure needed to teach that rule. Changing the rule to fit the weak sampler would invert the authority relationship and erase canonical behavior.

**Rejected alternative.** Modify the Racket program to flood simple unpartitioned frames. Rejected because all canonical examples contain meaningful 5-wall structure and the selected rule consistently handles it.

**Failure mode / limitation.** `rule_mirror` is test scaffolding, not authority. Future Python changes must continue to pass source-bound Racket smoke tests.

## D2 — Use exactly two detached color-9 frames

**Decision.** Emit two complete hollow 9-rectangles, horizontally detached by a zero gap and surrounded by an outer zero margin.

**Rationale.** This is the stable canonical object grammar and gives two independent containers for seed-placement contrasts. A strict rectangle parser makes missing walls, stray 9s, overlap, and touching frames observable rather than silently accepted.

**Rejected alternatives.** One-frame examples were rejected because they weaken support for `separate`; arbitrary 1–3 frame counts were rejected because no canonical evidence justified them and they would multiply layout/override edge cases.

**Probe.** Canonical examples and every generated draw pass `strict_canonical_like`; frame mutations are covered by `test_self_check_rejects_semantic_mutations`.

**Failure mode / limitation.** The generator deliberately does not explore vertically stacked frames. That is a distribution restriction, but it preserves the observed rule family and keeps all controls recoverable.

## D3 — Make color-5 partitions structurally unavoidable

**Decision.** Draw a full row-and-column divider in the left frame and one of three partition profiles in the right frame: `dual_cross`, `cross_gap`, or `cross_tee`.

**Rationale.** The old sampler omitted 5 entirely, making “5 is a blocker” unlearnable and causing zero canonical-profile hits. The left dual cross guarantees several real open components and at least one unseeded region for every seed profile. The right profile supplies geometric variation while remaining classifiable from pixels.

**Rejected alternatives.** Random sparse 5-cells were rejected because they often do not partition anything. Arbitrary maze generation was rejected because it adds geometry far outside the canonical examples and makes exact-profile support unreliable.

**Probe.** `five_wall_partition` must distinguish the official mirror from `ignore_color5`; the semantic gate, final task suite, production lesson census, and cyclic probe all exercise it.

**Failure mode / limitation.** The three divider templates are a finite grammar, not the set of all lawful walls. This is intentional YAGNI; future expansion should add a recoverable named profile and a witness, not an untracked random density knob.

## D4 — Limit seed controls to three semantic profiles

**Decision.** Expose `single`, `separate`, and `partitioned`.

- `single`: one key in a left-frame region.
- `separate`: one key in each frame.
- `partitioned`: two distinct keys in two different left-frame regions.

Every draw retains at least one unkeyed region.

**Rationale.** These profiles vary the number and container relationship of keys without introducing overlapping floods or ambiguous tie-breaking. They directly exercise key-specific flooding and unchanged unkeyed chambers.

**Rejected alternatives.** Multiple keys in one open component were rejected because the selected rule's row-major sequential behavior would introduce avoidable competition. Arbitrary key counts/palettes were rejected because canonical inputs use only one or two keys and extra controls would be weakly evidenced.

**Probe.** `observe_overrides` reconstructs the profile from key count and frame ownership; the full cross-product of four exact axes is tested.

**Failure mode / limitation.** This generator does not teach same-component competition. That behavior is deliberately outside the repaired domain rather than left accidental.

## D5 — Use a five-slot canonical-profile schedule

**Decision.** Schedule these profiles exactly once per five consecutive ordinary draws:

1. `13×20`, palette size 5, separate/cross-gap
2. `12×18`, palette size 5, partitioned/dual-cross
3. `14×19`, palette size 4, single/cross-tee
4. `12×17`, palette size 5, separate/dual-cross
5. `13×19`, palette size 5, partitioned/cross-gap

**Rationale.** The baseline missed every canonical size/palette profile in the profile-floor check. A short deterministic schedule guarantees support instead of hoping random draws hit five sparse combinations.

**Rejected alternatives.** Independent random height/width/profile draws were rejected because 20-draw floor checks could miss profiles and complete lessons could accidentally omit a critical seed/wall contrast.

**Probe.** Final profile floor is green; task tests inspect every schedule slot; `cyclic_lesson_probe.py` enumerates every schedule start. The production census materialized 1,200 unique inputs.

**Failure mode / limitation.** Schedule periodicity is itself a learnable artifact if sample index leaks downstream. The generated layouts and key positions remain RNG-varied, and downstream examples should not expose sample indices.

## D6 — Rotate difficulty bands instead of defining different manifolds

**Decision.** Use schedule offsets 0 (`easy`), 1 (`medium`), and 2 (`hard`).

**Rationale.** The first repaired candidate passed 97 tests but emitted byte-identical streams for easy/medium/hard; `defect_lint` correctly identified a dead knob. Rotation makes difficulty observable while preserving equal coverage and avoiding unsupported claims that one geometry is intrinsically harder.

**Rejected alternatives.** Distinct size ranges per band were rejected because they would confound task difficulty with shape and could violate exact overrides. Ignoring difficulty was rejected after the failing regression.

**Probe.** `test_difficulty_bands_rotate_the_schedule_without_leaving_the_manifold` failed 5 cases before the fix and passes in the final 102-test suite. Final defect lint is green.

**Failure mode / limitation.** The labels are curriculum positions, not calibrated model difficulty. Reports should not interpret them as empirical hardness.

## D7 — Advertise only four exact, pixel-recoverable axes

**Decision.** Keep `grid_h`, `grid_w`, `seed_profile`, and `wall_profile`; reject unknown keys and invalid values before generation. Route every accepted override through keyed draw provenance and expose `observe_overrides`.

**Rationale.** The before override gate found false/dead controls. Exact controls are trustworthy only when the returned grid proves what was realized.

**Rejected alternatives.** Keep legacy aliases or diagnostic axes. Rejected because they add combinatorial surface without changing pixels and recreate the failure seen in audit target `ca5dcbac0e83`.

**Probe.** Task tests exhaust the legal cross-product and invalid values; final override stage is green.

**Failure mode / limitation.** There are no declared incompatible combinations. If future profiles introduce incompatibilities, they must be explicit and falsifiable rather than silently clamped.

## D8 — Strengthen validation around semantic roles, not just counts

**Decision.** Validate rectangle completeness, margins, frame detachment, ownership of every 5/key cell, allowed colors, key uniqueness, one key per region, and presence of both keyed and unkeyed regions.

**Rationale.** Baseline `self_check` accepted destructive mutations because it checked only shallow counts. Training corruption often remains visually plausible, so role/geometry validation is necessary.

**Rejected alternative.** Rely on generation code never to make mistakes. Rejected because validators also guard future edits, overrides, and materialized data.

**Probe.** The mutation regression rejects stray walls/keys/colors and broken frames. Final self-check, strict-profile, and defect-lint stages are green.

**Failure mode / limitation.** The validator enforces the repaired generator domain, not every theoretically lawful instance of the Racket rule. This is intentional and documented.

## D9 — Declare two plausible wrong rules and test lessons, not only pairs

**Decision.** Declare `identity` and `ignore_color5` as executable rivals, with `fillable_region` and `five_wall_partition` witnesses. Use `lesson_identifiable` to flag a rival that fits all demonstrations but changes the query.

**Rationale.** Pair-level correctness does not ensure that a lesson teaches the intended rule. The two rivals correspond to the baseline's strongest shortcuts: do nothing, or flood through the omitted 5 walls.

**Rejected alternatives.** A long hand-written rival-name list with no executable functions was rejected because it cannot produce counterexamples. Claiming universal identifiability was rejected because finite rivals cannot establish it.

**Probe.** The final production census covered 100 lessons per band and every query rotation: 300 lessons / 1,200 rotations, 0 ambiguity. The exhaustive cyclic-start probe covered 500 windows / 2,000 rotations, 0 ambiguity.

**Failure mode / limitation.** Undeclared rivals remain possible. Results are explicitly scoped to the declared competitors and emitted domain.

## D10 — Keep reusable probes in the task workspace

**Decision.** Retain `reference_probe.py` and `cyclic_lesson_probe.py` beside the generator.

**Rationale.** Future reviewers need a source-bound way to reconstruct canonical profiles and exhaust short-period lesson schedules without reverse-engineering this review. Both tools hash/import the exact source they inspect and state authority limits.

**Rejected alternative.** Leave only prose. Rejected because the user requested built tools and future agents benefit from executable evidence.

**Failure mode / limitation.** Direct imports require the packet runtime environment. A shared launcher is proposed as feedback F3.

## D11 — Promote chamber-key selection as the native rule parameter

**Choice.** Add episode-fixed `fill_color_policy` with canonical `local_keys` and alternate `largest_chamber_key`. The canonical program is retained byte-for-byte. The alternate measures all keyed 4-connected chambers, selects the uniquely largest chamber, and uses that chamber's key color to flood every keyed chamber.

**Rationale.** This preserves the source task's frame/wall/chamber reasoning while adding a real input-dependent selector. It is not a cosmetic palette swap: the downstream flood color is unavailable until the chamber census and largest-chamber selection finish.

**Teaching evidence.** Deterministic matched inputs support 2–6 demonstrations and four prefix-stable queries. A 16-seed finite audit covered 96 lessons at 2/3/6 demonstrations against ten executable policies; no harmful rival survived. Protected-Racket qualification passed at 2, 3, and 6 demonstrations (32/40/64 evaluations).

**Causal evidence.** On the qualified 30x30 alternate query, the largest chamber has size 133 and key color 3. Substituting the smallest chamber (size 12, key color 8) changes 166 final cells; see `checks/a5e17b975ae0/causal-min/`.

**Limit / next action.** This is reviewer-ready finite evidence, not owner acceptance or universal identifiability. Integrate these exact bytes, rerun native qualification and the protected witness, then decide acceptance separately from training admission.
