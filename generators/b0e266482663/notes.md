# Working notes: b0e266482663

## Review objective

Improve the generator as training data, not merely make generic lint green. The central question is whether a three-example lesson forces the learner to infer bidirectional ray stopping and cyan intersections rather than exploit morphology, marker position, inert blockers, or a measurement shortcut.

## Baseline findings: version 3.1.1

Version 3.1.1 guaranteed red-only, green-only, and crossing cells, but blockers were random interior scatter. Re-measuring the fixed 500-draw census with the corrected version-2 probe shows both **visible** stop directions in only 31 easy, 278 medium, and 388 hard draws. Shooters never appeared at row/column 1, so adjacent origins and first-step blockers were absent by construction. Independent broad dimensions also drifted away from the three source shape pairs.

The exact before battery failed:

- lint: missing `RULE_HASH`;
- defect lint: dead/overlapping texture declarations and an undeclared degenerate;
- override: 23,933 findings, 147,570 legacy-accepted multi-axis rejections, and unknown-key swallowing.

The baseline was still diverse—500 unique inputs in each sampled band—and all color branches were visible. This was useful negative evidence: uniqueness and output-color coverage were not sufficient data-value metrics.

## Round-one hypotheses and experiments

### H1: Construct active blockers instead of sampling until lucky

Implemented one guaranteed live horizontal blocker and one live vertical blocker, protecting each ray prefix. This made both directions mathematically active in every sampled draw.

### H2: Preserve source morphology by planning a shape pair

The first candidate independently weighted source heights and widths. That generated nine combinations from three marginals, only three canonical. A fixed-seed test got 43 canonical hits against a 45-hit floor. The final plan samples whole pairs, weighting each canonical pair four times against controlled generalization pairs.

### H3: Teach adjacency and off-by-one behavior through a schedule

The first curriculum used four profiles: adjacent origins, first-step stops, separated stops, and late stops. With only three demonstrations, some contiguous windows omitted one special witness. The semantic gate reproduced this exactly. The final schedule combines adjacent origins and first-step stops into one profile, making every three-example default window complete.

### H4: Make overrides a falsifiable contract

Removed inert palette/texture controls and degenerate aliases. Kept five axes whose values can be recovered from the grid. Every axis uses one public domain in every band, unknown keys fail immediately, and generation compares requested/drawn values to `observe_overrides()`.

### H5: Evaluate the lesson, not only each grid

Added a Python authority mirror, structural witnesses, and rivals for ignoring blockers, choosing one crossing color, emitting only one ray direction, and stopping one cell early. `lesson_identifiable()` verifies the actual demonstration set and therefore catches schedule/filtering mistakes that grid-local checks cannot.

## Round-two adversarial findings against version 4.0.0

The first repair passed its focused tests and all generic stages, but a second independent probe found that “active blocker” was still too weak a concept.

### F1: a stop could be mathematically active but visually unteachable

`_ray_analysis()` and `distribution_probe.py` called the first blocker on a live ray active whenever it was not on the final interior cell. Extra blockers were allowed to occupy every later cell. In that case no unchanged background remains beyond the blocker, so the input/output pair does not reveal that the ray stopped there. Reproduced default examples included:

- easy seed/sample `7_000_025 / 25`;
- medium `7_000_010 / 10`;
- hard `7_000_008 / 8`.

Dense legal 6×6 overrides with ten blockers also reproduced one or both masked directions. The generator's `self_check()` and its measurement probe shared the same false premise, so they agreed with each other while both were wrong.

### F2: the adjacent profile required blockers it did not actually need

The two universal semantic anchors are themselves the horizontal and vertical first-step blockers when the crossing coordinate is 1. The code nevertheless required `n_blockers >= 4` before it required the second row and column shooters. With `n_row_shoot=2`, `n_col_shoot=2`, and the legal exact override `n_blockers=2`, seed/sample `0 / 0` failed to guarantee the horizontal first-step witness.

### F3: the one-cell-early rival erased perpendicular evidence

