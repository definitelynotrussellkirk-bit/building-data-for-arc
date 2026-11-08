# Working notes: fa55db418c9d

## Final source identity

- Generator version: `3.0.1`
- Generator SHA-256: `abba270cc9ed0ffffa6b6f8a11e9ba6070a42ffe4768153ecd846f1fec0235d2`
- Canonical rule hash: `eeee12543bcc`
- Canonical Racket authority changed: **no**

## Baseline defects reproduced

1. The old validator rejected three lawful canonical examples because it treated the generator’s isolation/count preferences as rule-domain requirements.
2. Most advertised axes were inert or fictional, including texture/palette controls.
3. There was no pinned `RULE_HASH` and no executable shortcut/lesson contract.
4. The generated distribution did not explicitly refute the strongest plausible canonical shortcut: treating every blue three-cell component as a target.

Retained evidence is under `checks/before-fast/`, `checks/before-command.log`, and `checks/baseline-source/` in the review return.

## Repair decisions

### Component semantics

The validator now parses exact-color cardinal components and recognizes an L only as three cells in a `2×2` bounding box. It does not require the generator’s visual moat and does not impose a fixed number of targets. This accepts all five canonical pairs while preserving the exact task rule.

### Five-profile linked schedule

A five-example lesson was selected because one cycle can guarantee every orientation plus independent shape, color, and border counterexamples. The profile index is `sample_index % 5`, so every cyclic start of five consecutive examples contains the full set. Difficulty does not perturb the semantic profile order.

Rejected alternative: independent random feature sampling. It produced good marginal frequencies but could leave complete lessons compatible with size-only, all-blue, all-L, orientation-omission, or ignore-edge rivals.

### Decoys

- Profile 0: canonical-scale anchor, size-six blue decoy, color-6 and color-7 line decorations.
- Profile 1: blue straight triomino, the exact witness against the canonical-fitting size-three shortcut.
- Profile 2: blue square.
- Profile 3: size-six blue rectangle.
- Profile 4: blue long-L tetromino.
- Profiles 1–4: one non-blue exact L.

Rejected alternative: singleton/domino-only blue distractors. They do not refute the strongest size-three shortcut.

### Controls

The old broad axis list was replaced with six controls that are both constructible and observable. Every Cartesian combination of exact boundary values is covered by a focused regression across all three bands. Unknown controls reject instead of silently becoming metadata.

### Placement

Backtracking placement with a cardinal moat replaced ad hoc random retries. The moat avoids accidental same-color merging in generated scenes. It is intentionally absent from validation because the canonical domain permits different-colored contact.

### Palette drift iteration

The first repaired version emitted only three input colors. `dist_gate` correctly reported `canonical_palette_unreachable: gen=3..3 vs canon=4`. A failing regression was added before changing profile 0’s second decoration from 7 to 6. Version `3.0.1` reaches `{0,1,6,7}` and the focused distribution gate passes. The failed gate remains retained as evidence.

## Measured final curriculum

`workspace/curriculum_probe.py` labels with the actual canonical Racket rule and inspects 100 lessons per band. Its final `3.0.1` run contains 1,800/1,800 unique generated inputs (600 per band), zero generation or Racket/mirror failures, and zero lesson-identifiability failures. Every one of the 100 lessons in each band refutes all eight declared competitors. All five schedule residues occur 20 times per band.

This is a finite census of the exact sampler recorded in the report. It does not establish universal induction beyond the generated default domain.

## Tools

- `workspace/curriculum_probe.py`: source-bound 100-lesson-per-band Racket-labelled rival census; reads rival/witness declarations from the generator rather than duplicating names.
- `workspace/audit_probe.py`: source-bound adversarial reproducer for the immutable audit targets, including actual Racket outputs and exact source hashes.
- `tests/test_generator_fa55db418c9d.py`: semantic, axis-boundary, canonical, rival, lesson, replay, and palette regressions.
- `tests/test_audit_probe.py`: pure helper regressions for the disconnected-template audit reproducer.

