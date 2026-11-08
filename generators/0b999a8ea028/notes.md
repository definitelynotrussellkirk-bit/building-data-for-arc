# Working notes: 0b999a8ea028

## Review finding

The imported v2.0.1 generator mirrored the selected rule on the three public
pairs, but its ordinary distribution did not make the rule identifiable. It
had no `RULE_HASH`, accepted unknown override keys, narrowed declared dimension
overrides by difficulty, and declared no semantic contract. Canonical examples
also admit three strong rivals: choose the first/only non-blue object, recognize
only 5x5 frames, or place the shape at the frame interior's top-left. All three
are answer-equivalent on every public pair.

## v3 choices

- Preserve the canonical Racket source unchanged; its normalized hash already
  matches assignment authority `d8a130fd2a56`.
- Replace probabilistic textures with an exact four-residue schedule so any four
  consecutive demonstrations cover the canonical positive, size-selection,
  generalized-frame/centering, malformed-blue, and no-frame evidence needed to
  distinguish the rule.
- Keep only three exact, observable axes: `grid_h`, `grid_w`, and `texture`.
  Every legal boundary combination is constructible in all difficulty bands.
- Bias natural canonical/no-frame dimensions toward 11x11, 12x12, and 13x13,
  while retaining all declared endpoints through exact overrides.
- Add a pure Python `rule_mirror`, structural scene analysis, strict canonical
  recognizer, override observer, semantic witnesses/rivals, shortcut declarations,
  and a lesson-level identifiability check.
- Make `self_check` profile-aware and mutation-sensitive instead of merely
  checking that some blue and non-blue pixels exist.

## Verification notes

Focused tests were written first and observed failing against v2.0.1. They cover
all public pairs, four-profile scheduling, rival counterexamples, all declared
override boundaries, unknown-key rejection, deterministic/fresh generation,
strict-profile support, and a broken-frame near miss.

The host packet lacks an executable Racket runtime. Attempts to locate a bundled
runtime and to install/download the official minimal runtime failed because no
Racket executable or network route is available. Racket-dependent battery
stages therefore remain environmental rather than silently skipped.

