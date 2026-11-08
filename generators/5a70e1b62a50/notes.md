# Working notes: 5a70e1b62a50

## Repair summary

Baseline source `9daa2d97f0d3f64b3a825ff60b3e7fbc26657cc560c0346c202451c016bde602` taught rectangle completion and exposed a large inaccurate override surface. The strongest plausible shortcut—fill one global bounding box per color—fit all five labeled canonical pairs and every ordinary baseline lesson.

The selected `3.0.0` source (`24cb3ea5fe87b5e6e35116d353e6733940913bf3d31c95e85e07c7fe58e3dddb`) preserves Racket rule hash `92650211204a` and exposes only an exact `profile` axis. The four-slot schedule is:

1. `canonical_rectangle`
2. `irregular_enclosure`
3. `shared_color_pair`
4. `closure_contrast`

`EXAMPLES_NEEDED = 3`, so every contiguous three-demo window contains a generated bbox counterexample. The next item is the production query; all four held-out query rotations are also checked by the large census.

## Evidence

- Before battery: 7 green, 2 advisory, 3 failed.
- After battery: 12/12 green.
- Final selected tests: 44/44 passed.
- Semantic gate: 454/600 bbox counterexamples; 12/12 lessons and 48/48 diagnostic rotations identifiable.
- Large Racket-labelled census: 300/300 production lessons, 1,200/1,200 rotations, 1,146 unique inputs.
- Retained source-bound probe: 384 draws, 312 contiguous windows, zero surviving declared rivals.

The prior accepted review `review-c75b3c20a8a6e96a:v0001` (source SHA `9daa2d97f0d3f64b3a825ff60b3e7fbc26657cc560c0346c202451c016bde602`) supplied the shortcut lead; all current counts were remeasured in this packet.

## Remaining limitations

The sampler intentionally uses one wall color and five canonical canvas dimensions. The finite declared rival set contains the global-bbox shortcut; passing it does not prove identifiability against every possible hypothesis. The deterministic periodic schedule is visible, although semantic checks do not rely on hiding it.
## Current reviewer considerations

Source SHA-256: `24cb3ea5fe87b5e6e35116d353e6733940913bf3d31c95e85e07c7fe58e3dddb`.

# Design and review decisions for 5a70e1b62a50

## D1 — Preserve the canonical authority

**Original rationale/evidence:** The canonical Racket rule already implements the more general and coherent topology: fill an enclosed zero region when it does not touch the border and has exactly one neighboring nonzero color. The baseline failures were in the sampler and contract, not a demonstrated authority error.

**Decision:** Keep rule hash `92650211204a` unchanged and repair only selected generator files.

**Rejected alternatives:** Replacing the authority with rectangle completion would validate the shortcut instead of fixing it; changing canonical data would exceed the assignment and erase the intended topology.

**Probe:** Before/after battery authority-set SHA is unchanged (`d8e03941f596c665817a118685265cfc242c7c4f257e6660a57c86c12ac9e28b`), and `authority_sync` is green.

**Limitation:** The Python `rule_mirror` is diagnostic code, not a label authority.

## D2 — Replace nine inaccurate axes with one observable semantic profile

**Original rationale/evidence:** The historical rationale for the nine-axis metadata is not retained. Measured behavior showed dead `texture` values, unprobeable single-token axes, dimension overrides inconsistent with difficulty bands, silently ignored axes, and accepted unknown keys.

**Decision:** Expose only `profile`, whose four values can be reconstructed exactly by `profile_signature` and `observe_overrides`.

**Rejected alternatives:** Keeping cosmetic aliases would preserve misleading API surface; marking all dead axes diagnostic would hide rather than repair the mismatch.

**Probe:** The final override matrix accepts 450/450 requested cases with zero findings; task tests cover every profile in every band, bad types, and unknown keys.

**Limitation:** Callers that depended on the old undocumented override behavior must migrate to `profile`.

## D3 — Teach four rule-relevant profiles

