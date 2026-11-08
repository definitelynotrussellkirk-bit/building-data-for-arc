# Working notes: 331074b4dcbc

## 2026-09-28 review `review-e05cdb62f199fe30`

### Rule understanding

The row-zero nonzero prefix is a tile. Replace the single solid cyan-8 rectangle below row zero by repeating that tile from the rectangle's left edge, independently on each rectangle row. A row-zero 8 is tile data, not a rectangle marker.

### Baseline diagnosis

- Battery: 7 green, 2 advisory, 3 failed.
- Missing `RULE_HASH`; semantic contract absent.
- Nine declared axes did not describe generation. Override contract: 5,797 findings / 47,700 draws; unknown keys accepted.
- Exact canonical morphology appeared in only 6/60 draws.
- `self_check` did not establish a contiguous distinct seed or one solid rectangle.
- Canonical examples all have `seed_length == rectangle_height`, so that shortcut fits the entire canonical set.

### Implemented curriculum

Version 2.0.0 uses eight exact `scene_profile` values. Every profile:

- has an exact canonical `(height, width, palette-size)` morphology;
- has `seed_length != rectangle_height`;
- starts the rectangle at a nonzero local-vs-global phase offset;
- has rectangle width non-divisible by seed length, exposing row reset;
- round-trips through `observe_overrides`.

Two profiles put color 8 in the seed to preserve the canonical marker/data overlap branch. All bands allow all profiles and only change their weights.

### Semantic hypotheses and evidence

Declared rivals:

1. force tile period to rectangle height;
2. phase from global column zero;
3. continue phase across rectangle rows.

Each generated profile is a witness against all three. Final semantic gate: strict 600/600, three witnesses firing 600/600 each, three rival claims verified 60/60 each, 12/12 lessons identifiable.

### Validation choices

One `_analysis` parser powers `self_check`, strict support, override observation, the Python mirror, rivals, and witnesses. It fails closed on malformed grids and semantic impostors. Degenerate positive examples (`no_seed`, `no_rect`, `monochrome_seed`) were removed because the canonical task does not define their outputs.

### Verification

- Prescribed after battery: 12/12 green.
- Profile floor: 60/60 exact and 60/60 envelope.
- Override: 810/810 accepted, zero findings, unknown keys rejected.
- Rule mirror: 120/120 generated parity.
- Diversity: 88% unique inputs/outputs over 300 pairs.
- Selected Racket and canonical authorities were not edited.

### Remaining limitations

The finite profile grammar prioritizes exactness and semantic information over exhaustive geometry. Identifiability is proved only against the three declared rivals. Generic mutation sensitivity is 57/60 because some minority-color removals remain structurally lawful.
## Current reviewer considerations

Source SHA-256: `91b88af47aff629f3c53f1f23ce80aec88e94840d7e124fe52d4c16d9fce8bad`.

# Design decisions for `331074b4dcbc`

Each section records the original behavior or rationale, the adopted choice, alternatives considered, the probe used, and known failure modes.

## D1. Preserve the selected rule authority

**Original rationale:** Unknown. The selected Racket program already encoded the canonical transformation and passed canonical execution, rule smoke, grammar, lint, and source synchronization checks.

**Decision:** Leave all Racket/canonical authority files unchanged and pin the Python generator to rule hash `663523cb8af9`.

**Alternatives considered:** Rewrite the selected Racket for style; replace it with the independent Python mirror; modify the archival divergent raw source. All were rejected because there was no semantic failure and each would increase source-role risk without improving training data.

**Probe:** Exact execution on all canonical pairs, 120 generated rule-smoke applications, and authority synchronization/execution parity.

**Failure modes / limitations:** One archival authority remains textually divergent. The gate confirms execution parity, not textual identity across every archival representation.

## D2. Replace nine misleading axes with one exact scene profile

**Original rationale:** The original comments called the controls “combinatorial axes,” presumably to expose dimensions, palette, density, position, and texture. In practice most were dead, aliased, private-RNG-controlled, or incompatible with band-specific ranges.

