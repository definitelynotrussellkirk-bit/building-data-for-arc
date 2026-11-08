# Working notes: 8384d9743be8

## Current rule and authority

Two fixed coordinate-aligned 5×5 color-1 masks occupy columns 0–4 and 6–10 of a 5×11 grid. The unchanged selected Racket authority emits a 5×17 gallery: union in color 2, intersection in color 3, XOR in color 4. The source is pinned by `RULE_HASH = 859078164faa`.

## Current generator design

- Version `3.0.0`; exact axes are only `density_l` and `density_r` (`3..9`).
- Default draws cycle over the five public occupancy signatures `(00,10,01,11)`: four complete truth tables plus the public right-subset-of-left query branch.
- `EXAMPLES_NEEDED = 4`; every five-pair cyclic window remains identifiable against the declared rivals under any query holdout.
- Masks are exact-size and 4-connected. Normal construction grows from a shared core; a deterministic transformed spiral interval is the total fallback.
- Difficulty alters shape RNG only, preserving each profile's semantic signature.
- `strict_canonical_like`, `rule_mirror`, witnesses, rivals, and `lesson_identifiable` are executable and covered by task-local tests.

## Reversed decisions

The previous version advertised six dead/singleton scaffold axes plus negative fixtures in the valid `texture` domain. Those controls were removed rather than emulated. An intermediate `LESSON_SCHEDULE_PERIOD = 5` declaration was also removed after the strict semantic gate warned that the stronger period claim had not been exhaustively enumerated; the five-profile schedule itself remains public through `schedule_profile`/`SCHEDULE_PROFILES`.

## Evidence and limits

Final generator SHA-256: `708a326dfd7a1f73479079928b1bcf4ad3e9032441a607fd2990bae9beacd08b`. Final battery: 12/12 green. Final task suite: 11/11. Large census: 300 lessons, 1,500 rotations, zero measured ambiguities/errors, 1,483 unique inputs.

The rule remains fixed-geometry/fixed-color. Exact count overrides may replace an incompatible scheduled subset relation with a lawful partial relation; relation is not an advertised axis. Finite rivals are evidence, not a proof of universal identifiability. Retained shortcut witness: `counterexamples/directional-xor-shortcuts.json`.
## Current reviewer considerations

Source SHA-256: `708a326dfd7a1f73479079928b1bcf4ad3e9032441a607fd2990bae9beacd08b`.

# Decisions for `8384d9743be8`

## D1 — Preserve the selected rule and fixed geometry

**Prior state:** two fixed 5×5 color-1 panels in a 5×11 input; the Racket rule emits union/intersection/XOR in a fixed 5×17 gallery.

**Decision:** keep the Racket authority unchanged and pin its hash (`859078164faa`). Keep the blank separator and literal output colors.

**Reason:** all five canonical examples use those fixed roles, and the selected program reads them literally. Generalizing palette, dimensions, or panel positions would require changing the task rather than repairing its input distribution.

**Rejected alternative:** vary colors, dimensions, or separator position. This was rejected because it would be outside the selected authority and could create correctly shaped but mislabeled training pairs.

**Evidence:** final rule smoke, grammar, Racket lint, and authority sync are green in `checks/after/`.

## D2 — Remove scaffold controls instead of pretending to implement them

**Prior state:** eight advertised axes, most ignored or singleton; negative fixtures appeared in the ordinary `texture` domain.

**Decision:** expose only exact left/right foreground counts, `density_l` and `density_r`, each `3..9`.

**Reason:** count is directly observable from pixels and useful for targeted generation. Palette, position, and texture are fixed by the authority or had no implementation.

**Rejected alternative:** preserve old names for compatibility and silently map them to no-ops. That would keep dead controls in downstream sweep metadata and permit invalid “valid” values.

**Failure modes considered:** incompatible joint counts, scalar coercion, unknown keys. Every pair in `3..9 × 3..9` is constructible; invalid types/ranges and unknown keys now reject.

## D3 — Match public occupancy signatures, not just marginal panel sizes

**Prior state:** random connected masks with nonempty intersection/XOR, but no explicit curriculum relation.