The rival was implemented by running the true rule and replacing the cells immediately before blockers with zero. If such a cell was also reached by the perpendicular ray, zero was not the rival's correct result; it should retain the perpendicular color. This made the rival easier to falsify for the wrong reason.

## Version 4.1.0 repair

- Reserve one zero-valued suffix witness immediately beyond each universal semantic blocker and exclude it from extra blocker placement.
- Define an observable stop as the first blocker on a live ray **plus at least one later non-blocker cell**.
- Apply the same definition in the generator, `self_check()`, semantic witnesses, first-step witnesses, and `distribution_probe.py`.
- Enable the adjacent/first-step fixture whenever both shooter counts are at least two; the blocker count no longer controls it because the two anchors are sufficient.
- Keep the ordinary difficulty-specific blocker distribution for the adjacent profile rather than correlating that lesson slot with four or more blockers.
- Recompute the one-cell-early rival from ray reachability with a one-cell lookahead, preserving any perpendicular ray.
- Bump the generator to `4.1.0` and the probe schema to `b0e266482663-distribution-probe-v2`.

## TDD and adversarial evidence

The round-two regressions were written first and failed four ways: the masked grid passed `self_check()`, a known generated counterexample had no visible horizontal suffix, the two-blocker adjacent override omitted one first-step witness, and the rival erased a perpendicular ray. The probe-specific test separately failed because it repeated the masked-stop classification. The repaired focused suite passes 11/11.

A deterministic sweep then checked 60,000 default draws plus the complete declared axis cross-product once for each of the three schedule profiles: 91,104 generations total. It found no exception, realized-axis mismatch, self-check failure, or missing visible stop direction (`workspace/visibility_override_sweep.json`).

## Final measured state

With 500 draws per band and the corrected probe:

- both visible stop directions: 500/500 in easy, medium, and hard;
- all output branches: 500/500 in every band;
- canonical shapes: 364 easy, 370 medium, 370 hard;
- adjacent shooters on both edges: measured in `workspace/distribution_after.json`;
- first-step stops on both axes: 167 easy, 187 medium, 195 hard;
- unique inputs: 494/500 easy, 500/500 medium and hard;
- tested three-example lesson windows: 12/12 per band.

All twelve repository stages passed in a fresh individual replay on generator SHA-256 `8fbad8c57bf158d7dc0e83cf93a934cff70d0b5bf5ecc77c965c06f27e57ae77`. The focused generator suite passes 11/11. The round-two fresh solve passes all three visible demonstrations; masked labels remain withheld. No Racket or canonical authority changed.

## Unresolved and intentional limits

- Easy generation can repeat a small number of highly constrained layouts (494/500 unique in this census).
- The default shape plan is intentionally source-weighted, not uniform over every legal height/width pair.
- Fixed overrides with only one shooter on an axis cannot simultaneously demonstrate a first-step stop on that axis and a cyan crossing in the same grid; exact axes remain valid grid controls, while the full three-profile curriculum guarantee applies to defaults.
- The declared rival set is targeted, not exhaustive.
- Downstream filtering or reordering should rerun `lesson_identifiable()` on the actual examples.
- Catalog approval and training admission remain maintainer decisions.

Imported associated notes, if any, remain in `evidence/associated_notes.jsonl`.

## Round-three adversarial findings against version 4.1.0

The second repair made every blocker stop visible, but the lesson still did not quantify its rule over all edge markers. Independent rivals were applied to complete three-example windows rather than individual grids.

### F4: productive-shooter evidence did not cover marker cardinality

Some windows were fully compatible with only the lowest shooter, then with only the first or last two shooters, and finally with only the first or last three shooters. The last shortcut was especially important: the public domain permits four markers, but the canonical examples contain exactly two per edge, so a fixed cap can fit the authority examples while being wrong on the declared distribution. Known red cases include `83_000_019/19`, `83_000_006/6`, and `113_000_000/0`.

The repair progressed constructively instead of adding random frequency. `separated_stops` now requires at least two productive shooters per axis. `late_stops` reaches exactly four productive row and column shooters, the public maximum, so every three-example default lesson falsifies all first/last caps below four.

