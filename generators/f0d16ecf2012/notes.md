# Working notes: f0d16ecf2012

## 2026-10-02 review

The baseline's “one blob per compartment” assumption was false. A labeled canonical input has three diagonally adjacent same-color singleton objects in one lane; the canonical Racket uses same-color 4-connected object extraction and moves them independently. The old self-check rejected that input.

The generator was rebuilt as version 3.0.0 with:

- `RULE_HASH = 4e0031784e59`;
- a pure Python rule mirror checked against live Racket;
- exact observable axes only (`grid_w`, `n_compartments`, `comp_h`);
- strict unknown-key rejection and override observation;
- canonical-profile anchors every third ordinary draw;
- guaranteed witnesses against one-step movement, row-wise right alignment, and merging a lane into one object;
- lesson-level competitor elimination;
- task-local regression tests.

A first anchor cadence of every fourth sample measured 14/60 canonical-profile hits and failed the 25% floor. Every third sample measured 19/60 and passed. The final battery was 12/12 green; the task test suite was 16/16 green.

The selected base `target_code` differed from canonical/raw authority only by one comment. That comment was removed; executable Racket behavior was not changed. The canonical source still has three style-only linter findings.

At the end of version 3.0.0, the known curriculum restrictions included regular horizontal lanes, globally distinct lane colors, and fixed witness lane roles. The second pass below removes the latter two cross-sample shortcuts while retaining regular lanes and one non-wall color within each lane.

Imported associated notes, if any, remain in `evidence/associated_notes.jsonl` with their original provenance.

## 2026-10-02 second pass

A distribution-level probe found four shortcuts that the per-grid semantic gate
could not see in version 3.0.0: the split-component witness was always the
second lane, every split diagonal sloped down-right, only two connected witness
profiles occurred, and every lane color was unique. Over 240 fixed-dimension
draws the counts were exact (`240/240` in the fixed category for each role).

Version 3.1.0 removes those correlations while preserving the same executable
rule and exact public axes:

- the connected and split witness roles are shuffled between lanes;
- split patterns use both diagonal slopes;
- six connected profiles with genuinely nonuniform east edges replace the
  two-shape vocabulary;
- noncanonical draws mix distinct palettes with one color reused across
  wall-separated lanes;
- `workspace/correlation_probe.py` emits a source-bound JSON census and exits
  nonzero when any of those coverage classes is absent.

An attempted four-rotation L vocabulary was rejected during TDD: the two L
rotations whose rows share the same east edge are answer-equivalent under the
row-wise-right-align rival, so they stopped being rigid-motion witnesses. The
final six profiles all retain unequal row-wise east extents. The task-local
suite now contains 21 tests, including the correlation probe contract.

The final source-bound battery remained 12/12 green at generator SHA-256
`5289a055328f352aabb660b9e9f8e09592c84bb382c88faa8ab725a660be0ddb`;
the expanded task suite passed 21/21, and the final correlation report had no
coverage findings.

## 2026-10-02 third pass

A source-level comparison against the canonical motion program found a deeper
semantic omission in versions 3.0.0 and 3.1.0. The authority does not move an
object against walls alone. For each object it constructs a static occupied
board containing the walls and the object's **original cells**, then repeatedly
translates the current object. A vacated source cell can therefore block a
later step. One labeled canonical object moves only 1 column although wall-only
clearance is 7 columns. The previous generator produced no such object in a
900-draw census and its prose incorrectly said every component docked at the
wall.

Version 3.3.0 repairs the curriculum and documentation:

- adds the `ignore_source_footprint` named rival and
  `source_footprint_blocking` semantic witness;
- guarantees one connected source-blocked object and one ordinary wall-docking
  split-component object in every ordinary scene;
- samples eight connected witness profiles with authority stop distances 1 or
  2, always reserving extra wall-only clearance so the rival disagrees;
- covers all movable colors 1–8 in noncanonical support;
- replaces the predictable `sample_index % 3 == 0` anchor schedule with a
  source-hashed one-of-three slot per sample block;
- adds `workspace/motion_semantics_probe.py` and extends the correlation probe
  to audit anchor slots and block cardinality;
- expands the task-local suite from 21 to 29 tests.

