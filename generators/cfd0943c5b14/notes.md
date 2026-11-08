# Working notes: cfd0943c5b14

## 2026-10-05 review `review-160f5ad2f553b47e`

The retained unverified audit `review-02d147bb3756aa81:v0001` was used as a lead. It showed that baseline v2.0.1 excluded color 8 even though the authority treats every nonzero cell as a seed, allowing an `ignore_cyan_seed` shortcut to fit all canonical pairs and sampled defaults. The current packet's own before battery then measured four failing and two advisory stages.

The generator was rewritten as v3.0.0 with four exact axes and a five-scene cyclic curriculum. The Racket rule and canonical data were left unchanged. The repair declares three canonical-fitting rivals, four witnesses, a four-demo lesson contract, strict canonical support, exact override observation, and strict validation.

Test-driven iterations retained under `checks/tdd/` found two non-obvious causal defects:

1. A boundary anchor could be completely covered by interior stamps.
2. A cyan anchor in a dense mixed scene could contribute no unique output cell, allowing `ignore_cyan_seed` to survive six held-out rotations.

Both anchors now have a causally unique center. The final independent probe reports 300 lawful draws, 289 distinct inputs, 1,500 cyclic rotations, zero ambiguities, and zero errors. The final shared lesson census reports 300 lessons, 1,500 labelled pairs, 1,282 unique inputs, and zero production or rotation ambiguities against the declared competitors.

Final generator SHA-256: `13dfe4aa92dde9c041beebd84b91914e47ca6891dfdb896f6b8e57e7b6d7e194`.
## Current reviewer considerations

Source SHA-256: `13dfe4aa92dde9c041beebd84b91914e47ca6891dfdb896f6b8e57e7b6d7e194`.

# Decisions for `cfd0943c5b14`

## D1 — Keep the Racket authority unchanged

- **Choice:** Pin `RULE_HASH = "6e86df413712"` and repair only the Python generator, contracts, tests, and task documentation.
- **Original rationale:** The authoritative transformation already implements the intended law: every nonzero cell paints a clipped cyan diagonal X on a fresh grid.
- **Alternatives considered:** Rewrite the Racket rule; alter canonical examples; narrow the rule to non-cyan seeds to match the old sampler.
- **Probes:** Before and after rule smoke, independent Python mirror comparisons, final authority sync, and canonical pair checks.
- **Reason:** The defect was distributional and contractual, not a wrong label function. Narrowing the rule would have encoded the sampler bug into the authority.
- **Limit:** Correct authority labels do not by themselves make a lesson identifiable.

## D2 — Replace misleading axes with four exact observable controls

- **Choice:** Expose only `grid_h`, `grid_w`, `seed_count`, and `scene`.
- **Original rationale:** The baseline declared `grid_h/grid_w` while drawing `height/width`, aliased `texture` to palette controls, advertised degenerate textures, and allowed difficulty to change legality.
- **Alternatives considered:** Repair every legacy axis; preserve aliases for compatibility; expose seed colors/coordinates as exact axes.
- **Probes:** Public `observe_overrides`, strict unknown-key/type/range tests, exhaustive legal joint overrides at 6×6, and the repository override gate.
- **Reason:** Four controls describe actual returned pixels and are sufficient for reproducible curriculum construction without a combinatorial coordinate API.
- **Failure modes / limits:** Seed positions and colors are intentionally sampled within a scene rather than exposed as public exact controls.

## D3 — Use a deterministic five-scene curriculum

- **Choice:** Cycle `canonical`, `edge_seed`, `mixed_overlap`, `corner_seed`, and `cyan_interior` by `sample_index mod 5`.
- **Original rationale:** A free random sampler did not guarantee that a complete lesson challenged color, boundary, and overlap shortcuts.
- **Alternatives considered:** Pure Monte Carlo with resampling; one over-constrained universal witness scene; separate hard-coded lessons outside the generator.
- **Probes:** Shared 300-lesson census, all five held-out rotations, 100 cyclic starts per band in the independent probe, and `schedule_profile` tests.
- **Reason:** A short periodic schedule is cheap to exhaust and guarantees broad support without requiring every grid to contain every feature.
- **Failure modes / limits:** Ordered scheduling is part of the data contract; arbitrary nonconsecutive assembly should rerun identifiability checks.

## D4 — Give boundary and cyan witnesses a unique causal pixel