Imported associated notes retain original evidence/timestamps in
`evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `dbdfd0ac67ccd457800595068a3c044a0c0792dddc7b02ce019a7be4f4a78ccc`.

# Generator decisions: `0b999a8ea028`

This records each material input/distribution choice, its inherited rationale when known, alternatives considered, the probe used, foreseeable failure modes, and current limitations.

## D1. Preserve the selected Racket rule

**Choice.** Keep the canonical Racket source unchanged and pin the generator with `RULE_HASH = "d8a130fd2a56"`.

**Original rationale.** The imported v2 generator already described the selected rule correctly, and the selected active authorities share the same normalized program. The assignment explicitly identifies this hash.

**Alternatives considered.** Rewrite/simplify the Racket program; change tie handling; special-case the connected-blue negative.

**Probe.** The Python mirror reproduces all three canonical outputs; static `racket_lint` is green; authority inspection reports selected active sources synchronized.

**Failure modes.** A Python/Racket semantic difference could remain in component enumeration, stable ties, or `quotient` centering.

**Limitation.** Racket is unavailable in this host, so generated-case parity is unmeasured. Changing verified rule text without executable validation would have increased risk and was rejected.

## D2. Use a four-example deterministic semantic schedule

**Choice.** `sample_index % 4` selects `canonical`, `size_contest`, `nonframe_blue`, then `no_frames`; `EXAMPLES_NEEDED = 4`.

**Original rationale.** v2 said 3–4 demonstrations should expose rivals but sampled helpful textures probabilistically. That did not guarantee a self-contained lesson.

**Alternatives considered.** Keep random texture selection; weighted random profiles; six or more micro-profiles; encode multiple rivals in one crowded board.

**Probe.** Focused tests examine eight sliding four-example windows in every difficulty band. Every window contains all four profiles and refutes all declared competitors in the Python contract. The after semantic census saw every profile in every band.

**Failure modes.** A consumer that always requests the same sample-index residue will see only one profile. Determinism may expose the schedule to a model that memorizes ordering.

**Limitation.** The schedule guarantees curriculum coverage, not distributional independence. Shuffling complete four-example blocks is safe; arbitrary subsampling is not guaranteed to be identifiable.

## D3. Declare only three observable override axes

**Choice.** Keep `grid_h`, `grid_w`, and `texture`; remove implicit knobs for random internal shape/count/layout choices.

**Original rationale.** v2 declared those same high-level axes, but its dimension ranges were inconsistent with per-difficulty implementation ranges. The internal random choices were not declared contracts.

**Alternatives considered.** Add explicit axes for prototype shape/color, frame size/count, decoy position, and layout; retain the larger v2 texture vocabulary.

**Probe.** The strict override matrix tested 175 cases over three bands and 15,750 draws, with zero findings/warnings and unknown-key rejection.

**Failure modes.** Fewer public axes limit targeted external experiments. Adding an internal choice later without an observable signature could weaken override auditing.

**Limitation.** Prototype color and canonical shape remain deterministic keyed draws, not caller-controlled axes.

## D4. Set dimensions to `11..18` by `11..20`

**Choice.** Use full declared ranges in every difficulty band. Natural draws are heavily biased to 11, 12, or 13, while overrides reach every endpoint exactly.

**Original rationale.** v2 declared `grid_h=9..18` and `grid_w=10..20`, but actual branches often used smaller subranges and rejected declared values. Very small endpoints also made the new 7x7/frame-composite profiles unnecessarily cramped.

**Alternatives considered.** Preserve 9/10 minima with more placement logic; use only 11–13 canonical squares; make ranges difficulty-dependent and declare incompatibilities.

**Probe.** Cartesian endpoint tests cover heights 11/18, widths 11/20, all four textures, and all three bands. The after profile gate rose to 44/60 exact and 45/60 envelope.

**Failure modes.** Strong natural bias can underrepresent large canvases; the exact public-size rate may be higher than downstream training wants.

**Limitation.** Large-endpoint morphology is contract-tested but sampled infrequently without an override.

## D5. Keep compact canonical prototype shapes

**Choice.** Canonical, malformed-blue, and no-frame profiles use the three public-like 3/4-cell, two-row shapes; `size_contest` uses a fixed five-cell 3x3 cross-like prototype.

**Original rationale.** The canonical examples contain compact 3/4-cell objects. v2 grew arbitrary connected objects, which increased diversity but did not guarantee a clean centering or object-selection witness.

**Alternatives considered.** Random polyomino growth; rotations/reflections; larger 6–8-cell prototypes; disconnected prototypes.

**Probe.** `strict_canonical_like`, profile-floor census, scene analysis, and focused tests verify public support and fit in all frame interiors.

**Failure modes.** A model may overfit to the small fixed shape family or the size-contest cross.

**Limitation.** Shape diversity is intentionally secondary to semantic identifiability in this revision. A future revision can add rotations/reflections after native parity is available.

## D6. Use arbitrary nonblue prototype colors, excluding 0 and 1

**Choice.** Keyed draw from colors 2–9; size-contest decoy uses a different nonblue color.

**Original rationale.** The rule preserves the prototype color and reserves 0 for background and 1 for frames. v2 used the same palette convention.

**Alternatives considered.** Fixed colors per profile; same color for decoy and prototype; palette-specific curricula.

**Probe.** Component analysis, rule mirror, and diversity gate. Global RNG state and deterministic replay are explicitly tested.

**Failure modes.** Different-color objects make component separation easy and may underteach same-color disconnected components.

**Limitation.** Same-color decoy/prototype cases are not currently generated.

## D7. Make the size-selection witness scan-order adversarial

**Choice.** Put a two-cell decoy at the earliest scan position and a later five-cell prototype before a 7x7 frame.

**Original rationale.** The canonical examples have exactly one nonblue object, so “first object” and “largest object” are indistinguishable. v2's `size_contest` intent was correct but not guaranteed in every lesson.

**Alternatives considered.** Place the larger object first; use equal-size ties; use three decoys; distinguish by color or proximity.

**Probe.** `decoy_precedes_largest` witness, `first_nonblue` rival, canonical-shortcut test, and the exact witness in `QUESTION_ANSWER.md` / `checks/shortcut_witness.txt`.

**Failure modes.** Fixed positions may create a positional meta-shortcut. Equal-size tie behavior remains untested.

**Limitation.** The profile teaches strict size selection, not stable tie selection.

## D8. Generalize exact frames beyond 5x5

**Choice.** Canonical uses 5x5 frames; size-contest uses 7x7; nonframe-blue uses one 6x6 exact frame.

**Original rationale.** Every exact frame in the public pairs is 5x5, so a fixed-size detector fits all demonstrations despite not being the selected rule.

**Alternatives considered.** Random rectangles with independent height/width; only squares; a separate profile for each size.

**Probe.** `generalized_frame` witness, `fixed_5x5_frames` rival, exact profile tests, and the 600-draw semantic census.

**Failure modes.** All generated exact frames are still square, so “exact square border” remains a narrower untested rival than “exact rectangular border.”

**Limitation.** Non-square exact frames should be the next semantic extension once Racket parity can be run.

## D9. Force a positive centering offset

**Choice.** The five-cell 3x3 prototype is stamped in a 7x7 frame with a 5x5 interior, producing positive row/column offsets.

**Original rationale.** Public examples center shapes in 3x3 interiors where at least one relevant offset can be zero; top-left placement remains answer-equivalent across all three public pairs.

**Alternatives considered.** A standalone odd/even `odd_center` texture; larger rectangular frames; asymmetric offsets.

**Probe.** `positive_center_offset` witness and `interior_top_left` rival disagree on the size-contest profile; focused tests assert this.

**Failure modes.** Only positive symmetric offset is taught. Odd negative differences are structurally excluded because the prototype always fits.

**Limitation.** Floor/quotient bias for odd leftover space is not isolated by this profile. The selected rule's centering is mirrored, but a dedicated odd-bias witness could be added later.

## D10. Add a one-cell-broken blue ring

**Choice.** `nonframe_blue` contains one exact 6x6 frame and a separate 5x5 ring missing exactly one border cell.

**Original rationale.** The rule accepts exact border components, not arbitrary blue objects or bounding boxes. v2 intended a nonframe-blue texture, but the new version gives it a precise, inspectable morphology.

**Alternatives considered.** Solid blue rectangle; extra interior pixel; disconnected blue fragments; ring with two missing cells.

**Probe.** `nonframe_blue_component` witness, `any_blue_bbox` rival, profile-specific `self_check`, and a one-cell-broken mutation fixture.

**Failure modes.** A rival that merely ignores the smaller blue component could still succeed on this profile for the wrong reason.

**Limitation.** The current profile does not vary which border cell is missing.

## D11. Preserve a no-exact-frame negative

**Choice.** `no_frames` paints two 5x5 apparent frames touching edge-to-edge, making one connected blue component whose bounding-box border is not exactly its cell set. The output is blank.

**Original rationale.** The second canonical training pair is a connected composite of apparent frame structures and has a blank output. v2 had `no_frames`, but its own self-check rejected it.

**Alternatives considered.** No blue pixels; one broken ring; two disconnected broken rings; a solid blue object.

**Probe.** `self_check` accepts the profile; `rule_mirror` returns blank; every four-example lesson includes it; exact canonical negative is accepted by `strict_canonical_like`.

**Failure modes.** A shortcut such as “ignore connected double frames” could fit without understanding exact border equality.

**Limitation.** Only one connected-composite topology is generated.

## D12. Use fixed corner placements with non-overlap by construction

**Choice.** Place objects/frames at deterministic corners/edges sized from the final dimensions rather than retry random packing.

**Original rationale.** v2 used randomized placement with up to 150 retries and relaxed frame count on tight grids. That made overrides and semantic coverage fragile.

**Alternatives considered.** General rejection-sampling packer; occupancy-aware random layout; full layout axis.

**Probe.** 15,750 strict override draws, three-band focused tests, diversity gate, and deterministic/fresh-object tests.

**Failure modes.** Spatial regularity can become a shortcut; generated boards do not stress occlusion or arbitrary translation.

**Limitation.** This revision prioritizes contract reliability over layout entropy. A later occupancy-based randomizer should be added only with the same exhaustive override matrix.

## D13. Make `self_check` structural and profile-aware

**Choice.** Analyze 4-connected components, exact borders, prototype geometry, profile identity, and override realization.

**Original rationale.** v2 checked only broad pixel/object presence and therefore both admitted weak cases and rejected its intended no-frame negative.

**Alternatives considered.** Minimal invariants only; compare output to the mirror; invoke Racket from `self_check`.

**Probe.** Focused canonical/profile tests, mutation fixture, static lint, and immutable `selfcheck` stage.

**Failure modes.** The checker and generator share helper logic, so a common bug can evade both.

**Limitation.** Independent native Racket execution is still needed for semantic parity.

## D14. Declare rivals and lesson identifiability in code

**Choice.** Make plausible shortcuts executable and require a four-demo lesson to refute each one.

**Original rationale.** Comments in v2 named some rivals, but the tooling could not verify whether generated lessons actually falsified them.

**Alternatives considered.** Document rivals only; rely on aggregate distribution statistics; add hidden answer labels.

**Probe.** Canonical shortcut check (3/3 each), focused generated counterexamples, four-profile lesson tests, and semantic-gate witness census.

**Failure modes.** The declared competitor set is not exhaustive. In particular, square-only frames and fixed positional policies remain possible.

**Limitation.** The semantic gate could not authoritatively execute the Racket rule here, so its rival claims remain structurally demonstrated by the Python mirror/tests but not native-verified.