**Decision:** use five scheduled occupancy signatures copied from the four public demonstrations and one public query.

**Reason:** this keeps the generator on the measured canonical manifold while giving a deterministic semantic curriculum. Four profiles display all truth-table branches; the subset profile preserves a lawful canonical edge case.

**Rejected alternatives:**

- independent Bernoulli masks: high object fragmentation and known distribution drift;
- only partial-overlap examples: teaches the truth table but drops the public subset branch;
- only subset examples: lets a directional-difference shortcut masquerade as XOR;
- arbitrary relation randomization: gives no lesson-level coverage guarantee.

**Probe:** `test_default_five_slot_schedule_reproduces_every_canonical_occupancy_signature` and the 300-lesson census.

## D4 — Four demonstrations plus one query

**Decision:** set `EXAMPLES_NEEDED = 4` and retain five consecutive profiles per materialized lesson.

**Reason:** this mirrors the public 4-train/1-test structure. In any hold-one-out rotation, four remaining demonstrations include at least three full truth tables, refuting every declared competitor.

**Rejected alternative:** three demonstrations. It could work for the present rivals, but would no longer mirror the public lesson structure and would remove one full-profile redundancy under arbitrary query rotation.

**Limit:** downstream assemblers that do not use consecutive indices are outside this evidence. The public census uses the production sampler and reports accepted indices.

## D5 — Do not overclaim an enumerated schedule period

**Intermediate choice:** declare `LESSON_SCHEDULE_PERIOD = 5`.

**Reversal:** remove that declaration while retaining `schedule_profile` and `SCHEDULE_PROFILES`.

**Reason:** the strict semantic gate correctly warned that the period claim had not been exhaustively enumerated by that run. The ordinary census and task-local cyclic tests support the observed five-slot behavior, but a public period declaration carries a stronger fixed-seed enumeration expectation.

**Evidence:** failed intermediate receipt `checks/after-semantic_gate/`; corrected final semantic pass in `checks/after/`.

## D6 — Exact connected construction with a deterministic fallback

**Decision:** grow a connected intersection/core and two connected masks using keyed RNG; forbid left-exclusive cells while growing the right mask so overlap remains exact. Use a transformed spiral path only as a guaranteed fallback.

**Reason:** random rejection alone can make edge overrides flaky. The constructive path supports every legal count pair while normal draws remain compact and varied.

**Rejected alternative:** pre-enumerate all connected subsets of a 5×5 grid. It would add complexity and module-load cost without improving this small domain.

**Probe:** boundary overrides `(3,3)`, `(9,9)`, `(3,9)`, `(9,3)` round-trip and pass `self_check`.

## D7 — Difficulty changes morphology, not semantics

**Intermediate defect:** easy/medium/hard were byte-identical for the same seed/index, causing defect lint to report dead bands.

**Decision:** include the difficulty label in the keyed shape RNG while keeping the scheduled counts and occupancy signature unchanged.

**Reason:** difficulty may vary concrete morphology without changing the rule branch taught by a profile.

**Probe:** task test confirms at least two band-specific shapes per profile and one shared occupancy signature.

## D8 — Explicit semantic rivals

**Decision:** declare panel-order, copy-mask, and directional-XOR competitors; verify two witnesses against them; reject lessons where a competitor survives every demonstration.

**Reason:** correct per-grid labels are insufficient for training value. The most plausible accidental shortcut here is treating XOR as one directional set difference, especially on the subset query.

**Counterexample:** `repo/generators/8384d9743be8/counterexamples/directional-xor-shortcuts.json` contains both one-sided states and exact correct/rival outputs.

**Limit:** the rival list is finite and task-specific. It does not establish uniqueness against arbitrary programs.

## D9 — Strict literal validation

**Decision:** reject nonliteral ARC cells, non-integer/negative sample indices, invalid difficulty labels, unknown overrides, and nonliteral/out-of-range counts.

**Reason:** Boolean values are Python integers and legacy `draw_int` coerces floats/strings, so relying on implicit typing lets malformed sweep requests silently enter the dataset.

**Rejected alternative:** coerce inputs for convenience. Training generation should fail loudly rather than make provenance ambiguous.
