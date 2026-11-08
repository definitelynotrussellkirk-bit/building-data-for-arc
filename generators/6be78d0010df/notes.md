# Working notes: 6be78d0010df

## Current rule

Two full-height color-1 columns split a grid into three equal square panels. Crop each panel independently. A and B must have the same cropped nonzero mask, and corresponding cells define a consistent injective color map. Apply that map to the cropped C object.

## Current generator decisions (v3.0.0)

- Advertise only four observable controls: `panel_n=4..7`, `n_colors_used=2..4`, `analogy_alignment=aligned|shifted`, and `mapping_order=monotone|nonmonotone`.
- Use disjoint source/target palettes and make C use every source color, so every mapping role is demonstrated and queried.
- Build connected snake-like objects in adjacent same-color pairs. This reversed the first v3 draft, which colored cells individually and created many singleton color components outside the canonical marker-count support `{0,2}`. The retained regression requires every generated role to own an adjacent pair.
- Use a four-draw cyclic curriculum: canonical-size shifted/nonmonotone anchor, aligned/monotone, shifted/monotone, aligned/nonmonotone. Every four consecutive default draws therefore contain a canonical-profile case and witnesses against both declared shortcuts.
- Reject malformed grids structurally: exact dividers and panel geometry, nonempty crops, equal A/B masks, consistent injective mapping, disjoint palettes, and complete C source coverage.
- Pin canonical rule hash `20d652a9b458`. The selected base file's `target_code` was changed only to the already-identical `raw_code` text (comments removed); canonical behavior and executable rule logic were not changed.

## Reversed prior choices

The imported v2.0.1 generator declared eight controls, but `palette_kind`, `palette_size`, `position_bias`, `n_distinct_colors`, `density`, and helpful `texture` values were inert; some declared `panel_n` and `n_colors_used` values were rejected by difficulty-local draw bounds. It also advertised `no_dividers`, `identity_recolor`, and `no_C_content` degenerates, even though the selected rule crashes or becomes uninformative on them, and `self_check` explicitly accepted a no-divider grid. Those declarations were removed rather than simulated.

The imported sampler always placed A and B at the same coordinates and used an unconstrained random palette pairing. The current sampler makes alignment and mapping order explicit, observable axes and schedules both distinguishing cases.

## Evidence and limits

- Final task-local tests: 32/32 pass (`checks/task-tests/`).
- Final battery: 11/12 green; the only non-green stage is the semantic gate's procedural demand for separate schedule enumeration. All semantic facts passed. The required production census found 0/300 ambiguous lessons and 0/1500 ambiguous query rotations; the fixed-period census found 0/12 ambiguous starts and 0/60 ambiguous rotations.
- The finite checks cover the declared rivals `aligned_panels_only` and `sorted_palette_mapping`; they are not a proof against every possible hypothesis.
- Shapes are connected paired-cell snakes, mappings are non-identity and injective with disjoint source/target palettes, and the schedule period was exhaustively enumerated only at seed 0. These are deliberate current domain limits, not claims about all lawful inputs.
- Prior accepted review `review-2b98f7290646e283:v0001` supplied the no-divider and ignored-override leads; all final measurements were rerun on the selected baseline and final source.
## Current reviewer considerations

Source SHA-256: `28ea8292ac8ebfcf7b31796d45e139ec0f326aa9f1b36dce6e65d6a8a3c3f6e5`.

# Decision ledger — 6be78d0010df

## D1 — Replace the eight-axis metadata surface with four observable controls

**Prior choice and rationale.** v2.0.1 declared `panel_n`, `n_colors_used`, `palette_kind`, `palette_size`, `position_bias`, `n_distinct_colors`, `density`, and `texture`. No design rationale was documented beyond generic combinatorial variation.

**Probe.** The before override gate found inert axes, missing keyed provenance, accepted unknown keys, and 390 declared/default generation errors. Prior retained evidence at `repo/generators/6be78d0010df/counterexamples/review-2b98f7290646e283-v0001/retained/checks/audit_6be78d0010df_ignored_overrides.json` independently showed output equality under several advertised overrides.

