# Working notes: d9d4f0ebb48b

## Review review-e935ce7fbf9f51fb — 2026-10-02

The imported 2.0.0 generator reserved colors 1–7 for pluses and 8–9 for distractors. Every measured generated pair was solved by a palette-filtered bounding-box rival. Its three-cell L also left a five-cell-component bbox rival intact. Version 2.1.0 samples plus colors from all 1–9, reuses true-plus colors for distractors, and generates a five-cell 3x3 L. No Racket authority changed.

Decisions: retain zero background, separated 3x3 footprints, difficulty/size/count axes and four cyclic profiles. Keep a one-third canonical-palette mixture on clean draws; other draws are color-randomized. Match color and area in the L profile so geometry is the necessary distinction. Validators accept structurally valid recolorings and legacy three-cell Ls; witness predicates distinguish the narrower generated counterexamples from those legacy members.

Regression work: independent reference-backed palette/area rivals; permutation closure; all-color role support; exact semantic witnesses; every negative fixture must actually mutate its source. The first repair exposed a no-op spur fixture; select a genuinely blank in-bounds cell instead of clipping coordinates onto an existing arm.

Final generator SHA256: `25e5382551d170b93c84b77befa5dfc51b799e05ee12e884e01cd8fd1891e5eb`.
Baseline SHA256: `f5182597a8d957ee6d0f97684306a74cadf73ed61f95793a41c2b878d748682e`.

Measured: three bands, seeds 0–63, indexes 0–3 give 768 pairs / 192 disjoint four-demo groups per source. Both composed rivals survive 192/192 baseline groups and 0/192 final groups. Final recoloring self-check rejections are 0/768 versus 576/768 baseline; reference equivariance and mirror disagreement counts are zero. Unique original inputs are 731 baseline / 752 final. Canonical comparisons use four pairs. Each source census calls Racket 1,540 times. Raw evidence is retained in the review's `checks/counterfactual-{baseline,final}` directories, not duplicated here.

Final focused tests: 79 passed. Final complete battery: 12/12 green. Full repository suite: 169 passed, one shared streaming-timeout failure, diagnosed as a 0.2-second startup-budget assumption in this environment; no shared fix included. Detailed reports and failed iterations are in the source-bound return.

Limits: no learner training run, no all-seed claim, no arbitrary-background or overlapping-trigger extension. An exact plus-shape recognizer is still equivalent within the separated teaching grammar. Rejecting the named rivals is useful but not proof of global identifiability or training admission. Imported associated notes and timestamps remain untouched in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `25e5382551d170b93c84b77befa5dfc51b799e05ee12e884e01cd8fd1891e5eb`.

# Design decisions and rejected alternatives

Scope: selected generator `d9d4f0ebb48b`, version 2.0.0 → 2.1.0. Baseline and final SHA256 values are recorded in `REVIEW.md`; final-source measurements below refer to `25e5382551d170b93c84b77befa5dfc51b799e05ee12e884e01cd8fd1891e5eb`.

## Preserve the task rather than relabel it

The authority is a local same-color cardinal-neighbor predicate followed by 3x3 filling. Keep the Racket source and canonical outputs unchanged. There was no evidence of an authority defect in this task; changing it to match a convenient generator shortcut would reverse the direction of correctness. Keep a Python mirror for tests, but use real Racket output in the independent audit so the mirror does not certify itself.

Keep zero as background. Arbitrary background permutations would change the nonzero predicate and are not automatically valid transformations. Restrict recoloring tests to bijections of 1–9 that fix 0. On the measured final 768-pair population the reference is equivariant, the mirror agrees, and all recolored inputs pass the validator. This is a finite check, not a universal proof over arbitrary invalid input.

## G1: remove absolute color roles

Original choice: true pluses use 1–7; L and mixed-cross center use 9; false-cross arms and boundary bar use 8. The author's original motivation for those specific IDs is unknown. Visual separation is a plausible hypothesis, not a documented explanation. The fixed split made a color-filtered component-bbox solver sufficient on all 768 original generated pairs.

Selected change: sample true colors from all 1–9; sample each distractor's primary color from the actual true-plus colors in that scene. The false-cross arm color differs from its center and remains nonzero. Equality relationships are semantic; literal IDs are not. Sample through a dedicated keyed palette RNG, separate from geometric placement.

Rejected: merely shuffle the global palette once per task. A learner could still assign semantic roles from a persistent task-level split. Merely adding occasional color-8 true pluses would kill one hardcoded filter but would leave same-color component selection separable in most lessons. Matched positive and negative color roles are a stronger controlled contrast at nearly the same grid cost.

Validation change: recognize L, bar and false-cross geometry using observed colors and equality, not literal 8/9. Accept legacy three-cell L inputs as valid grammar members, while generating the stronger five-cell L. Do not mistake broader validator acceptance for a promise that every accepted member is sampled uniformly.

Evidence: G1 in `REVIEW.md`; role histograms, counterexamples, independent reference output and rejection counts in `checks/counterfactual-{baseline,final}/palette.json`; red/green regressions retained.

