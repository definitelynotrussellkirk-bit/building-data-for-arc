# Working notes: 7c2a3ec6c4fb

## 2026-09-29 review

- Canonical semantics retained: exact colored bbox-crop multiplicity under 8-connected multicolor components.
- Baseline v2.2.0 preserved in `workspace/generator_v2_2_0_baseline.py`.
- Replaced one-repeat-class 3/4-object distribution with 2–4 exact pairs plus one singleton (5/7/9 objects).
- Added canonical morphology profiles, deliberate nuisance-feature matching, disjoint bbox zones, strict independent analysis, exact override observability, semantic rivals, and named witnesses.
- Reproducer for old bbox contamination: `seed="probe", sample_index=3113`.
- Canonical-perfect shortcut: unique color signature solves all four canonical pairs; generated witnesses now refute it.
- Selected base `target_code` synchronized exactly to canonical hash `38ad2c645d79`; old `raw_code` remains archival.
- Focused suite: 43 tests. Custom census and battery evidence are returned under `checks/`.

First-round limitation (partly addressed below): shapes fit within 3x3 zones; larger exact crops and unconstrained spatial packing were not represented.

## 2026-09-29 second hardening round

- Bumped the selected implementation to v3.1.0 without changing the canonical exact-crop rule or rule hash.
- Added monochrome answers as well as multicolor answers; the repeated base class still shares the answer palette, so color rarity is not reintroduced.
- Added canonical-style 1x4, 1x5, 4x1, and 5x1 crops in five-object scenes.
- Replaced the old 3x3 placement lattice with bbox-safe randomized free placement for five- and seven-object scenes; nine-object scenes retain the bounded lattice because dense free packing is unreliable at this grid size.
- Discovered three additional low-complexity signatures that solve all four canonical pairs: unique color histogram, unique geometry-plus-colors, and unique bbox-plus-histogram. They are now executable canonical shortcuts with named generated counterexamples.
- Added `workspace/shortcut_census.py`, which automatically inventories canonical-perfect signatures, generated shortcut hit rates, morphology/layout coverage, observable controls, and semantic-witness support.
- The exhaustive override gate exposed an ambiguity at `seed=18`, `sample_index=309`, `difficulty="hard"`, requested `pattern_profile="mixed_signature"`: an unrelated repeated class also matched the color-swap relation. Construction now rejects any scene whose singleton supports more than the requested profile relation, and a gate-range regression test covers all profiles and difficulty bands.
- Focused coverage is 63 tests after the second round; final battery and census receipts are returned under `checks/round2/`.

Known limitations: nine-object scenes still use a visible 3x3 lattice; long crops occur only in five-object scenes; the finite mask library stops at length five; and the signature census is deliberately extensible rather than exhaustive over all possible learned shortcuts.


## 2026-10-02 connectivity hardening (review-3ad0f68943a2c87d)

- Selected version 3.2.0; canonical rule and selected Racket authorities unchanged.
- Corrected initial hypothesis: v3.1.0 already had one diagonal mask, but diagonal answers were rare and shape mutation forced orthogonal connectivity. The new base-stratum draw is nominally 1/3 diagonal, once before retries; eight tight diagonal masks and connectivity-preserving mutations support every public pattern profile.
- A duplicated base retains the answer's connectivity, avoiding a unique-diagonal-object cue. Added `orthogonal_components` rival and `diagonal_connectivity_counterexample` witness without a new public axis.
- Independent matched-protocol census: seed `connectivity-census-v1`, indices 0–1799, 200 samples per difficulty/profile. Baseline hash `073456bd402dc0c357a80b208fd3afcd1b90e13288583f08e58bd55a333b7f6d`: 69/1,800 diagonal answers; final hash `8700398dc69b3e155a72ac7624307ec1d312e877cfeab3e7df4bfbfb8482cf57`: 593/1,800. Both versions have 1,800 distinct inputs within their run and zero validation/Racket mismatches. Shape-shift diagonal support rises 0/600 -> 186/600. This is distribution measurement, not a training result.
- Reusable probes: `workspace/connectivity_census.py` independently segments and optionally checks every Racket label; `workspace/review_probes.py` stages a source-isolated runtime for the assigned smoke/audits. The existing shortcut census now includes non-signature rivals, honest failure totals beyond the first-20 preview, and exact source/seed provenance.
- Final focused suite: 76 tests; before/after batteries: all 12 stages green; standalone lint green. Broad shared suite has a reproducible startup-sensitive 0.2-second timeout fixture failure (169 passed/1 failed), documented rather than patched outside scope.
- Fresh solve: one genuine revision, 3/3 visible examples; prior exposure yes, no reference consultation during solving. Masked query labels remain unknown.
- Main question counterexample: seed `connectivity-census-v1`, index 19, easy, `pattern_profile=shape_shift`; exact input/Racket output and orthogonal rival saved in return `checks/question-counterexample.json`.
- Prior limitations remain: finite masks and max length five, square canvases, fixed pair multiplicities, dense nine-object lattice. No claim of sufficient training duration or learned transfer.
## Current reviewer considerations