The final 240-draw motion census has no findings: all 240 scenes contain both
motion regimes, all 240 disagree with wall-only docking, stop distances 1 and 2
both occur, and colors 1–8 are covered. The final correlation census has no
findings: both split positions and slopes, eight source-blocking profiles, both
palette modes, and all three anchor slots occur with zero block violations.
The integrated 12-stage battery is all green at generator SHA-256
`14b945e4b17ab4cdca182508fd67d8c78370e05221bdc6601f101dd37cd760dd`.
## Current reviewer considerations

Source SHA-256: `14b945e4b17ab4cdca182508fd67d8c78370e05221bdc6601f101dd37cd760dd`.

# Decisions for `f0d16ecf2012`

## D1 — Interpret diagonal adjacency as separate movable components

**Input evidence.** The canonical program uses same-color object extraction with 4-connectivity. One canonical lane contains a diagonal chain that is three singleton components, and the authority moves them independently. The baseline generator comment claimed two blobs in a compartment would overlap and therefore prohibited them; the original rationale beyond that comment is unknown.

**Alternatives considered.**

1. Keep exactly one component per lane and special-case the canonical sample in `self_check`.
2. Treat diagonal adjacency as one 8-connected object.
3. Model the authority directly: arbitrary same-color 4-connected components, evaluated independently.

**Choice.** Alternative 3. It is the only option that explains the canonical pair without exceptions and agrees with direct Racket execution.

**Probe.** All five labeled canonical pairs must pass `self_check`, and `rule_mirror(input)` must equal the canonical output exactly. This is enforced by `test_canonical_pairs_are_accepted_and_python_mirror_matches`.

**Failure mode / limitation.** Generated scenes still constrain components to regular horizontal lanes; the mirror is broader than the sampler.

## D2 — Replace advertised breadth with three honest axes

**Input evidence.** Baseline `palette_kind`, `palette_size`, `position_bias`, `density`, and `texture` either did not control the returned grid as declared, overlapped with deliberately invalid degenerates, or could not be observed exactly. Difficulty-specific draw bounds also contradicted the public valid ranges.

**Alternatives considered.**

1. Preserve every old axis and implement all cross-products.
2. Mark ambiguous axes as approximate or diagnostic.
3. Remove nonessential claims and retain only exact, returned-grid-observable controls.

**Choice.** Alternative 3: `grid_w`, `n_compartments`, and `comp_h` only. Their full declared ranges are legal in every band, and `observe_overrides` recovers them exactly.

**Probe.** Single-axis, pairwise, and extreme three-axis cases across easy/medium/hard, plus strict unknown-key rejection. The repository override gate exercised 12,060 draws over 134 cases.

**Failure mode / limitation.** Color relations, component count, and witness placement remain stochastic internals rather than caller-controlled axes. This is deliberate until an exact observable contract is needed.

## D3 — Preserve a canonical-profile floor with deterministic anchors

**Input evidence.** The baseline distribution had only 3/60 canonical-profile hits and no hard-band support. Broadening dimensions alone had moved the generator away from the source task.

**Alternatives considered.**

1. Restrict every sample to the canonical 3-lane, height-3, width-11/12/13 family.
2. Draw canonical dimensions randomly and accept whatever rate emerges.
3. Reserve a deterministic fraction for canonical anchors and use the rest for breadth.

**Choice.** Alternative 3. Unoverridden sample indices divisible by three draw from the canonical dimension family; other indices draw from the full envelope.

**Probe and failed attempt.** An every-fourth schedule produced 14/60 hits (23.3%) and failed the repository's 25% floor. A stricter task test was made red, then the cadence changed to every third. The final gate measured 19/60 and support in every band. Evidence is under `checks/iterations/profile_anchor_pre_fix/` and `checks/after/f0d16ecf2012_after_profile_floor.json`.

**Failure mode / limitation.** The modulo schedule is discoverable. It is useful for reproducible curriculum coverage but should not be mistaken for an unbiased natural distribution.

## D4 — Put all three semantic rebuttals in every ordinary draw

**Input evidence.** The task is vulnerable to cheap hypotheses that often agree on simple rectangles: move one step, shift each row independently, or merge all cells in a lane. A diversity metric cannot tell whether those hypotheses remain viable.

**Alternatives considered.**

1. Let witnesses occur stochastically and rely on large datasets.
2. Guarantee one witness per lesson window but not per pair.
3. Guarantee all three distinctions in each ordinary input.