### F5: crossing color could be tied to a privileged shooter pair

Even after multiple shooters were productive, some windows fit a rival that used cyan only when at least one ray came from the lowest row or column shooter. A known counterexample was `93_000_300/300`. The separated profile now reserves a crossing between nonlowest row and column shooters, so cyan is demonstrated as a relation between rays rather than a property of one privileged pair.

### F6: emission and blocker response could generalize to different subsets

Version 4.5.0 visibly emitted all four row and column rays, yet many windows remained compatible with “only the first/last two or three markers respect blockers; the omitted marker passes through.” This showed that presence of a mechanism and presence of an object do not prove the mechanism applies to that object.

The final late fixture visibly stops both the lowest and highest row shooters and both the lowest and highest column shooters. Its stopping row and column are not shooters, and it preserves horizontal-only, vertical-only, cyan, and post-blocker suffix witnesses. Exact low-count overrides still use the generic constructive layout, while default late lessons use the maximum-cardinality fixture.

## Version 4.6.0 semantic contract

The final lesson contract contains 16 witnesses and 24 rivals. In addition to the original blocker, branch, and off-by-one checks, it requires two-, three-, and four-shooter productivity; a nonlowest-by-nonlowest crossing; and visible extreme-shooter stopping. The matching rivals cap emission at the first or last one/two/three markers or restrict blocker response to first/last marker subsets.

`workspace/distribution_probe.py` is now schema `b0e266482663-distribution-probe-v6`. Its shortcut renderer is independent of the production rival functions. On the final source, all 18 independent shortcuts were refuted in all 12 sampled windows per band. Larger independent probes refuted every tested fixed-cardinality, crossing-color, global-wall, and blocker-scope family in `3000/3000` windows for each difficulty.

## Final round-three measured state

Generator SHA-256: `bd9bba5d02cec811f5e7a6f9b209281bfe604f47f224d9598e2bc050476e23ec`.

- focused generator tests: 20/20 passed;
- repository tests: 138 passed, 28 Racket-dependent tests skipped by that Python run;
- both visible stop directions and all output branches: 500/500 in every band;
- unique inputs: 484 easy, 492 medium, 500 hard;
- canonical shapes: 372 easy, 377 medium, 389 hard;
- four productive shooters on both axes: 167/172/188 easy/medium/hard;
- both extreme row shooters visibly stopped: 184/189/224;
- both extreme column shooters visibly stopped: 179/195/220;
- nonlowest-by-nonlowest crossing: 382/363/361;
- tested lesson windows: 12/12 per band;
- adversarial default/override sweep: 91,104/91,104 clean;
- source-bound repository stages: 12/12 passed.

The canonical/Racket authority was not changed. The lower easy and medium uniqueness is a conscious consequence of using a highly constrained four-marker/four-extreme-stop fixture in every late lesson. The rival set remains targeted rather than exhaustive, and masked solve labels remain unavailable to the reviewer.
## Current reviewer considerations

Source SHA-256: `bd9bba5d02cec811f5e7a6f9b209281bfe604f47f224d9598e2bc050476e23ec`.

# Decisions for `b0e266482663`

This file records the input-distribution choices, what the imported generator appeared to be optimizing, alternatives considered, the probes used, and known limits. “Original rationale” distinguishes explicit baseline comments from inference; undocumented intent is not presented as fact.

## 1. Preserve the transformation authority

**Original rationale.** The imported comments and canonical examples consistently described the same rule: red left-edge row shooters cast rightward, green top-edge column shooters cast downward, maroon blockers stop rays, and crossings become cyan. No contradictory canonical example was found.

**Decision.** Keep the canonical/Racket authority unchanged and pin the generator to `RULE_HASH = "d12310adc715"`. Add an input-pure Python mirror only as a checker and semantic-probe aid.

**Alternatives considered.** Editing the Racket rule was rejected because rule smoke against the real authority already fired correctly, and the defect was in lesson construction rather than transformation semantics.

