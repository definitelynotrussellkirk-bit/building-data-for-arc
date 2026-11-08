# Current notes: 66a121e0d7e4

## Intended rule

Color-8 cells in column 0 select payload rows and color-8 cells in row 0 select payload columns. Extract their ordered Cartesian intersection. Command `(0,0)` applies: 1 identity, 2 clockwise, 3 180 degrees, 4 counter-clockwise. Canonical authority hash: `c03aadcd616e`; the Racket rule was not changed.

## Review repair (generator 4.0.0)

Generator 3.0.0 used sparse 7x8–14x16 boards, documented the command mapping incorrectly, declared dead controls, narrowed exact overrides by difficulty, and had no `RULE_HASH`, validator, oracle, or semantic lesson contract. Version 4.0.0 replaces it with dense 5x5–9x10 scene profiles, exact observable `scene_profile/cmd/n_rows/n_cols` controls, strict call validation, canonical-size anchors in every band, and an eight-step curriculum with seven demonstrations plus one query.

Every default sample has a fourth selector on at least one axis. This refutes the strongest canonical-fitting shortcut, `first_three_selectors`, which matches all five labeled canonical pairs. Other declared rivals are `ignore_command` and `selector_span`; each has an executable mapped witness. The minimal Racket-checked shortcut counterexample is under `counterexamples/review-0fd77e2c8a314ae1-v0001/`.

## Evidence

- Task regressions: 46 passed, including all 2,048 exact cross-product calls and batched Racket parity.
- Final battery: 11 green stages; semantic content passes but the stage exits on the shared `declared_period_not_enumerated` warning.
- Production census: 300 lessons, 2,400 unique inputs, 2,400 rotations, zero declared ambiguity/errors.
- Fixed-seed schedule census: period 8 × 3 bands = 24 lessons and 192 rotations, complete and unambiguous.
- Independent audit: 400 samples, no validation/determinism/oracle errors; 21 Racket applications, no mismatch.

## Assumptions and limits

The strict hook describes a broad dense canonical-like manifold, not every conceivable lawful input. The rival set is finite; census success does not prove unique induction against undeclared hypotheses. Period enumeration is exhaustive only for seed 0 and the three requested bands. The fixed schedule is declared rather than hidden; the shared semantic gate currently cannot consume the completed census receipt.
## Current reviewer considerations

Source SHA-256: `da201e9ac177acbd53a435c18b5c3d33fa1e86f06c3c1fb89d3353f3be041705`.

# Decisions for 66a121e0d7e4

## D1 — Keep the selected Racket authority unchanged

**Prior choice:** generator 3.0.0 described a different command mapping in prose (`2=flip`, `3=CW`, `4=180`) but had no `RULE_HASH` or executable mirror.

**New choice:** bind the generator to canonical rule hash `c03aadcd616e`: command 1 is identity, 2 rotates clockwise, 3 rotates 180 degrees, and 4 rotates counter-clockwise.

**Why:** all five labeled canonical pairs and the canonical source agree on that mapping. Changing the rule would have been unjustified. The independent probe and task tests compare both canonical and generated inputs with the real Racket worker.

**Limit:** the Python mirror is diagnostic only; Racket remains label authority.

## D2 — Replace sparse oversized boards with dense canonical-like profiles

**Prior choice:** dimensions varied roughly 7x8 through 14x16, with content only at selected intersections. This created a visually sparse task unlike canonicals and failed distribution/profile-floor checks.

**Alternatives considered:**

1. Keep arbitrary height/width axes and merely reduce their ranges.
2. Preserve the sparse payload but inject a few distractor colors.
3. Use named scene profiles with full dense interiors.

**Choice:** eight uniquely shaped profiles from 5x5 through 9x10, including exact canonical shapes 5x5, 5x6, and 6x5. Every interior cell is ordinary multicolor payload data.

**Why:** named profiles make shape an exact observable axis, keep the full axis cross-product constructive, and guarantee canonical anchors in every band. Dense payload prevents the shortcut “all nonzero interior cells are answer cells.”