**Original rationale/evidence:** Rectangle-only examples admit global bounding-box completion. A useful curriculum must distinguish enclosure from rectangle shape, object count, and mere near-closure.

**Decision:** Use `canonical_rectangle`, `irregular_enclosure`, `shared_color_pair`, and `closure_contrast`.

**Rejected alternatives:** More rectangle colors or sizes increase visual diversity without breaking the rival. Open-only negative scenes were rejected because every ordinary input should still contain a positive enclosed region.

**Probe:** Semantic witnesses fire in all bands; the semantic gate observes profile counts `146/135/164/155` across 600 draws and no missing branch.

**Limitation:** These four profiles are not an exhaustive basis for every topology accepted by the authority.

## D4 — Use a deterministic four-slot schedule

**Original rationale/evidence:** Random independent profile draws can create a three-demonstration lesson containing only canonical rectangles, allowing the rival to survive by chance.

**Decision:** Map `sample_index % 4` to the four profiles, independent of seed and band. Set `EXAMPLES_NEEDED = 3`; every three consecutive demonstrations include at least one rival counterexample, and the next item is the production query.

**Rejected alternatives:** Weighted random sampling could satisfy pooled frequencies while leaving unlucky lessons ambiguous. Forcing all four profiles into the demonstrations would require four demos and enlarge every lesson unnecessarily.

**Probe:** Tests enumerate every three-demo window over multiple seeds and bands. The retained probe checks 312 windows with zero surviving declared rivals; the large census passes 300 production lessons and all 1,200 query rotations.

**Limitation:** The periodic ordering is learnable metadata. It is acceptable here because semantic identifiability is checked independently of predicting the schedule.

## D5 — Add same-color double holes as the exact bounding-box discriminator

**Original rationale/evidence:** Two separated frames of distinct colors do not break a per-color bounding-box rule. Two separated holes of the same color do: the intended rule fills each interior but leaves the exterior gap zero, while the rival fills the global gap.

**Decision:** Generate two separated 3×4 same-color rectangular walls for `shared_color_pair`.

**Rejected alternatives:** A 3×3 pair changed only two cells and triggered transformation-drift warnings because the lesson barely displayed the output change. Larger walls reduced placement diversity on canonical canvases.

**Probe:** `checks/question/5a70e1b62a50/` contains the exact authority/rival disagreement; the semantic gate counts 454/600 bbox counterexamples.

**Limitation:** The pair is always same-colored and separated by at least one-cell Chebyshev clearance.

## D6 — Include an irregular enclosure and a closed/open contrast

**Original rationale/evidence:** Same-color pairs refute one shortcut but do not by themselves show that rectangularity is irrelevant or that closure, rather than visual U-shape interior, controls filling.

**Decision:** Build connected irregular walls around small polyomino interiors, and pair a 4×4 closed wall with a transformed open U wall.

**Rejected alternatives:** Thin cardinal dilation around concave interiors could disconnect or leak at corners; Moore-neighbor dilation gives a stable connected wall. A 3×3 closed contrast again changed too few cells.

**Probe:** `self_check`, profile reconstruction, semantic witnesses, and authority-labelled gates pass across all transforms and bands.

**Limitation:** The irregular family contains four small seed polyominoes and eight dihedral transforms, not arbitrary enclosures.

## D7 — Match canonical canvas support without copying canonical scenes

**Original rationale/evidence:** Baseline hard draws had zero canonical-profile support and used dimensions outside the five canonical shapes. Coarse dimensions could become another generator/canonical split.

**Decision:** Sample exactly the five canonical canvas dimensions: `(6,10)`, `(7,8)`, `(8,9)`, `(8,10)`, `(9,9)`.

**Rejected alternatives:** A broad 6–16 range increases surface area without teaching the rule and weakened profile-floor alignment. Fixed single dimensions would create a new shortcut.

**Probe:** Tests observe all five shapes and deterministic replay; profile floor is green and canonical strict rate is `146/600 = 24.33%`, above the declared `0.20` floor.

