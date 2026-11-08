# Working notes: c782972f840b

## Review repair (version 3.0.0)

The selected 2.1.1 baseline sampled random shape/color assignments, declared controls it did not consume, omitted `RULE_HASH`, and accepted structurally unrelated grids. It also did not deliberately construct the relation branches its summary promised. Baseline evidence is retained under `checks/before-lint/`, `checks/before-defect/`, and `checks/c782972f840b_baseline_selected_tests.*`.

The repair replaces chance coverage with a constructive sampler. Every lawful draw has 4–6 separated monochrome objects, 2–3 colors, at least two rotation classes, both same-color and same-shape comparisons, and a chiral mirror pair that is dihedrally—but not rotationally—equivalent. `relation_profile=with_duplicate` adds a same-shape/same-color duplicate (matrix value 6); `without_duplicate` excludes that branch while retaining 4, 2, and 0. The exact observer `observe_overrides()` makes all advertised controls machine-checkable, and unknown/out-of-domain controls are rejected.

The canonical five pairs do not distinguish rotation equivalence from reflection equivalence: the declared `dihedral_equivalence` shortcut fits 5/5 canonical pairs. Therefore the generator declares that shortcut and an executable `mirror_not_rotation` witness. The reusable probe in `workspace/lesson_probe.py` assembles non-overlapping 3-demo/1-query lessons from the actual default sampler and tests declarations rather than a copied rival list.

## Final evidence

- Generator SHA-256: `dc8131b1802dc0d2c4495022fbab7316d1878769342c9cbbead11eb1bb2fbae8`.
- Official after battery: 12/12 stages green, including lint, strict defect lint, profile floor, exact overrides, semantic gate, and authority sync (`checks/after/result.json`).
- Focused tests: 52/52 pass (`checks/c782972f840b_selected_tests.log`).
- Lesson probe: 300 lessons, 1,200 unique inputs, zero self-check/determinism failures, zero lessons missing the witness, and the dihedral rival survives 0/300 lessons (`checks/c782972f840b_lesson_probe.json`).
- No canonical or Racket authority source was changed. Selected execution parity is green; an archival raw rule text remains divergent and is reported by authority sync as archival-only.

## Limits

The sampler intentionally stays within sparse isolated monochrome objects, a finite hand-built bank of shapes with bounding boxes at most 3×3, 4–6 objects, and 2–3 colors. The finite rival probe demonstrates rejection of declared competitors over its sampled domain; it is not a proof of universal identifiability or a model-training experiment.

Imported associated notes, if any, remain in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `dc8131b1802dc0d2c4495022fbab7316d1878769342c9cbbead11eb1bb2fbae8`.

# Design decisions for c782972f840b

## D1 — Construct relation classes instead of hoping random assignments cover them

**Baseline / rationale.** Version 2.1.1 randomly drew a small shape pool and color pool, then independently assigned pairs to objects. Its prose promised visible 6/4/2/0 relation branches, but there was no construction or validation ensuring them. The original rationale beyond “richer matrices” is not documented.

**Decision.** Build assignments from three shape classes and 2–3 colors. `with_duplicate` deliberately includes a same-shape/same-color pair (6); `without_duplicate` excludes that branch while retaining same-shape/different-color (4), different-shape/same-color (2), and neither (0). Fill any fifth/sixth object only after these teaching relations exist.

**Rejected alternatives.** Retaining random independent assignments was rejected because relation coverage is probabilistic and difficult to observe. Requiring all four off-diagonal values in every draw was rejected because it would make the advertised duplicate/no-duplicate control false.

**Probe.** `tests/test_generator.py::test_relation_profile_controls_only_same_shape_same_color_duplicates`; final battery `override`, `semantic_gate`, and `diversity`; 300-lesson probe.

## D2 — Default to the exact canonical canvas/palette profiles

**Baseline / rationale.** The baseline used difficulty-dependent rectangles that did not intentionally hit all canonical dimension/palette combinations. The five canonical inputs have profiles 12×14 with 3 colors including background, 13×15×3, 12×16×4, 14×15×3, and 13×14×3.

**Decision.** Make those five profiles the complete default `canvas_profile` support. Keep an explicit `expanded` override at 16–18×18–20 with 2–3 nonzero colors so the branch is observable and never aliases a canonical token.

**Rejected alternatives.** Free uniform dimensions were rejected because they dilute canonical support. Making expanded sizes part of the default was rejected because the profile-floor objective is canonical fidelity, not maximum canvas variety.

**Probe.** Every exact profile is parameterized in `test_every_exact_override_is_realized`; final `profile_floor` passes; the lesson probe observed all five default profiles in each difficulty band.

## D3 — Use 4–6 objects

**Baseline / rationale.** Baseline metadata said 3–4 while implementation sampled 3–6. Every canonical pair has four objects, and matrix size is itself an important output feature.

**Decision.** Use 4–6 objects: four anchors canonical support; five and six broaden matrix size without exceeding placement capacity. Difficulty only reweights the same lawful domain.

**Rejected alternatives.** Three objects were removed because there is too little room to demonstrate the mirror rival plus independent color/shape relations. More than six was rejected as unnecessary placement pressure on 12×14 canonical canvases.

**Probe.** Exact overrides test 4, 5, and 6; lesson probe observed 4–6 in every band with 1,200/1,200 unique inputs.

## D4 — Include a chiral mirror-not-rotation witness in every draw

**Baseline / rationale.** The canonical set is semantically underdetermined: a dihedral equivalence rule matches 5/5 pairs. Random polyominoes do not guarantee a reflection counterexample.