**Decision:** Expose only `scene_profile`, with eight finite values recoverable exactly from the returned grid. A profile atomically specifies a supported geometry and whether the seed contains marker color 8.

**Alternatives considered:**

1. Repair every old axis independently. Rejected because many combinations would require a constraint solver or a large incompatibility matrix, and several values were semantically meaningless (`density=sparse`, fixed `position_bias`).
2. Expose separate exact axes for every geometric coordinate. Rejected because free recombination would easily leave the canonical envelope or create non-observable/invalid combinations.
3. Expose no axes. Rejected because exact targeted generation is useful for tests, data balancing, and future agents.

**Probe:** Override contract over 810 draws and 9 cases; explicit round-trip tests for all profiles in every band.

**Failure modes / limitations:** Atomic profiles trade combinatorial freedom for honesty. Adding a new geometry requires a new profile and exact inverse signature.

## D3. Stay on exact canonical morphology

**Original rationale:** The old generator sampled heights 6–9 and widths 11–14, likely to diversify grids, but this produced low canonical-profile support.

**Decision:** Use only the canonical size/palette signatures `(6,12,4)`, `(6,12,5)`, and `(5,13,4)`. The strict gate requires every generated scene to match one of them.

**Alternatives considered:** Keep broad dimensions; use a looser bounding-box envelope; add larger canvases only for hard examples. Rejected because the assigned goal is high-value training data, and exact morphology removes a source of distribution drift while still allowing semantic variation.

**Probe:** Profile floor moved from 6/60 exact and 7/60 envelope to 60/60 for both; strict semantic support is 600/600.

**Failure modes / limitations:** This does not teach scale extrapolation. A future, separately validated expansion could add larger exact profiles after semantic coverage remains guaranteed.

## D4. Seed length and palette

**Original rationale:** The old generator used two or three distinct non-8 colors, matching most obvious canonical seeds but incorrectly excluding the canonical case where 8 appears in the seed.

**Decision:** Keep seed length at two or three and require distinct nonzero colors. Six profiles exclude 8 and two profiles deliberately include 8, with the remaining colors drawn from `{1,2,3,4,5,6,7,9}`.

**Alternatives considered:** Always include 8; never include 8; allow repeated/monochrome seeds; permit seed length one or four. Rejected because always/never would distort support, repeated colors make the period ambiguous, and lengths outside two/three are not canonically supported.

**Probe:** All canonical inputs pass, marker-overlap profiles round-trip exactly, and the semantic oracle treats row-zero 8 as tile data rather than rectangle marker.

**Failure modes / limitations:** Only two of eight profiles force marker overlap. Difficulty weighting can alter frequency but not eliminate the branch.

## D5. Rectangle geometry is selected to expose rule semantics

**Original rationale:** The old private RNG selected rectangle height 2–3, width 5–8, and interior placement. Those choices produced valid-looking scenes but did not guarantee that phase conventions were observable.

**Decision:** Every profile enforces:

- `seed_length != rectangle_height`;
- `rectangle_left % seed_length != 0`;
- `rectangle_width % seed_length != 0`;
- at least two rectangle rows and width greater than one tile.

These conditions respectively refute height-as-period, global-column phase, and continuous row phase.

**Alternatives considered:** Random geometry with rejection sampling; one handpicked geometry; exhaustive coordinate products. Rejection sampling would obscure override behavior, one geometry would encourage template memorization, and exhaustive products would add unsupported morphologies.

**Probe:** Each of three witnesses fires 600/600 times; each named rival disagrees with the official rule on 60/60 independent checks.

**Failure modes / limitations:** Because every sample is maximally diagnostic, the training distribution does not include semantically redundant/easier geometry. That is intentional for data value but may differ from natural frequency.

## D6. Rectangle position coverage

**Original rationale:** The original generator kept the rectangle away from borders (`r1,c1 >= 2`), with no stated reason.

**Decision:** Include left, right, center, and bottom placements within canonical canvases, including top coordinate 1 and several different left offsets, while never overlapping row zero.

**Alternatives considered:** Fully uniform legal placement or preserving the interior-only policy. Uniform placement would require many more profiles to retain exact observability; interior-only was rejected because it needlessly teaches a location prior.