**Choice.** Alternative 3 for this repair. It gives small three-example lessons strong identifiability and makes the claims easy to audit. Version 3.1.0 keeps every witness present but randomizes which lanes carry the connected and split roles.

**Probe.** Every default sample in every band must fire all three predicates; the semantic gate must verify each witness against its named rival and report 12/12 identifiable lessons. A separate cross-sample probe must observe each special role in more than one legal position.

**Failure mode / limitation.** Guaranteeing every distinction in every ordinary draw is still a strong curriculum regularity. It favors data value and small-lesson identifiability over a natural frequency distribution.

## D5 — Require at least two eastward moves

**Input evidence.** A component only one cell from its blocker makes “move one step” observationally equivalent to the real rule.

**Alternatives considered.** Permit one-step cases as ordinary noise, schedule them only after a lesson already distinguishes full motion, or exclude them.

**Choice.** Exclude them from ordinary draws by keeping every placed shape at least two full moves from the east wall.

**Probe.** `multi_step_motion` compares the authority mirror with a one-step rival and must fire on every sampled draw.

**Failure mode / limitation.** The training distribution does not include already-docked or one-step boundary cases. Those could be introduced later as explicitly labeled recombination cases, not as the only evidence in a lesson.

## D6 — Use asymmetric connected shapes for rigid translation

**Input evidence.** Horizontal or vertical bars can be moved correctly by several row-wise shortcuts. An L-like component exposes whether relative offsets are preserved.

**Alternatives considered.** Randomly hope for asymmetry, use a single fixed L, or draw from mirrored asymmetric teaching shapes plus broader extras.

**Choice.** Version 3.0.0 used two mirrored teaching shapes. Version 3.1.0 expands this to six connected profiles whose occupied rows have unequal east extents, so the row-wise docking rival must disagree.

**Probe.** `rigid_shape_translation` compares the mirror to a rival that decomposes every occupied horizontal run and docks it independently. The cross-sample probe also requires at least four distinct connected witness profiles.

**Rejected alternative.** Four simple L rotations looked symmetric, but two rotations have equal east edges across occupied rows and are therefore answer-equivalent under row-wise right alignment. TDD caught the lost witness, so those rotations were rejected rather than counted as superficial variety.

**Failure mode / limitation.** Six profiles remain a finite teaching vocabulary. Future expansion must preserve the diagnostic east-edge property instead of adding shapes that only look different.

## D7 — Validate independent-slide collisions instead of forbidding multiple components

**Input evidence.** The authority paints independently moved objects. In arbitrary arrangements two outputs could overlap and erase a cell, making a sample ambiguous for a conservation-based learner.

**Alternatives considered.** Ban all multiple-component lanes, analytically prove placements cannot collide, or compute the actual mirror and check colored-cell conservation.

**Choice.** Compute the mirror in `self_check` and require input/output colored-cell counts to match. The generated diagonal arrangement is constructed to be collision-free.

**Probe.** Structural mutation checks plus rule-smoke parity and the cell-conservation assertion.

**Failure mode / limitation.** This rejects some technically executable authority inputs whose independently painted objects overlap. That is an intentional training-domain restriction, not a claim about total program semantics.

## D8 — Pin and independently mirror the rule

**Input evidence.** The baseline had no `RULE_HASH`, no Python mirror, and exact selected-authority text divergence.

**Alternatives considered.** Trust catalog selection only, copy the Racket logic without a pin, or bind the generator to the normalized canonical rule hash and test an independent Python implementation.

**Choice.** Pin `RULE_HASH = "4e0031784e59"` and expose `rule_mirror` for parity checks.

**Probe.** The rule-smoke gate compared 120 generated inputs and reported 120/120 mirror matches; authority sync verifies all selected sources.

**Failure mode / limitation.** The mirror is test infrastructure, not a replacement authority. A shared bug is still possible, which is why canonical examples and live Racket execution remain required.

## D9 — Synchronize Racket text without changing behavior

**Input evidence.** Canonical `program_solution` and archival `raw_code` were exact matches. Selected `target_code` differed only by the line comment `;; Positions of every color 9 cell`; execution parity already passed.

**Alternatives considered.** Leave the diagnostic divergence, copy the comment into the other authorities, or remove it from the selected target.

**Choice.** Remove the lone nonsemantic comment from selected `target_code`. No form, binding, or expression changed.