Source SHA-256: `8700398dc69b3e155a72ac7624307ec1d312e877cfeab3e7df4bfbfb8482cf57`.

# Decisions — assignment review-3ad0f68943a2c87d

## D1: Teach the intended segmentation without changing the task

The authority uses 8-connected multicolor foreground objects and exact colored bounding-box crops, preserving interior zero cells. I retained it. A new labeling rule or shape-normalizing comparison would change the puzzle rather than improve its training support. Canonical program SHA-256: `640d5deff723c95eb5ee161d578592e7eaac3bf36c965b02a0fc973007837a9b`.

Original rationale: prior notes explain compact canonical masks, deliberately matched nuisance signatures, and bbox-safe placement. They do not explain the absence of a connectivity quota; that intent is unknown. Inspection initially suggested all masks were orthogonal, but a real diagonal mask and 69/1,800 baseline examples refuted that stronger claim. Independent tests established the narrower gap, especially zero diagonal `shape_shift` answers. Evidence and the exact protocols are in `REVIEW.md` and the before census.

### Input choices retained

| Choice | Existing rationale or observation | This review's decision | Limit / rejected alternative |
|---|---|---|---|
| Black background and square 11/12/13 canvases | Existing canonical morphology profiles | Retain | Rectangular/new-size scenes require separate domain and placement review |
| Three/four foreground colors selected by scene profile | Existing exact override observability | Retain | Avoid adding a latent cue through a new special color |
| Two to four duplicate pairs plus one singleton | Earlier repair removed one-repeat-class shortcuts | Retain 5/7/9 objects and difficulty behavior | Not arbitrary multiplicity patterns |
| `color_swap`, `shape_shift`, `mixed_signature` | Existing witness construction defeats coarse signatures | Preserve all three, including unique profile observability | Do not trade old shortcuts for the connectivity fix |
| Monochrome and multicolor answers | Canonical support and prior hardening | Retain | No exclusive answer color |
| Free bbox-safe placement for 5/7 objects | Earlier lattice countermeasure | Retain | Nine-object scenes still use dense lattice; not solved here |
| Lines up to length five in sparse 5-object scenes | Canonical morphology coverage | Retain | Larger sparse shapes and long diagonal bridges remain absent |
| Tight bboxes, separated objects, exact duplicates | Prevent crop contamination and make rule labels unambiguous | Retain | Touching/colliding objects are outside this generator domain |

### New connectivity construction

**Eight small diagonal masks.** Use explicit tight 8-connected masks with multiple 4-components, including opposite handedness. This is bounded and reviewable within existing compact placement. Fully random polyomino growth could give broader morphology but would require a new distribution and retry analysis; it was not necessary for this repair.

**One nominal 1/3 stratum draw before retries.** Simply adding masks to the pool would make support depend on library size, rejection, profile, and difficulty. Choosing once keeps retries from repeatedly resampling away from the harder stratum. It fails explicitly if a stratum cannot construct a valid scene; it does not silently fall back to an orthogonal answer. One third leaves substantial ordinary canonical-like coverage. It is not claimed to be optimal for learning. The measured final rate is 593/1,800 in the stratified protocol, not exactly 1/3.

**Preserve connectivity in shape mutation.** The old `_connected4(candidate)` gate forced away diagonal `shape_shift` answers. The replacement requires a single 8-component, a tight bbox, and matching orthogonal-connectivity status between base and mutation. Color and signature constraints remain in force. This yields a diagonal singleton *and a duplicated diagonal base*, defeating the obvious connectivity-only answer selector.