## G2: match area as well as color

Original L had three cells in a 2x2 footprint; true pluses had five. Changing only color roles leaves a different shortcut: fill bounding boxes of five-cell monochrome connected components. This rival matches all four canonical pairs and all 768 original draws.

Selected change: the generated L is the union of two perpendicular three-cell edges of one 3x3 square, hence exactly five cells, with one of four orientations. It has the same monochrome area and bounding-box dimensions as a true plus but no valid trigger center. It reuses a true-plus color. A correct response grows the plus and preserves the L.

Rejected: arbitrary random noise as a distractor. Noise can accidentally create triggers or conflate many differences at once; the matched L isolates the shape predicate and fits the established footprint allocator. Rejected: making every example a dense collage of counterexamples. A clean canonical-like profile remains useful, and every four consecutive scheduled samples still contains all four profiles.

Added rivals `palette_gated_bbox` and `five_cell_bbox`. Added distinct witnesses for a shared-color L and a five-cell L rather than declaring that every legacy L defeats both rivals. The generic L witness only promises to defeat the unconditional component-bbox rival. Tests retain a legacy three-cell L and verify that it is not falsely labeled a five-cell witness.

Proof sketch for ordinary L draws: if its shared true-plus color lies in 1–7, the palette rival wrongly fills the L's missing bbox cells; if it is 8 or 9, that rival fails to grow the shared-color true plus. Either way it disagrees. The five-cell rival wrongly fills the L for every nonzero color. The cyclic schedule provides an L in every length-four consecutive group. Measurements verify these claims for the final finite census; future code changes must retain the conditions.

## Preserve useful bounds and schedule

Keep the existing advertised size axes (height 7–14, width 8–14), one or two pluses, difficulty bands and deterministic four-profile schedule. The defaults vary by profile and difficulty and retain canonical-scale anchors. Generalizing counts, overlap, noise and backgrounds all at once would make it difficult to attribute gains and would enlarge the authority/validator review. These are deferred, not deemed useless.

Keep one blank cell between 3x3 footprints and the backtracking allocator. Matching colors must not accidentally merge a distractor with a true plus. Keep initially blank diagonals so growth is observable. Keep the multicolor-cross profile to distinguish occupancy from color agreement. Keep repeated-color pluses to defeat one-per-color processing and a border-touching footprint to defeat skipping valid edge-adjacent centers. Explicit `plus_count=1` overrides remain legal and may not teach multiplicity; the default four-example curriculum provides the two-center witness.

Clean samples retain the band's canonical palette with probability one third; the remaining clean draws use the all-color palette. This probability is a practical continuity choice, **not** a value established by a Qwen training ablation. Exact canonical dimensions and palette cardinalities remain; exact canonical colored grids are not required on every draw.

## G3: mutation fixtures must actually mutate

Color-role repair exposed an inherited fixture weakness: `max(0, col-2)` can land on an existing plus arm near a border. Repainting that arm is not a negative example. The replacement chooses an in-bounds empty cell two cardinal steps from the trigger. Tests first assert that every returned fixture differs from its source and then assert rejection.

L color-corruption and solid-bbox fixtures derive the observed L color rather than assuming 9. The first palette repair had one failing test, retained under `checks/palette-green`, before this issue was fixed. No weakened expected result was used to get a pass.

## Reusable, scoped tooling

`workspace/review_checks.py` builds an independent runtime, explicitly copies both selected test files, unsets caller PYTHONPATH, runs tests or the probe, writes the actual runtime cwd and staged-source hash, and deletes the bulky runtime afterward. The frozen import map otherwise omits newly added task tests. A temporary absolute cwd is recorded in receipts; the portable reproduction entry point is the packet-root wrapper in `RESULTS.json`.

`workspace/palette_probe.py` implements rivals independently of the generator and compares against Racket, tracks counts at both pair and complete-lesson level, checks lawful recoloring and writes full witnesses. Nonempty findings produce nonzero exit. The initial staged-hash race in our new runner is documented and superseded, not hidden.

`workspace/adversarial_audit.py` is findings-only and touches neither audit target. `workspace/runtime_timeout_probe.py` isolates the shared startup-budget failure without changing shared acceptance criteria. Exit 0 from either diagnostic means execution completed, not that their reports contain no findings.

## Limits and rejected overclaims

An exact plus-shape recognizer remains equivalent to the intended local predicate on this separated grammar. Rejecting two more simple rivals does not imply a unique mathematical rule, general ARC transfer or efficient learning by Qwen3.5-9B. The probe's seed sample is not exhaustive and duplicates are counted explicitly. Eight checks of similar implementations do not replace an independent authority. The next empirical step would be a held-out learner ablation with geometry and color shifts; none was run in this return.

No shared timeout fix, audit-generator repair, catalog promotion or training admission is included. Broadening the task distribution is a separate measured change, not an excuse to weaken the present task's contracts.