**Decision.** Seed every assignment with one of two hand-checked chiral mirror pairs (S/Z or L/J), which share a dihedral key but not a rotation key. Declare the witness and the `dihedral_equivalence` rival as executable callables.

**Rejected alternatives.** Reflection-symmetric or rotation-equivalent-only shape banks were rejected because they cannot separate the rules. Changing the canonical/Racket rule to dihedral equivalence was rejected because the selected authority is rotation-only and already passes all canonical outputs.

**Probe.** `test_rotation_is_equivalent_but_reflection_is_not`; canonical shortcut check 5/5; lesson probe records the witness in 300/300 lessons and rival survival 0/300.

**Limitation introduced.** Every generated draw contains a mirror witness. This is intentional teaching support but narrows the input distribution and could teach the incidental prior “a chiral pair is always present.” The model still must compute all pairwise labels, and shape/orientation/color/object-count/profile combinations vary, but absence-of-witness cases are not sampled.

## D5 — Use sparse isolated monochrome objects from a finite small-shape bank

**Baseline / rationale.** The rule operates on connected objects and their colors; touching or multicolor components would introduce segmentation ambiguity unrelated to the target relation.

**Decision.** Place separated monochrome polyominoes with 3–5 cells and bounding boxes at most 3×3, using two mirror pairs plus T/U/P/line third shapes. Use 2–3 nonzero colors to match canonical palette sizes.

**Rejected alternatives.** Arbitrary random walks were rejected because duplicate/dihedral class control becomes hard to prove. Touching or multicolor objects were rejected as outside canonical support.

**Probe.** Strict `self_check`, structural mutation tests, final `defect_lint`, and canonical profile checks.

**Limitation.** The finite bank does not cover large polyominoes, holes, touching components, or multicolor components. This is a documented support boundary, not a universal ARC object generator.

## D6 — Advertise only exact observable controls

**Baseline / rationale.** The baseline exposed singleton/dead axes and helpful textures it never consumed; unknown keys were silently tolerated by the context path.

**Decision.** Keep only `canvas_profile`, `n_objects`, and `relation_profile`. Validate key names and domains before generation, and provide `observe_overrides(grid)` so the battery/tests can recover every exact value from the resulting input.

**Rejected alternatives.** Keeping aliases such as palette kind, density, or position bias as decorative metadata was rejected. Diagnostic-only axes were unnecessary because each retained control has a real behavioral domain.

**Probe.** 36 cross-product exact-control tests plus invalid/unknown override tests; final override stage reports unknown-key verdict `rejected`.

## D7 — Make `self_check` semantic and structural

**Baseline / rationale.** Baseline validation required only three nonzero cells and one nonzero color, admitting solid grids, short lines, bool-valued cells, and examples with no meaningful pairwise contrast.

**Decision.** Validate rectangular integer-valued ARC grids; canonical/expanded dimensions and palette support; 4–6 isolated monochrome components; component size/bounding box; separation; color count; at least two rotation classes; the chosen relation-profile class; and a mirror-not-rotation witness.

**Rejected alternatives.** A renderer-only check was rejected because many malformed inputs still have a defined matrix. A canonical-examples whitelist was rejected because it would not validate generated diversity.

**Probe.** Parameterized malformed/impostor tests; final `selfcheck` and strict `defect_lint` pass with zero flags.

## D8 — Add a source-bound lesson probe rather than claim universal induction

**Decision.** `workspace/lesson_probe.py` loads the final generator, independent Python authority, canonical ledger, and the generator's actual semantic declarations. It assembles 100 non-overlapping 3-demo/1-query lessons per band using seeds `910000 + band_index*100000 + lesson_index` and sample indices `lesson_index*4 .. +3`.

**Rejected alternatives.** Counting witness frequency per individual row was rejected because it does not prove complete lessons identify the rule. Copying a list of rival names into the probe was rejected because declarations and tests could drift. Treating 300 sampled lessons as a proof was rejected.

**Probe result / limit.** Final SHA `dc8131b…fbae8`: 300 lessons, 1,200 unique inputs, 518 unique outputs, zero self-check or determinism failures, zero missing-demo-witness lessons, and zero rival survivors. This is finite evidence over the documented domain, not universal induction or a Qwen training evaluation.

## D9 — Leave Racket/canonical authority unchanged

The selected rule already produces all five canonical outputs and the repaired independent Python oracle agrees. No canonical row, base rule, or Racket source was edited. Final authority sync reports selected execution parity `PASS`; an archival raw source remains textually divergent but behaviorally matched on the tool's sample.

## Native parametric review — 2026-10-25

Built a source-bound `equivalence_policy` family without changing the approved
production generator or canonical authority. `rotation` is the exact canonical
Racket program; `dihedral` extends shape equivalence to rotations plus reflection.
Inputs are setting-neutral, support 2–6 demonstrations and 1–4 prefix-stable
queries, and include 16×18, 20×22, 24×27, and 30×30 query canvases. The first two
demonstrations separate the settings and refute the retained finite rival set.

The required dependency is substantive: object crops are canonicalized into an
ordered vector of transformation-orbit class IDs, and the relation-matrix renderer
consumes equality of those IDs together with color equality. The protected witness
replaces dihedral IDs with rotation-only IDs and changes mirror-pair matrix cells.

Retained evidence: 60 focused parametric tests; 112 complete task tests; a
12-episode audit with 92 selected labels, 96 rival checks, and no findings; native
qualification for 2 settings × seeds 0/17 with 40 protected-Racket evaluations;
16 verified one-query public views; and a protected causal replay. Inventory
SHA-256 is `56c26c0214b7d7d25be998b64fb7d21027e537323c58db89679f93053a30185e`.
Owner exact-source integration and acceptance remain pending; no training
admission is claimed.