**Probe.** Authority sync now reports one exact group and live parity across every labeled canonical pair.

**Failure mode / limitation.** The canonical Racket still triggers style-only lints (`dummy-let-binding`, `style-eq-zero`, `style-not-eq`). I did not rewrite working authority logic merely to silence style diagnostics.

## D10 — Add task-local regression tests as the reusable tool

**Input evidence.** The original defects crossed generator structure, authority semantics, sampling, overrides, and lesson composition; no single existing unit test captured that task-specific contract.

**Alternatives considered.** Rely only on the global battery, write a one-off analysis script, or keep a focused test suite beside the generator.

**Choice.** Add `tests/test_generator.py`. It is fast enough for future agents to run before the full battery and preserves the exact failure modes found here.

**Probe.** The first-pass suite was observed failing 16/16 on the baseline, then passing 16/16 after implementation. A later tightened profile test was separately observed failing before the anchor correction and passing afterward. The second pass added five tests with observed red states and now passes 21/21.

**Failure mode / limitation.** These tests intentionally encode the present curriculum choices. Future legitimate redesigns should update them and retain a new red/green rationale rather than treating them as immutable truth.

## D11 — Measure correlations across examples, not only semantics within one grid

**Input evidence.** Version 3.0.0 passed all 12 global battery stages and every generated grid fired all three semantic witnesses. A controlled 240-draw census nevertheless found four deterministic cross-sample cues: fixed split lane, fixed split slope, two connected profiles, and all-distinct palettes.

**Alternatives considered.** Trust the existing battery, inspect a few grids manually, or build a deterministic support-matrix probe tied to the source hash.

**Choice.** Build `workspace/correlation_probe.py` and make its contract part of the task test suite. This detects dataset shortcuts that are invisible to per-grid validity and rival checks.

**Probe.** The old source exits nonzero with four findings; version 3.1.0 exits zero with both positions, both slopes, six profiles, and both palette modes. Evidence: `checks/round2_correlation_probe_before.json` and `checks/round2_correlation_probe_final.json`.

**Failure mode / limitation.** The tool measures four known cues, not every possible latent correlation. It is a reusable pattern, not a proof of statistical independence.

## D12 — Randomize witness lane assignment

**Input evidence.** The split witness appeared in lane 1 for 240/240 controlled draws. This made semantic role predictable from absolute vertical position.

**Alternatives considered.** Swap roles on a fixed modulo schedule, choose roles randomly, or leave placement fixed and rely on other lanes for noise.

**Choice.** Draw two distinct lane indices from the layout RNG for connected and split roles. Randomization avoids a simple sample-index code while preserving exact witness coverage.

**Probe.** With two lanes held fixed, the final census observed split positions 121 and 119 times.

**Failure mode / limitation.** With more than two lanes, the remaining lanes are still generic extras and the two special roles are guaranteed to exist.

## D13 — Counterbalance split-diagonal orientation

**Input evidence.** Every version 3.0.0 split witness sloped down-right. Orientation is irrelevant because connectivity and eastward translation, not diagonal direction, define the lesson.

**Alternatives considered.** Deterministic alternation, arbitrary rotation/reflection of all patterns, or sample the two valid diagonal slopes.

**Choice.** Sample down-left or down-right. Vertical reversal is already equivalent inside the lane, so the two slope classes are the useful observable distinction.

**Probe.** The final census observed 133 down-left and 107 down-right witnesses while the independent-components witness remained true for every tested draw.

**Failure mode / limitation.** The split witness is still a compact diagonal pattern rather than arbitrary separated same-color components.

## D14 — Reuse colors only across wall-separated lanes

**Input evidence.** All-distinct lane colors in 240/240 draws could teach that color uniquely identifies a lane or object family. The authority only uses color to group components; color uniqueness across wall-separated lanes is unnecessary.

**Alternatives considered.** Reuse colors anywhere, keep all colors unique, or reuse one color only across lanes whose walls make the contexts unambiguous.

**Choice.** Preserve distinct colors for canonical anchors, but let noncanonical draws mix distinct palettes with one duplicated lane color. Within each lane there remains exactly one non-wall color.

**Probe.** The final three-lane census observed 117 distinct and 123 reused palettes; self-check, mirror parity, and the full battery stayed green.

**Failure mode / limitation.** This does not test multiple colors within one lane, which would broaden the executable domain but complicate the present canonical curriculum.