**Probe/evidence.** Final rule smoke applied the rule 120 times and found 120/120 mirror-parity matches, zero mutations, and zero crashes. Racket lint and authority sync passed on final generator SHA-256 `8fbad8c57bf158d7dc0e83cf93a934cff70d0b5bf5ecc77c965c06f27e57ae77`.

**Failure modes/limits.** The Python mirror is secondary evidence, not authority. A shared misunderstanding could affect both generator tests and the mirror, which is why the real Racket smoke remains required.

## 2. Choose height and width as a coherent pair

**Original rationale.** Version 3.1.1 chose independent dimensions by difficulty. Its stated defaults emphasized broad size ranges, but no rationale was recorded for separating the marginals from the three observed source shapes `(7,8)`, `(8,9)`, and `(9,10)`.

**Decision.** Draw a shape pair from a weighted plan: the three canonical pairs appear four times each, plus one controlled generalization set per difficulty. Expose `grid_h` and `grid_w` as independent exact overrides after the default pair is planned.

**Alternatives considered.** Independently weighting canonical height and width marginals was implemented first and rejected. Three heights crossed with three widths make nine pairs, of which only three are source pairs; the fixed-seed test obtained only 43 canonical hits where the intended floor was 45. Uniformly using only source shapes was rejected because it would remove useful size generalization.

**Probe/evidence.** The corrected version-2 500-draw census retained canonical shapes in 364 easy, 370 medium, and 370 hard draws. The profile-floor gate passed on the final source.

**Failure modes/limits.** Defaults do not sample every legal `(height,width)` cross-product. The complete public domains are instead tested through exact overrides. The generalization shapes are design choices, not canonical evidence.

## 3. Shooter-count distributions

**Original rationale.** The baseline used 1–2 shooters per direction for easy, 2–4 for medium, and 3–6 for hard. Comments aimed to guarantee at least one shooter and all three output branches, but positions started at index 2, excluding adjacency to the top-left corner.

**Decision.** Keep the public count domain compact and source-compatible at 1–4. Bias easy toward 1–2, medium toward 2–3, and hard toward 3–4. On the `adjacent_first_step` schedule slot, bias both shooter counts to at least 2 so one ray can cross while another demonstrates an immediate stop. Allow explicit count overrides to take precedence.

**Alternatives considered.** Retaining counts up to 8 was rejected because the source has four of each marker and larger counts mostly increase density without adding a new rule distinction. Forcing the same count on every example was rejected as a positional/count shortcut.

**Probe/evidence.** Histograms in `checks/round2/distribution-after-v2.json` show all declared counts represented. In the final 500-draw census, both-edge adjacent shooters occurred 273/297/314 times for easy/medium/hard, compared with 0 in every baseline band.

**Failure modes/limits.** Difficulty is a density curriculum, not a formal complexity proof. A model could still correlate hard with more markers; mixed counts within each band reduce but do not eliminate that cue.

## 4. Construct blockers as causal anchors with visible suffixes

**Original rationale.** The baseline scattered blockers in rows and columns starting at coordinate 2 and protected one crossing path. That guaranteed color branches but not that any blocker intersected a live ray. The comment “blockers only in the interior so every shooter fills at least its first cell” deliberately excluded first-step stopping.

**Decision.** Construct one horizontal and one vertical blocker on live rays, protect each prefix, and reserve at least one post-blocker zero-valued cell on each ray. Extra blockers may not occupy those two suffix witnesses. An active stop therefore means: the ray reaches this first blocker and a later non-blocker cell remains unchanged to demonstrate stopping. The adjacent profile uses its two universal anchors as the first-step blockers whenever both shooter counts are at least two; it does not require four blockers.

**Alternatives considered.** Pure random scattering was rejected after the baseline census. Rejection sampling until both directions happened to be active was rejected because it wastes draws, obscures why a lesson is valid, and gives no control over first-step or late-stop witnesses. Version 4.0.0's weaker “first blocker before far edge” predicate was also rejected: extra blockers could fill every later cell, making the claimed stop observationally indistinguishable.