## Remaining limitations

- Default lessons follow a deterministic five-profile grammar; a learner could identify that schedule itself. Semantic checks therefore score task-rule rivals against outputs, not novelty of profile order.
- Generated scenes do not exhaust every lawful component arrangement, adjacency pattern, grid size, or palette combination.
- `rule_mirror` exists only for tests and probes. Canonical Racket remains authoritative.
## Current reviewer considerations

Source SHA-256: `abba270cc9ed0ffffa6b6f8a11e9ba6070a42ffe4768153ecd846f1fec0235d2`.

# Decisions and trade-offs

## D1 — Treat component semantics as the rule boundary

**Input choice.** Validation accepts rectangular ARC grids whose nonzero cells can be partitioned into exact-color, four-connected components. Targets are only blue, exactly three-cell, `2×2` L components.

**Original rationale.** The canonical Racket authority and all five public pairs operate at the same-color component level. The previous validator instead embedded generation preferences: fixed counts, a halo, and assumptions about allowed contacts. That rejected lawful canonical rows.

**Alternatives considered.** Retain a strict isolated-object grammar; special-case the canonical rows; or weaken validation to little more than shape checks. The first two confuse sampling policy with task law, while the third would admit merged blue structures without classifying them correctly.

**Probe.** All five canonical pairs pass `self_check`; the canonical Racket output and independent mirror agree. Generated placements still use a cardinal moat, but validation does not require it.

**Failure modes and limits.** This validator recognizes the task’s component law but does not claim every lawful scene is pedagogically useful. Cross-color contact is accepted; same-color contact can merge components and thereby change their classification, as intended.

## D2 — Use a deterministic five-profile curriculum

**Input choice.** `sample_index % 5` selects one canonical anchor and four contrast profiles. Five consecutive demonstrations contain all orientations, shape counterexamples, a color counterexample, and an edge case.

**Original rationale.** The task has multiple independent ambiguities. Marginally frequent witnesses do not guarantee that one lesson refutes every rival. A linked schedule makes lesson-level support testable.

**Alternatives considered.** Independent random profiles; a longer schedule; or injecting every witness into every grid. Independent sampling leaves unlucky lessons ambiguous, a longer cycle would require more demonstrations, and all-in-one grids are cluttered and reduce useful morphological variation.

**Probe.** `lesson_identifiable` checks each complete lesson. The final source-bound census tested 100 lessons per band and all five start residues: zero failures, and each of eight competitors was refuted in 100/100 lessons per band.

**Failure modes and limits.** The deterministic schedule is itself learnable and only covers its declared finite grammar. The evidence establishes rival separation for emitted lessons, not universal human or model induction.

## D3 — Include a straight blue triomino as the critical negative

**Input choice.** Profile 1 contains a blue horizontal or vertical straight triomino that must remain blue.

**Original rationale.** “Recolor every blue size-three component” fits all five canonical pairs and is therefore the strongest simple canonical shortcut. A straight triomino isolates the missing shape predicate while keeping color and size unchanged.

**Alternatives considered.** Singleton, domino, square, or larger blue decoys. Those refute “recolor every blue component” but not the more precise size-three shortcut.

**Probe.** The exact generated witness is saved in `checks/generator-shortcut-counterexample.json`. Actual Racket leaves the straight triomino as `1`; the rival changes it to `2`. The final census contains 120 such disagreements in each 600-grid band.

**Failure modes and limits.** The rival’s arbitrary default output color for a non-L shape is one concrete extension. Any rival that changes a blue straight triomino is refuted by the same unchanged Racket output.

## D4 — Use independent shape, color, orientation, and border contrasts

**Input choice.** The schedule includes four blue non-L families, a non-blue L in profiles 1–4, all four target orientations, and edge-touching targets in profiles 2–3.

**Original rationale.** Each feature targets a distinct shortcut: all-blue, all-L-regardless-of-color, one-orientation omission, or ignoring border objects.