- **Choice:** Prevent other seeds from stamping the designated boundary/cyan anchor center.
- **Original rationale:** The first rewrite placed the right feature but sometimes let other X footprints cover all of its output contribution. A rival could therefore ignore the nominal witness and still match the label.
- **Alternatives considered:** Merely assert witness predicates; reduce hard-mode seed counts; reject overlaps entirely.
- **Probes:** The first contract probe found six hard-mode rotation ambiguities. A targeted failing test then required removal of the cyan anchor to change the output in 100 hard mixed scenes; after the repair, 1,500 cyclic rotations were clean.
- **Reason:** Training value comes from causal counterexamples, not feature presence alone. Preserving overlaps still teaches the union branch.
- **Failure modes / limits:** Unique contribution is enforced for the scheduled anchor, not for every seed in every scene.

## D5 — Use four demonstrations and test every query position

- **Choice:** Set `EXAMPLES_NEEDED = 4` and form lessons from five consecutive scene slots, holding out one as the query.
- **Original rationale:** Three demonstrations could not simultaneously guarantee canonical presentation plus color, boundary, and overlap evidence under arbitrary query rotation.
- **Alternatives considered:** Keep three demos; use five demos; support only a fixed query position.
- **Probes:** Semantic-gate rotation smoke (60/60), shared lesson census (1,500/1,500), and independent exhaustive schedule probe (1,500/1,500).
- **Reason:** Four demos are the smallest clean complement of a five-scene schedule and remain compact.
- **Failure modes / limits:** The checks cover the declared three rivals, not every possible program consistent with four examples.

## D6 — Preserve canonical support with an honest 18% strict floor

- **Choice:** Alternate exact 8×8/9×9, two-color-3-seed canonical scenes while allowing broader 6..12 canvases and 2..5 seeds elsewhere; declare `MIN_STRICT_FRAC = 0.18`.
- **Original rationale:** Training needs both canonical-distribution overlap and counterexamples outside the tiny canonical manifold.
- **Alternatives considered:** Make every sample canonical-like; declare a 20% floor despite a measured 19.5%; remove a strict floor.
- **Probes:** Final semantic audit measured 117/600 strict hits (19.5%); profile-floor audit found 34 exact hits in 60 draws with support in every band.
- **Reason:** Eighteen percent is a conservative declared lower bound beneath observed deterministic evidence, not an aspirational rounded claim.
- **Failure modes / limits:** Exact hit rate depends on the deterministic seeds used by the gate and should be remeasured after any source change.

## D7 — Treat all nonzero colors as seeds and retain three canonical-fitting rivals

- **Choice:** Define competitors `ignore_cyan_seed`, `ignore_boundary_seeds`, and `only_color_three`; map them to causal witnesses.
- **Original rationale:** Each shortcut is plausible from the canonical/baseline presentation, and the retained prior audit proved the cyan shortcut survived the old distribution.
- **Alternatives considered:** Declare only the historically observed cyan shortcut; add a large speculative rival library.
- **Probes:** All three rivals fit every usable canonical pair, are refuted in every final lesson tested, and disagree on all 60 checked witness examples apiece.
- **Reason:** A small, source-owned rival contract is maintainable and directly tied to known presentation accidents.
- **Failure modes / limits:** Undeclared rivals may remain; finite rival rejection is not universal identifiability.

## D8 — Add independent task tests and reusable probes

- **Choice:** Add `tests/test_generator.py`, `workspace/reference_probe.py`, and `workspace/contract_probe.py`.
- **Original rationale:** The generic battery did not discover task tests automatically and its small semantic sample initially missed a rare causal-redundancy failure.
- **Alternatives considered:** Rely only on the generic battery; write one-off notebooks; test only the Python mirror.
- **Probes:** Tests were observed failing before implementation and after each discovered defect; final portable task-test run reports 147 passed. The contract probe uses an independent stencil oracle and tests every cyclic query rotation.
- **Reason:** Future reviewers can replay the exact hard guarantees without reconstructing ad hoc commands.
- **Failure modes / limits:** The Python oracle is independent of generator layout logic but not a substitute for selected Racket execution; Racket-backed generic gates were also retained.

## D9 — Record the post-repair solve as exposed

- **Choice:** Declare `earlier_rule_exposure = yes` and `reference_consulted_during_solve = no`.
- **Original rationale:** The solve occurred after inspecting and repairing the generator, so claiming blindness would be false.
- **Alternatives considered:** Skip the solve; claim no exposure; reopen reference material during the solve.
- **Probe:** The episode is bound to final generator SHA `13dfe4aa…`; revision 1 passed 4/4 visible demonstrations and was then frozen.
- **Reason:** This preserves useful executable evidence while keeping its epistemic status honest.
- **Failure modes / limits:** Masked-query correctness is unavailable and the episode does not measure an unexposed model.