**Probe/evidence.** Under the corrected predicate, both blocker directions are visibly active in 500/500 draws in every band, versus 31/278/388 before. Both first-step stops occur in 167/187/195 easy/medium/hard draws. Deterministic 4.0.0 counterexamples include default seed/sample `7_000_025/25`, `7_000_010/10`, and `7_000_008/8`, plus dense exact overrides. `self_check()` now rejects those masked-stop layouts.

**Failure modes/limits.** Constructive anchors introduce recurring relational roles. Randomized coordinates, separated/late profiles, varied counts, and extra blockers reduce fixed-location shortcuts, but the curriculum is intentionally structured.

## 5. Three-example semantic schedule

**Original rationale.** No lesson-level schedule or identifiability contract existed in version 3.1.1. Individual grids were sampled independently.

**Decision.** Use exactly three rotating profiles because `EXAMPLES_NEEDED = 3`:

1. `adjacent_first_step`: adjacent origins and immediate visible stopping in both directions when counts permit;
2. `separated_stops`: ordinary interior stopping at varied positions;
3. `late_stops`: blockers near the far edge while preserving a post-blocker background witness.

Every three consecutive default examples contain all three profiles, regardless of starting offset.

**Alternatives considered.** The first implementation used four profiles—adjacent origins, first-step stops, separated stops, and late stops. It was rejected after the semantic gate showed that a three-example window starting at offset 1 omitted adjacent-origin evidence and another omitted first-step evidence. Increasing `EXAMPLES_NEEDED` to 4 was rejected because the packet's solve/training contract uses three examples. Requiring four blockers for the adjacent slot was later removed: its two universal anchors are already first-step blockers, so two legal blockers suffice.

**Probe/evidence.** The failed four-slot design is retained in `checks/after-semantic_gate`; the corrected design passed the semantic gate and all 36 tested three-example windows across three bands and twelve offsets in the version-2 census. The exact override `n_row_shoot=2,n_col_shoot=2,n_blockers=2` has a focused regression test.

**Failure modes/limits.** `schedule_profile()` is sample-index based, so callers that discard or reorder examples can break the intended lesson. The lesson hook checks the actual demos and should be invoked after downstream filtering. Exact one-shooter overrides cannot simultaneously expose a same-axis first-step stop and retain a crossing in one grid.

## 6. Exact override surface

**Original rationale.** The baseline advertised broad ranges, palette aliases, and degenerates. Difficulty-specific `draw_int` bounds contradicted the declared domains. `palette_kind` had no effect; `texture` overlapped palette and degenerate semantics; unknown keys were silently ignored.

**Decision.** Retain only five externally observable controls: `grid_h`, `grid_w`, `n_row_shoot`, `n_col_shoot`, and `n_blockers`. Give each one a single full domain valid in every difficulty. Reject every unknown key before creating the draw context. Verify realized values with `observe_overrides()` inside generation.

**Alternatives considered.** Declaring a large incompatibility matrix was rejected because the constructive layout supports the compact full domain directly. Preserving degenerate textures was rejected because training-facing defaults should not silently mix identity/no-blocker/all-blocked tasks, and the baseline linter found those declarations overlapping and dead.

**Probe/evidence.** The before override gate reported 23,933 findings and 147,570 undeclared multi-axis rejections. The final repository override stage passed. A separate 91,104-generation sweep covered 60,000 defaults plus the complete declared axis cross-product once per schedule profile, with no exception, exact-axis mismatch, self-check failure, or missing visible stop direction (`checks/round2/adversarial-visible-stop-probe.log`).

**Failure modes/limits.** The compact domains intentionally drop extreme dimensions/counts. They can be expanded later only with constructive capacity checks, source/profile evidence, and the same complete override sweep.

## 7. Self-check and lesson-level rivals

**Original rationale.** Baseline `self_check()` enforced markers and all three ray-output branches. That was useful but insufficient: a grid could show red, green, and cyan while every blocker was irrelevant.