**No new public axis.** Connectivity is a latent construction choice. Existing overrides remain valid and observable; a new axis would increase the API surface and require independent override semantics. Regression tests inspect output morphology directly instead.

**Executable segmentation rival.** The new rival only substitutes four neighbors for eight, keeping exact colored-crop comparison. It scans deterministically for the first singleton, making it a concrete reproducible program rather than an informal hypothesis. It is registered alongside existing rivals, and the witness requires an actual disagreement on a valid diagonal-answer input. All four canonical pairs fit this rival. This is the most important newly identified shortcut here, not a proof that no stronger learned heuristic exists.

## D2: Make measurement failures count honestly

The old shortcut census retained at most 20 invalid examples and incorrectly used that preview length as its total. A fixture with 35 invalid samples first reproduced a count of 20. A separate accumulator now reports the true total while retaining the bounded preview. `valid_samples` and conditional valid-input rates clarify denominators; generator identity and exact main/layout seed ranges bind the evidence.

Signature-only enumeration assumed the correct segmentation before proposing rivals. The census now also evaluates declared non-signature shortcuts; its existing label/profile/layout guardrails are unchanged. The independent connectivity census separately flood-fills without generator helpers, preserves every actual failure, and optionally calls real Racket on every input. Its wrapper is intentionally task-local: adapting it to arbitrary Racket syntax requires the proper staged rule converter.

## Verification choices and failed approaches

New tests were run red before implementation. Final selected-task tests cover support floors per difficulty and profile, mask validity, repeated diagonal distractors, witness/rival contracts, measurement correctness, and D4/nonzero-color equivariance. Metamorphic checks establish mirror/validator consistency, not new independent Racket checks for every transformed grid. The two 1,800-sample real-Racket censuses establish label parity separately.

Both before and after batteries were fully green. Thus the original battery result was not sufficient evidence against this missed rival. No thresholds were weakened. The default shortcut census and stratified comparison are different datasets and are reported separately, with overlapping witness counts identified as such.

The source-layout `wrap_rule` import failure was repaired only in the new task-local probe. A subsequent interrupted census invocation was rerun to completion; its incomplete attempt is not counted. The broader shared timeout test remained outside permitted patch scope. A timing probe isolated startup sensitivity; the failed full-suite logs remain visible rather than being replaced by a filtered green run.

## Audit and solve boundaries

A1/A2/A3 are audit findings only: neither randomly drawn target is patched. Their exact counterexamples and real-Racket outputs are preserved. Normal-domain label checks were clean; the row issue is missing support, and the panel issues are control/texture contract defects, not demonstrated incorrect Racket labels.

After final generator work, the fresh solve used only the public challenge and reviewer-written Python. Prior exposure is declared. The intentional four-neighbor diagnostic is not an accidental failed solve. One genuine attempt passed visible examples; hidden labels stayed closed and remain unscored.

## Remaining uncertainty

This is a measured distribution hardening, not a model-training experiment. It does not establish transfer, optimal mixture weights, or a sufficient total dataset size. Finite mask coverage, coarse scene/profile choices, and lattice structure in dense scenes can still support other heuristics. Future expansion should retain the new segmentation rival while adding independent shape/layout families and evaluating actual held-out learning, rather than assuming more random seeds imply more reasoning variety.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/7c2a3ec6c4fb/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->

## 2026-10-25 native parametric build

Built a task-local native family with one parameter, `crop_orientation`. The
`as_found` default returns the catalog-selected Racket program byte-for-byte.
The `marker_to_top_left` branch first performs the same exact duplicate-crop
census, then derives the unique singleton-colored corner marker inside the
selected crop and flips only the axes required to move that marker to output
upper-left. Sampling is independent of the hidden setting, supports 3–6
demonstrations and 1–4 prefix-stable queries, and retains a dense 30×30 stress
query with nine 6×6 objects.

Reviewer verification is source-bound and retained under
`workspace/parametric/evidence/` and `checks/7c2a3ec6c4fb/`: 10 focused tests,
76 existing task tests, a 20-seed × 2-setting self-audit with no finite-rival
ambiguity, protected-Racket native qualification for four jobs, and a replayed
wrong-intermediate causal witness. This is reviewer-ready prototype work only;
owner qualification/acceptance and any training admission remain unperformed.