**Decision.** Keep only `panel_n`, `n_colors_used`, `analogy_alignment`, and `mapping_order`. Validate types/ranges before construction, reject unknown keys, and expose `observe_overrides` so every value is recoverable from pixels.

**Alternatives rejected.** Keeping inert labels as “future axes” would preserve a false public contract; inventing hidden metadata-only variation would still not be observable in the grid.

**Limit.** The four controls are not a claim that they span every lawful analogy scene.

## D2 — Remove all advertised degenerate textures

**Prior choice and rationale.** v2.0.1 advertised `no_dividers`, `identity_recolor`, and `no_C_content`; comments described them as rule-degenerate examples. `self_check` explicitly returned success for a grid with no full-height divider.

**Probe.** The selected Racket rule crashes on the retained no-divider example (`length` contract violation). Empty C and identity mapping are either undefined/uninformative for teaching and were not supported by the canonical distribution.

**Decision.** Set both texture lists empty and reject `texture` as an unknown override. The generator now emits only lawful, informative examples.

**Alternative rejected.** Teaching invalid inputs with synthetic labels would change the task rather than improve its sampler.

## D3 — Make panel size and palette size exact across all bands

**Decision.** `panel_n` supports every integer 4..7 and `n_colors_used` every integer 2..4 in easy, medium, hard, and default bands. Without overrides, each band has narrower defaults, while the phase-0 schedule anchor is canonical-size (`n=6`, two source colors).

**Probe.** The final override gate and task-local parameterized tests cover both domain endpoints in every band. The profile-floor stage finds canonical-size/palette support in each 20-draw band sample.

**Failure mode considered.** A small panel with four colors can be overfull. The paired snake constructor chooses only bounding boxes with at least two cells per role; unsupported combinations fail internally rather than returning malformed grids.

## D4 — Use disjoint, injective source and target palettes

**Decision.** Draw `2*n_colors_used` distinct non-divider colors, split them into source and target palettes, and map one-to-one. C uses every source color.

**Reason.** This makes the analogy fully observable, prevents identity-map ambiguity, and ensures every learned mapping matters to the query.

**Alternative rejected.** Allowing overlapping/identity roles can be lawful in a broader abstract rule, but would weaken lesson identifiability without adding a needed canonical behavior.

**Limit.** The current domain does not teach partial, many-to-one, or identity mappings.

## D5 — Add independent A/B placement as a first-class axis

**Prior choice.** v2.0.1 wrote A and B at identical coordinates.

**Problem.** Every canonical pair also permits the shortcut “align raw panel coordinates; do not crop each panel independently.”

**Decision.** `analogy_alignment=shifted` chooses distinct legal offsets, while `aligned` deliberately preserves the simpler case. The `independent_panel_offsets` witness and `aligned_panels_only` rival are executable and source-bound.

**Evidence.** `checks/primary-shortcut-witnesses.json`; semantic gate 60/60 checked witness/rival claims held.

## D6 — Make mapping order explicit and schedule non-monotone cases

**Problem.** Pairing sorted source and target colors is a plausible rank shortcut and fits the four canonical training demonstrations.

**Decision.** `mapping_order=monotone` pairs sorted palettes; `nonmonotone` rotates the sorted target palette, guaranteeing disagreement for at least two colors. Both modes remain observable from A/B pairs.

**Evidence.** `checks/primary-shortcut-witnesses.json`; semantic gate 60/60 nonmonotone witness claims refuted `sorted_palette_mapping`.

## D7 — Use paired-color connected snakes, not arbitrary individually colored cells

**Initial v3 choice.** The first repair draft built connected masks but assigned individual cells to colors. It passed functional tests, yet defect lint found many singleton same-color components unlike canonical structural support.

**RED probe.** `checks/task-tests-marker-red/checks/task_tests.xml` contains the failing marker-support regression.