**Decision.** Keep surface grammar checks, require visible stops in both directions, and declare semantic witnesses and rival transformations. A visible stop requires post-blocker background. The current rivals are: ignore blockers, horizontal wins crossings, vertical wins crossings, horizontal-only rays, vertical-only rays, and stop one cell before the blocker. The off-by-one rival is recomputed from horizontal/vertical reachability so it removes only the affected ray and preserves any perpendicular contribution. `lesson_identifiable()` checks all examples against the mirror, requires every witness somewhere in the demonstrations, and requires every rival to disagree on at least one demonstration.

**Alternatives considered.** A single scalar “difficulty” score was rejected because it cannot explain which rule ambiguity remains. Checking only output-color presence was rejected because the baseline already passed it. Mutating a correct output in place for the off-by-one rival was rejected after it erased a legitimate perpendicular ray at the predecessor cell.

**Probe/evidence.** The semantic gate caught the initial four-slot schedule error. Round-two focused tests catch both the masked-stop false positive and the perpendicular-ray rival error. The final semantic stage passed on the current source.

**Failure modes/limits.** Rival sets are never complete. They encode plausible shortcuts found in this review, not all programs a model might learn. Authority-driven counterfactual audits can extend them without trusting generator-declared witnesses.

## 8. Reusable measurement instead of one-off inspection

**Original rationale.** No task-specific distribution census was present.

**Decision.** Maintain `workspace/distribution_probe.py`, which can load a frozen or current generator and report deterministic replay, errors, uniqueness, shape/count histograms, visible stops, adjacency, first-step stops, output-branch visibility, self-check findings, schedule frequencies, and three-demo lesson windows. Its schema is now `b0e266482663-distribution-probe-v2`.

**Alternatives considered.** Hand-inspecting several generated grids was rejected because rare schedule and override defects are seed-dependent. Only relying on the repository battery was rejected because generic stages do not expose task-specific rates. Reusing the version-1 probe unchanged was rejected because its stop classifier duplicated the production bug and overcounted masked stops.

**Probe/evidence.** A dedicated probe regression was observed red before the classifier fix and green after it. Version 2 reproduced the baseline at 31/278/388 both-direction visible stops and measured final 4.1.0 at 500/500 in each band. It also recorded final canonical shapes 364/370/370, first-step pairs 167/187/195, all three output branches in 1,500/1,500 draws, and lesson windows 36/36.

**Failure modes/limits.** The probe understands this task's marker colors and geometry. It is a reusable tool for this generator family, not a universal ARC analyzer. Metrics describe sampled behavior, not a proof over all seeds.

## 9. Bind evidence to the exact final source

**Original rationale.** A monolithic battery attempt was externally terminated and did not leave a completed aggregate result, while individual stages were independently resumable.

**Decision.** Replay every stage separately against the final source, retain each stage's `result.json`, and aggregate only receipts whose task ID, phase, pass status, and runtime-manifest generator hash match. Pair that with a complete declared-axis sweep and a fresh visible-only solve prepared after the final generator change.

**Alternatives considered.** Treating old green receipts as sufficient was rejected because they were bound to version 4.0.0. Trusting only the focused tests was rejected because they do not exercise the authority, generic grammar, catalog synchronization, or full override machinery.

**Probe/evidence.** All twelve stage receipts pass and bind to SHA-256 `8fbad8c57bf158d7dc0e83cf93a934cff70d0b5bf5ecc77c965c06f27e57ae77`; the aggregate is `checks/round2/stage-replay-summary.json`. The fresh solve passed all three visible demonstrations; the masked query remains honestly reported as unknown.

**Failure modes/limits.** The stage aggregation is review-side glue because the repository does not yet provide a supported resume/aggregate command. It validates receipt consistency but does not replace the stage implementations themselves.

## 10. Quantify over the full public marker domain

**Finding.** The canonical inputs contain exactly two row markers and two column markers. Earlier repaired lessons could therefore satisfy all branch and blocker checks while remaining compatible with fixed first/last one-, two-, or three-marker emission caps. The strongest cap of three survived because the public domain reaches four but the curriculum did not force all four to matter.

