# Working notes: bb432515d2e6

Review `review-4b79da4b3c98ad9a` replaced the imported generic-axis sampler with a source-bound blocked-geodesic curriculum. The retained implementation deliberately guarantees one finite-tie example, one wall-detour example, and one seedless-component example in every three consecutive defaults. It also adds exact pixel-observable overrides, destructive grammar validation, a Python oracle, three plausible rival rules, lesson identifiability, focused regression tests, and `workspace/lesson_probe.py`.

The Racket algorithm and canonical rule hash were not changed. The selected authority record's `target_code` was synchronized byte-for-byte to its existing `raw_code` by deleting two non-semantic injected comments. See the packet-root `REVIEW.md`, `DECISIONS.md`, and `checks/` evidence in the returned review package for measurements and limitations.
## Current reviewer considerations

Source SHA-256: `bce22c67c8568ad56994f276fe911d57c141046e823c6042638abf19b5de136e`.

# Decisions for bb432515d2e6

## D1 — Preserve the canonical blocked-geodesic rule

**Decision.** Keep the canonical rule unchanged: color 5 is impassable; every other nonzero cell is a seed; each zero cell takes the uniquely nearest finite seed under four-neighbor shortest-path distance; finite ties and unreachable cells remain zero.

**Original rationale.** The imported source described BFS Voronoi propagation and its live Racket authority already matched all five canonical pairs. The baseline live rule-smoke stage passed even while generator-contract gates failed, so the defect was in data generation and declaration rather than the selected transformation.

**Alternatives rejected.** I did not simplify the rule to Manhattan distance, force assignment on ties, or globally fill disconnected chambers. Those are retained as executable rivals because each is plausible from incomplete demonstrations and each changes canonical or generated answers.

**Probe and failure mode.** A separately written Python BFS oracle checks all canonical pairs and generated cases. Live Racket rule smoke and authority sync remain mandatory because a Python mirror alone could faithfully test the wrong rule.

## D2 — Replace eight generic axes with four exact observable controls

**Decision.** Advertise only `grid_h=10..12`, `grid_w=11..14`, `n_seeds=2..3`, and `profile ∈ {open_tie, wall_detour, seedless_chamber}`. Every Cartesian combination is constructive in every difficulty band, and `observe_overrides` recovers the requested values from pixels.

**Why.** The baseline's palette kind, palette size, position bias, color count, density, and texture declarations were largely aliases, singleton metadata, ignored controls, or degenerate fixtures. The exact matrix also conflicted with narrower difficulty-specific draw ranges. Training metadata that cannot be observed or honored is worse than a smaller truthful contract.

**Alternatives rejected.** I rejected retaining a generic axis merely as `probe: diagnostic`; that would preserve dead public surface area without increasing data value. I also rejected a broad random-maze axis because it would reintroduce rejection sampling and make exact topology observation difficult before semantic coverage was secured.

**Probe and failure mode.** The override stage and focused tests exercise minimum/maximum values and every profile in `None`, easy, medium, and hard. Unknown keys, booleans masquerading as integers, out-of-range integers, and invalid profiles are rejected. The deliberate cost is narrower structural variety, documented under D8.

## D3 — Use a deterministic three-profile lesson schedule

**Decision.** `sample_index % 3` selects `open_tie`, `wall_detour`, then `seedless_chamber`; `EXAMPLES_NEEDED = 3`. Thus every three consecutive default demonstrations contain all three semantic branches regardless of start offset.

**Why.** Individual witness frequency does not prove that a complete lesson disambiguates the rule. A deterministic cycle gives an exact, cheap guarantee and makes exhaustive cyclic-start testing possible.

**Alternatives rejected.** Independent random profile draws could omit a branch from a three-example lesson. Weighted random draws would improve average frequency but still leave bad windows. Enlarging the lesson count would consume training context instead of fixing sampler policy.

**Probe and failure mode.** The source-bound lesson census checked 100 cyclic starts per difficulty, 300 complete lessons, and observed zero failures or rival survivors. The schedule is predictable; surface diversity therefore comes from dimensions, colors, seed count, and symmetries rather than profile order.

## D4 — Construct profiles that isolate three named semantic errors

**Open tie.** Two top-row seeds are placed at even horizontal separation, creating a finite equal-distance locus. A third seed, when requested, is placed on the opposite row so it cannot erase the intended witness.

**Wall detour.** A color-5 barrier is attached to one frame edge and leaves one gap at the other. Shortest paths must route around the gap, yielding cells where BFS and component-local Manhattan choose differently.

**Seedless chamber.** A complete frame-to-frame separator creates an interior component with no seed. Its zeros must remain zero.

**Alternatives rejected.** Arbitrary partial walls were not retained as the primary teaching source because many random layouts do not actually reverse a nearest-seed decision. The baseline's connectivity requirement explicitly excluded seedless chambers, hiding selected-rule behavior on unreachable cells.

**Probe and failure mode.** Each profile has a named witness and associated rival. Focused tests force every profile at both seed counts and all boundary sizes. The profile observer distinguishes no interior wall, incomplete separator, and complete separator from pixels.