**Alternatives considered.** Decorative noise with no relation to the rule, or only varied target counts. Neither provides a labeled counterexample to the named rivals.

**Probe.** Executable `SEMANTIC_WITNESSES`, `WITNESS_RIVALS`, and `LESSON_COMPETITORS` are checked both by focused tests and the actual-Racket probe. Every witness fires in all bands, and every declared witness has at least one named rival that disagrees with truth.

**Failure modes and limits.** The competitor set is explicit, not exhaustive. Unknown more complex shortcuts may remain.

## D5 — Advertise only six exact, observable controls

**Input choice.** Keep `grid_h`, `grid_w`, `n_target_l`, `n_blue_decoys`, `n_colored_l_decoys`, and `target_position`; reject unknown keys and difficulty names.

**Original rationale.** The old generator advertised many controls it ignored. An axis is useful only if exact requests are constructible, observable, and independently testable.

**Alternatives considered.** Preserve legacy palette/texture aliases for compatibility, or advertise hidden profile identity. The aliases would remain semantically vague; direct profile control would let callers accidentally assemble weak lessons and duplicate the meaning of the observable axes.

**Probe.** The focused regression exhausts the Cartesian product of every lower/upper or enum boundary across easy, medium, and hard. The official override gate evaluates the full declared matrix.

**Failure modes and limits.** Exact overrides intentionally suppress hidden canonical decorations so the smallest `9×10` boundary remains feasible. An overridden profile need not remain a canonical anchor; it must remain lawful and match the requested observables.

## D6 — Use bounded backtracking and a generation-only moat

**Input choice.** Candidate placements are enumerated and shuffled deterministically, then solved by bounded backtracking with a one-cell cardinal moat.

**Original rationale.** Random retry placement can fail silently or bias later objects. Backtracking makes requested object counts reliable, including dense boundary combinations.

**Alternatives considered.** Fixed slots, unbounded rejection sampling, or allowing generated components to touch. Fixed slots make positions predictable; rejection sampling has unstable tails; touching risks accidental same-color mergers that invalidate exact controls.

**Probe.** Boundary Cartesian tests, official override testing, deterministic replay checks, and self-check all pass. A node bound fails loudly rather than returning an underfilled grid.

**Failure modes and limits.** The moat narrows the generated adjacency distribution. Because it is not a validator requirement, it does not redefine the canonical rule domain.

## D7 — Reach the full canonical palette in the strict anchor

**Input choice.** Profile 0 uses one color-7 line and one color-6 line, giving palette `{0,1,6,7}`.

**Original rationale.** The first repaired source used two color-7 lines. The diagnostic distribution gate then proved that generated palettes were always size three while a canonical input has four colors.

**Alternatives considered.** Dismiss the marginal gate because semantic gates already passed, randomize both decoration colors, or add another public palette axis. The gap was cheap to close deterministically; randomization would weaken the strict profile floor; a new axis was unnecessary.

**Probe.** A failing test first reproduced `{0,1,7}` instead of `{0,1,6,7}`. After the single-color change, the focused test and `dist_gate` passed. The failed intermediate gate is retained under `checks/after-fast/dist_gate-retry/`.

**Failure modes and limits.** One strict profile reaching the largest canonical palette does not reproduce every palette/layout correlation in the canonical set.

## D8 — Keep Racket authoritative and Python mirrors test-only

**Input choice.** No canonical Racket source changed. `rule_mirror` exists for regressions and probes; actual-Racket labeling is used for retained evidence.

**Original rationale.** The defect was in generator distribution, validation, and contracts, not in the canonical outputs. A Python mirror accelerates focused tests but should not silently replace the authority.

**Alternatives considered.** Patch Racket to match a narrower generated grammar, or rely only on the Python mirror. Both would weaken source binding.

**Probe.** Rule smoke, Racket lint, authority sync, canonical output checks, and the source-bound curriculum probe compare the declared hash and actual outputs.

**Failure modes and limits.** A mirror can share a conceptual mistake with a generator; that is why final evidence also executes canonical Racket.