**Decision.** Derive cardinality witnesses and rivals from the declared `n_row_shoot` and `n_col_shoot` domain. Keep `separated_stops` at a minimum of two productive shooters per axis, and make each default `late_stops` example use all four productive row and column shooters. Add first/last one-, two-, and three-marker rivals and require each complete three-example lesson to falsify them.

**Alternatives considered.** Raising average marker counts without a deterministic fixture was rejected because sampled frequency does not guarantee a three-example lesson distinguishes a cap. Removing four from the public domain was rejected because the constructive grid can support it and the richer cardinality is useful training variation.

**Probe/evidence.** Red regressions reproduced one-, two-, and three-marker shortcuts. Final independent probes refuted every tested cap in `3000/3000` windows per difficulty; the version-6 census independently refuted its full cap set in 12/12 windows per band.

**Failure modes/limits.** This proves the tested ordered-prefix/suffix caps are inconsistent with the lesson. It does not enumerate arbitrary subsets or every conditional program a learner could construct.

## 11. Compose mechanisms with object rank

**Finding.** Version 4.5.0 made all four markers emit but still allowed blocker semantics to apply only to a subset. Many lessons fit rivals where the omitted extreme marker passed through blockers. A parallel crossing shortcut used cyan only when one ray came from the lowest shooter.

**Decision.** Treat object presence and mechanism application as separate obligations. Reserve a nonlowest-by-nonlowest crossing in `separated_stops`. In the default late fixture, visibly stop both the lowest and highest row shooters and both the lowest and highest column shooters while preserving suffix, branch, and crossing witnesses. Add marker-subset blocker-scope rivals and extreme-stop witnesses to `lesson_identifiable()`.

**Alternatives considered.** Merely requiring four blockers was rejected because blocker count does not show which shooter each blocker governs. Stopping four arbitrary shooters was rejected because the untested extreme could still support a prefix/suffix shortcut. Applying blockers to every shooter was rejected as unnecessarily rigid and less varied; both extremes are sufficient to falsify the declared rank-based rivals.

**Probe/evidence.** `checks/round3/blocker-scope-shortcut-v45.json` records the surviving version-4.5 rivals. On version 4.6.0, all eight first/last-two/three blocker-scope rivals were refuted in `3000/3000` windows per band. The 500-draw census observed both extreme row stops in 184/189/224 and both extreme column stops in 179/195/220 easy/medium/hard draws.

**Failure modes/limits.** The fixture is structured and therefore repeats some relational geometry. Random middle coordinates and extra blockers vary its surface form, but easy and medium uniqueness fall to 484/500 and 492/500 in the fixed census.

## 12. Keep an independent semantic shortcut probe

**Finding.** Production `self_check()` and an earlier reviewer probe once shared the same false definition of an observable stop. Reusing production rivals would repeat that failure mode for the new cardinality and blocker-scope checks.

**Decision.** Upgrade `workspace/distribution_probe.py` to schema `b0e266482663-distribution-probe-v6`. Its marker-cap, crossing-color, and blocker-scope renderers are implemented independently of `SEMANTIC_RIVALS`. Retain exact red/green logs, large independent window probes, a portable 91,104-case sweep, and twelve source-bound repository stage receipts.

**Alternatives considered.** Trusting `lesson_identifiable()` alone was rejected because it could share an implementation error with its rivals. Keeping only temporary one-off scripts was rejected because future agents need a repeatable audit tied to any compatible generator path.

**Probe/evidence.** The final probe reports deterministic replay, zero generation/self-check failures, 36/36 identifiable lesson windows, and every one of its 18 shortcuts refuted in every sampled window. Four supplemental probes each tested 3,000 windows per band. The complete declared-axis sweep and all twelve repository stages pass on generator SHA-256 `bd9bba5d02cec811f5e7a6f9b209281bfe604f47f224d9598e2bc050476e23ec`.

**Failure modes/limits.** Independence is architectural, not formal proof: both implementations could still embody the same conceptual omission. New shortcuts should be added first as failing independent tests, then to the durable probe and production lesson contract only after their disagreement is understood.