**Probe:** distribution/profile-floor gates are green; all 400 independent-audit samples pass strict validation.

## D3 — Advertise only four honest exact axes

**Prior choice:** `palette_kind`, `palette_size`, `position_bias`, `n_distinct_colors`, `density`, and `texture` were declared but dead, aliases, singleton controls, or degenerate escape hatches. Difficulty narrowed command and selector ranges, rejecting otherwise valid exact overrides.

**Choice:** expose only `scene_profile`, `cmd`, `n_rows`, and `n_cols`. Each is recoverable from pixels by `observe_overrides`; all values are legal in every difficulty band; unknown keys and nonliteral scalars are rejected.

**Why:** these are the actual independent semantic controls. A focused regression enumerates 8×4×4×4 combinations in each of four band settings (2,048 calls) and checks validity plus exact observation.

**Failure found during implementation:** rare one-column selections sampled equal payload values and failed the nonuniformity invariant. A failing full-cross-product test was added before `_ensure_selected_variety` was implemented.

## D4 — Use an eight-step, seven-demo curriculum

**Policy:** `LESSON_SCHEDULE_PERIOD = 8`, `EXAMPLES_NEEDED = 7`, one query. Commands are `[1,2,3,4,2,3,4,1]`; selector-count pairs ensure every sample has four selectors on at least one axis.

**Why seven demos:** holding out any one of eight samples still leaves both instances of each command except possibly one, several nonidentity transformations, and at least seven fourth-selector witnesses. It is intentionally stronger than the previous random smoke curriculum.

**Query policy:** arbitrary rotation is supported, not just the last item. The 300-lesson census used `--rotate-query --rotation-policy require`; the period census checked every one of eight query positions at every start residue in all three bands at seed 0.

**Measured results:** 300/300 production lessons and 2,400/2,400 rotations had no declared ambiguity. Fixed-seed period enumeration completed 24/24 lessons and 192/192 rotations.

**Limits:** this exhausts only the declared period at seed 0 and tests only the declared rival set. It does not prove unique induction against every possible rule or every seed.

## D5 — Declare executable rivals and witnesses

The compact rival set is:

- `first_three_selectors`: ignore selectors after the third. It fits all five labeled canonical pairs.
- `ignore_command`: extract but do not rotate.
- `selector_span`: crop every row/column between the outermost selectors rather than exact indices.

Mapped witnesses are `more_than_three_selectors`, `non_identity_command`, and `gapped_selectors`. The first rival is also declared under `CANONICAL_SHORTCUTS` and has a minimal Racket-checked counterexample under `counterexamples/review-0fd77e2c8a314ae1-v0001/`.

**Rejected alternative:** declaring dozens of syntactic rotation variants. The current set targets the strongest public-data shortcut and two qualitatively different misreadings while remaining understandable and independently testable.

## D6 — Validate a broad canonical-like manifold, not one generator trace

`self_check` accepts every canonical input and generated profile while enforcing rectangular ARC colors, supported shapes, legal headers, 1..4 selectors per axis, dense interior payload, broad color use, and informative multi-cell selections.

**Rejected alternative:** require all ten colors or zero-free interiors. One canonical input uses only nine colors and another contains an interior zero, so those restrictions would encode the sampler rather than the task manifold.

## D7 — Preserve and report the shared semantic-gate warning

The final semantic smoke stage is otherwise clean but reports `declared_period_not_enumerated` solely because the shared gate cannot consume a separate census receipt. I did not remove the truthful schedule declaration to manufacture a green battery. `checks/schedule-census-final.json` is source-bound to the final generator and exhausts the requested period at seed 0.

## D8 — Solve records and exposure

The pre-repair blind task was solved before source exposure and recorded `earlier-exposure=no`, `reference-consulted=no`. The post-repair task uses the final generator hash, passed 7/7 visible examples, and honestly records `earlier-exposure=yes`, `reference-consulted=no`.