## D15 — Make audit evidence replayable from the returned packet

**Input evidence.** The carried-forward audit script initially depended on a private `.review/audit_runtime` compatibility import and failed after reconstruction with `ModuleNotFoundError: scripts`.

**Alternatives considered.** Omit the replay, copy private runtime files into the return, or bind the packaged `repo/shared/tools/comment_solutions.py` explicitly.

**Choice.** Make the evidence script self-contained against files that actually ship in the full packet. This changes no audited generator and preserves the original counterexamples.

**Probe.** The failed replay is retained at `checks/audits/reproduce_counterexamples_round2.failed.log`; the corrected replay at `checks/audits/reproduce_counterexamples_round2.log` reproduces both mismatches.

**Failure mode / limitation.** This is a packet-evidence compatibility fix, not a general cleanup of the repository's historical import surface.


## D16 — Treat the original object footprint as static authority state

**Input evidence.** The canonical program evaluates each object on a board that
still contains that object's source cells. In one labeled pair the authority
moves a connected color-7 object 1 column while a wall-only simulation moves it
7. Version 3.1.0 generated zero source-footprint disagreements in a 900-draw
probe and described all components as wall-docking.

**Alternatives considered.** Keep the simpler wall-only interpretation, model
all input objects as mutual blockers, or mirror the program's per-object static
source board exactly.

**Choice.** Mirror the authority exactly: walls plus the current object's
original footprint are static; other movable components are absent from that
object's motion board. Add an explicit wall-only rival and generated witnesses.

**Probe.** `checks/round3/motion_semantics_before.json` records the gap;
`checks/round3_final/motion_semantics.json` records canonical distance `1/7`,
240/240 generated disagreements, and both source-stop distances.

**Failure mode / limitation.** The generated curriculum covers stop distances 1
and 2, not every connected shape or arbitrarily long source-trail interaction.

## D17 — Pair source-blocked and wall-docking regimes in every ordinary scene

**Input evidence.** Teaching only source-blocked objects could replace the old
wall-only shortcut with a new shortcut that every object stops early. Teaching
only wall-docking objects omits the authority distinction entirely.

**Alternatives considered.** Rely on probabilistic coverage across episodes,
place both regimes deterministically in fixed lanes, or guarantee both while
randomizing their lane assignments and profiles.

**Choice.** Every ordinary scene contains a connected source-blocked witness and
a split-component wall-docking witness, with shuffled lane roles. This makes the
per-scene lesson identify both the exceptional-looking stop and ordinary full
travel.

**Probe.** The final motion census reports
`scenes_with_both_motion_regimes = 240`; the semantic gate fires all four
witnesses 600/600 across three bands.

**Failure mode / limitation.** Guaranteed witnesses make the curriculum denser
and more diagnostic than the unrestricted executable input domain.

## D18 — Vary source-stop distance rather than teach a one-step template

**Input evidence.** The first repaired source-blocking vocabulary stopped after
exactly one step. A learner could identify the gapped connected shape and apply
“move one” without representing the static source collision.

**Alternatives considered.** Keep one-step witnesses, sample arbitrary shapes
without proving their stopping distance, or curate profiles with independently
verified source stops.

**Choice.** Use eight connected profiles whose verified authority stop is 1 or
2, and reserve at least one additional wall-only step for every placement.

**Probe.** A failing test first required both distances; the final report
contains source-blocked `1/N` and `2/N` pairs and no coverage findings.

**Failure mode / limitation.** Distances longer than 2 are not currently forced.

## D19 — Preserve the canonical-profile rate without a fixed sample-index cue

**Input evidence.** Version 3.1.0 used `sample_index % 3 == 0`, exposing an exact
anchor position despite passing the profile floor.

**Alternatives considered.** Remove anchors and risk profile-floor regression,
choose each draw independently with probability one-third, or guarantee one
anchor per block while hashing its slot from task/version/seed/block.

**Choice.** Hash-select one of the three positions in each block. This preserves
the exact one-third support guarantee while distributing anchors over slots 0,
1, and 2.

**Probe.** The final 240-block census observes slots 0/1/2 as 28/31/21 with
zero blocks containing other than exactly one anchor.

**Failure mode / limitation.** The block-level one-of-three rate remains a
curriculum design choice, though its absolute slot is no longer predictable.