**Probe:** The eight profile signatures are all generated and recovered exactly; local-vs-global phase differs for each.

**Failure modes / limitations:** Bottom-boundary placements are represented, but no profile touches the right canvas boundary and not every legal coordinate is represented.

## D7. Difficulty bands change weighting, not validity

**Original rationale:** The old bands changed canvas ranges, which made declared dimension overrides legal in metadata but illegal in a particular band.

**Decision:** All eight profiles are legal in all bands. Bands only upweight different diagnostic profiles: short profiles for easy, long/center profiles for medium, and bottom/marker-overlap profiles for hard.

**Alternatives considered:** Disjoint per-band profile sets or no weighting. Disjoint sets would make overrides band-dependent again; no weighting would make difficulty inert.

**Probe:** Every profile succeeds under `None`, easy, medium, and hard in task tests; override contract reports no combination rejection.

**Failure modes / limitations:** The bands are pedagogical mixtures, not calibrated empirical difficulty estimates for Qwen3.5-9B.

## D8. Remove degenerate examples from positive generation

**Original rationale:** `no_seed`, `no_rect`, and `monochrome_seed` were apparently intended as negative or degenerate textures. However, `self_check` waived all checks for them, so they entered the generator contract as accepted examples with no defined target behavior.

**Decision:** Remove these values from `AXES` and positive generation. Malformed scenes are instead used as rejected validator tests.

**Alternatives considered:** Keep them with identity outputs; add a classification task; retain them as private fuzz cases. The first two change the assigned transformation, while private mutations are better handled by tests and self-check probes.

**Probe:** Unknown/removed values are rejected, destructive mutation sensitivity improved, and malformed hollow rectangles, wrong colors, and duplicate seeds fail closed.

**Failure modes / limitations:** The generator does not teach “do nothing when no marker exists.” That behavior is not established by the canonical task.

## D9. Share one structural analyzer across contracts

**Original rationale:** The old validator was intentionally lightweight but accepted many semantic impostors.

**Decision:** Centralize grammar extraction in `_analysis` and reuse it in validation, profile observation, strict support, the Python oracle, rival rules, and witness predicates.

**Alternatives considered:** Independent parsers for each hook or a permissive oracle that tries best effort. Multiple parsers risk drift; permissive execution can silently assign outputs to invalid data.

**Probe:** Canonical and generated scenes pass; malformed grids return explicit errors; `rule_mirror` raises instead of fabricating an answer; lint and defect lint are clean.

**Failure modes / limitations:** Shared analysis means one parser defect could affect several hooks. The independent selected Racket execution and task-local mutation tests provide a second line of defense.

## D10. Add explicit rival-rule and lesson-identifiability contracts

**Original rationale:** None existed. The baseline semantic gate reported no contract.

**Decision:** Declare three plausible rivals and three executable witnesses. Require two-demo lessons to eliminate any rival that would answer the query differently.

**Alternatives considered:** Rely only on output diversity; enumerate many speculative rivals; use a model-in-the-loop judge. Diversity does not imply identifiability, a large rival list can become arbitrary, and a model judge is expensive/non-deterministic.

**Probe:** Semantic gate passes strict 600/600, witnesses 3/3, rival claims 3/3, and lessons 12/12 across all bands.

**Failure modes / limitations:** The rival set is curated, not complete. Future audit findings should be added as executable competitors and witnesses rather than prose only.

## D11. Add task-local tests and retain evidence

**Original rationale:** No task-local regression tests existed.

**Decision:** Add focused pytest coverage for canonical parity, profile exactness, semantic witnesses, identifiability, and fail-closed behavior. Retain immutable before and final after batteries plus the audit evidence script.

**Alternatives considered:** Depend only on the generic battery. Rejected because task-specific semantic facts—especially color-8 seed overlap and phase-reset rivals—deserve stable executable tests.

**Probe:** Focused tests and the full generic battery pass.

**Failure modes / limitations:** The tests intentionally inspect private `_analysis` facts for constructing mutations; a future internal refactor may require test updates even if external behavior is unchanged.