## D5 — Make difficulty live without changing legal override domains

**Decision.** Difficulty offsets a deterministic reflection choice: easy shares the base orientation, medium and hard rotate through the four reflection states. Size, seed count, and profile overrides remain legal and exact in all bands.

**Why.** An intermediate implementation allowed all controls but emitted byte-identical results across bands. The new mapping makes the public knob behaviorally live without silently narrowing exact domains.

**Alternatives rejected.** Difficulty-specific size ranges were rejected because they make advertised exact values invalid in some bands. Adding harder semantic rules was rejected because difficulty should not change the target transformation.

**Probe and failure mode.** A red regression first demonstrated identical outputs; the final test checks multiple seeds and requires at least two distinct band outputs. Reflections do not make hard intrinsically more complex, so this knob supplies controlled presentation variation rather than a calibrated cognitive ranking.

## D6 — Strengthen validation from acceptance-only to grammar-specific

**Decision.** `self_check` now verifies rectangular shape, ARC integer colors, 10–12 × 11–14 dimensions, a complete rectangular color-5 perimeter with a zero margin, zero exterior, exactly two or three distinct singleton seeds strictly inside, and at least one interior zero.

**Why.** The baseline accepted blank grids, no-wall layouts, minimal impostors, malformed values, and most destructive mutations. Such acceptance makes a green generation sweep non-probative.

**Alternatives rejected.** I did not validate only metadata returned by the generator; the checker must infer lawfulness from pixels so it can catch construction drift and canonical inputs. I also did not require all non-wall interior cells to be connected, because disconnected seedless components are selected-rule evidence.

**Probe and failure mode.** Canonical inputs are all accepted, while malformed/ragged/out-of-domain grids and structure-destroying mutations are rejected. The validator intentionally accepts any grid satisfying the documented rectangular-frame grammar, not only the three exact constructors.

## D7 — Declare rivals at the right semantic scope

**Decision.** Keep `break_ties_low_color`, `component_manhattan`, and `fill_seedless_chambers` in `LESSON_COMPETITORS`; map them to witnesses; leave `CANONICAL_SHORTCUTS` empty.

**Why.** The rivals are useful generated-lesson competitors, but the new source-bound probe showed that each disagrees with one or more of the five canonical pairs. Calling them canonical shortcuts was factually false.

**Alternatives rejected.** I did not delete the rivals after the metadata failure; that would lose valuable lesson checks. I did not weaken the probe to ignore mismatches. The failing intermediate run is retained in `checks/tdd_probe_green.log`.

**Probe and failure mode.** The retained probe imports declarations directly, evaluates every declared canonical shortcut against every usable canonical pair, and fails on any mismatch. This found a gap in the shared semantic gate described as F1 in `FEEDBACK_TO_CODEX.md`.

## D8 — Accept a controlled manifold, document its limits

**Decision.** Use one outer rectangular frame, two or three globally distinct singleton seeds, three wall topologies, dimensions close to canonical examples, eight possible seed colors, and four reflections.

**Why.** The immediate goal is high-value, falsifiable training data. These constraints give exact semantic coverage, robust validation, and complete override support rather than broad but unreliable random layouts.

**Limitations.** The generator does not yet cover arbitrary labyrinths, multiple seeds of the same color, more than three seeds, irregular outer boundaries, diagonal movement, or multiple independent detours. A model could exploit profile geometry. Expanding topology should be a later version with new observers, rivals, and lesson-census evidence—not an untested widening of this patch.

**Small witness.** In the final census, each profile occurred exactly 300 times across 900 overlapping demo slots; dimensions/colors/reflections yielded 300 unique demo inputs and 294 unique queries. All three rivals survived zero complete lessons.

## D9 — Synchronize authority text without changing authority semantics

**Decision.** In `H128__bb432515d2e6.json`, copy the existing `raw_code` text into `target_code`, deleting only the comments “Mutable lookup table for visited” and “Top edge of the distances bbox.”

**Why.** The comments created source-divergence findings and the second was misleading. The executable forms were otherwise identical.

**Alternatives rejected.** I did not edit the canonical JSONL rule or the Racket algorithm. The final rule hash remains `823ef34eb751`.

**Probe and failure mode.** Live Racket smoke, Racket lint, and authority synchronization all pass. The final solve is bound to the generator hash after this synchronization.

## D10 — Retain a reusable source-bound lesson tool

**Decision.** Add `workspace/lesson_probe.py`, not a one-off notebook or copied rival list.

**Why.** Future edits can accidentally change declarations, canonical ambiguity, or lesson assembly. Importing the selected source prevents the probe from silently testing stale names.

**Alternatives rejected.** A frequency-only report was rejected because overlapping witness counts do not establish per-lesson identifiability. A random sample alone was rejected because the three-state schedule makes all cyclic starts cheap to enumerate over a substantial deterministic range.

**Probe and failure mode.** The tool emits source/rule hashes, sampler policy, denominators, unique-input counts, failures, rival survivor counts, witness counts, and canonical-shortcut mismatches. It exits nonzero on any lesson failure, surviving competitor, or false shortcut declaration.