**Limitation:** Canvas-shape support intentionally remains finite.

## D8 — Use one wall color per scene

**Original rationale/evidence:** Every canonical input uses one nonzero color, and the authority's essential distinction can be taught without introducing mixed-boundary cases whose intended status is less obvious to a solver.

**Decision:** Draw one nonzero color and use it for every wall object in a scene.

**Rejected alternatives:** Distinct colors per frame preserve the bbox shortcut. Mixed-color boundaries exercise authority edge cases but are not needed to repair the demonstrated curriculum and could make the teaching signal less direct.

**Probe:** All five canonical inputs pass `self_check`; all generated profiles reconstruct exactly and pass Racket-labelled checks.

**Limitation:** The generator does not teach how the authority behaves when an enclosed zero region touches multiple colors.

## D9 — Give difficulty bands distinct deterministic streams, not different semantics

**Original rationale/evidence:** An intermediate repair was flagged because easy/medium/hard were byte-identical for every sampled seed. Difficulty should affect deterministic sampling if it is part of the interface, but changing the semantic profile mix by band would make some bands weaker.

**Decision:** Include `band_tag` in canvas, wall-color, shape, and layout RNG keys while keeping the same four-profile schedule in all bands.

**Rejected alternatives:** Dropping difficulty support would diverge from the shared runner. Making hard structurally different would introduce band-dependent rule coverage.

**Probe:** The task test detects at least one cross-band difference, and final defect lint is clean.

**Limitation:** Bands differ as deterministic scene streams, not as a calibrated monotonic difficulty scale.

## D10 — Require visible transformations

**Original rationale/evidence:** The defect linter found that an intermediate repair changed under 3% of cells on 21/60 generated pairs while canonical demonstrations changed at least 13%.

**Decision:** Enlarge the shared pair and closed contrast so every ordinary generated example changes at least 3% of cells.

**Rejected alternatives:** Suppressing the warning would keep weak demonstrations. Inflating every enclosure would reduce layout diversity.

**Probe:** The task suite enumerates 576 draws across default/easy/medium/hard and checks the 3% floor; final defect lint is green.

**Limitation:** The 3% threshold is a presentation safeguard, not a semantic theorem.

## D11 — Declare and execute the rival contract

**Original rationale/evidence:** The baseline semantic gate had `NO_CONTRACT`, so it could not measure the exact shortcut that motivated the repair.

**Decision:** Declare the global-per-color bbox rival consistently in `SEMANTIC_RIVALS`, `CANONICAL_SHORTCUTS`, and `LESSON_COMPETITORS`; connect it to a `bbox_counterexample` witness and validate lessons with `lesson_identifiable`.

**Rejected alternatives:** A prose-only warning is not regression protection. Hard-coding the rival only in tests would prevent shared gates and census tools from discovering it.

**Probe:** The shortcut fits 5/5 canonical pairs, is refuted in all 300 large-census lessons, and has zero surviving windows in the retained 312-window probe.

**Limitation:** The declared family contains one task-specific rival; unlisted hypotheses remain possible.

## D12 — Retain a portable all-window probe

**Original rationale/evidence:** The shared lesson census tests many production lessons and query rotations but explicitly does not enumerate every contiguous schedule window. Future edits to the schedule could regress a boundary window while pooled checks remain green.

**Decision:** Add `workspace/probe_bbox_curriculum.py`, which loads the sibling source, reads canonical pairs with `reviewer_support.find_root`, discovers declared rivals, and checks every contiguous window for the requested seeds and sample span.

**Rejected alternatives:** A one-off analysis script outside the task would not survive the return. Duplicating canonical data in the probe would be brittle and expose a second source of truth.

**Probe:** Its regression test first failed because the tool did not exist, then passed; the retained wide run covers 384 draws and 312 windows.

**Limitation:** It uses the explicitly diagnostic Python mirror for generated labels; authority-labelled confidence comes from the shared semantic gate and lesson census.