**Decision.** Traverse a rectangular snake in adjacent cell pairs; assign at least one adjacent pair to every palette role and optionally repeat roles by pair. This keeps objects connected and generated singleton-component counts within canonical support `{0,2}`.

**GREEN evidence.** Final 32/32 task tests and clean defect lint.

**Limit.** Shape topology is still a bounded snake family, not arbitrary connected polyominoes.

## D8 — Centralize structural analysis and use it for validation, observation, and the Python mirror

**Decision.** `_analyse` parses divider geometry, panels, crops, masks, mappings, palette relations, offsets, and query coverage. `self_check`, `observe_overrides`, `rule_mirror`, strict-profile classification, witnesses, and rivals consume those facts.

**Reason.** The old checker only counted full-height color-1 columns and could accept illegal inputs. One parser reduces disagreement between validation and semantic tooling while the task tests retain an independent oracle for output checking.

**Probe.** Mutations cover broken/extra dividers, A/B mask mismatch, inconsistent maps, foreign C colors, empty C, ragged grids, booleans, and the retained no-divider counterexample.

## D9 — Use a deterministic four-draw teaching schedule

**Decision.** The cycle is: canonical-size shifted/nonmonotone; band-sized aligned/monotone; band-sized shifted/monotone; band-sized aligned/nonmonotone. Four demonstrations are required.

**Reason.** Every cyclic four-example window includes a strict-profile anchor, a shifted-placement witness, and a non-monotone mapping witness. Random independent sampling would leave substantial probability that a full lesson never refutes one shortcut.

**Evidence.** Task-local cyclic-start tests; production census 300/300; fixed-seed period census 12/12 starts across three bands; all production and rotated-query checks unambiguous against declared rivals.

**Limit.** Fixed-period enumeration is at schedule seed 0 only; random census covers 100 lessons per band but does not prove all seeds or undeclared rivals.

## D10 — Synchronize selected authority text without changing rule behavior

**Prior state.** `raw_code` and `target_code` differed only by comments, producing two exact/whitespace authority hashes while execution parity passed.

**Decision.** Set selected `target_code` byte-for-byte equal to its existing `raw_code`. The canonical program and executable logic were not edited; rule hash remains `20d652a9b458`.

**Evidence.** Final `authority_sync` green; final authority-set SHA-256 `62f39e8e25aeb41f4b52d02458b1c27029947b9b854d08d9f8b607f715b03233`.

## D11 — Treat the semantic battery warning as a required external follow-up, not hide it

**Observation.** The semantic stage passed canonical acceptance, strict rate, witnesses, rivals, 12/12 lessons, and 60/60 rotations, but returns warning/failure solely because a declared period must be enumerated separately.

**Decision.** Retain honest `LESSON_SCHEDULE_PERIOD=4`, run both mandated censuses, and report the aggregate as 11/12 plus completed follow-up rather than removing metadata to obtain a cosmetic 12/12.

**Evidence.** `checks/after/checks/6be78d0010df_after_semantic_gate.json`, `checks/lesson-census.json`, `checks/schedule-census.json`.

## D12 — Replay the generated patch in a fresh packet before return

**Decision.** Build the compact return once, extract its exact `patches/source.patch`, freshly extract the original packet, initialize Git at that fresh `WORK/` directory, run `git apply --check` and `git apply`, then verify every changed path by SHA-256.

**Evidence.** All five path hashes match the reviewed workspace, including final generator SHA-256 `28ea8292ac8ebfcf7b31796d45e139ec0f326aa9f1b36dce6e65d6a8a3c3f6e5`. Fresh task tests pass 32/32, and fresh `lint`, `defect_lint`, and `authority_sync` stages pass. See `checks/fresh-replay/replay.json`.

**Interrupted attempt.** The first fresh `defect_lint` foreground call lost its command transport after writing a `running` receipt; no child remained. That receipt is retained, and the stage was rerun in a new output directory to an exit-0 pass.
