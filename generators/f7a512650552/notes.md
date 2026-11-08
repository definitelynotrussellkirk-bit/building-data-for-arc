# Working notes: f7a512650552

Review `review-75826ec49c2b02a7` replaced the broad-but-inexact v2 distribution with an authority-pinned v3 contract.

Key repair decisions:

- Preserve the canonical Racket rule and exact row-first branch order; canonical examples whose row and column closures coincide remain lawful.
- Advertise only controls recoverable from returned pixels: `grid_h`, `example_w`, `query_w`, and `mode`. Reject unknown, obsolete, non-integer, and out-of-range overrides.
- Bound widths by `2*example_w + 2 + query_w <= 30` and use constructive connected-shape fallbacks instead of returning an unrelated fixed example.
- Alternate row/column mode by sample index and place canonical-profile anchors at indices congruent to 0 or 1 modulo 6.
- Require generated source/query shapes to distinguish row from column closure; require query labels to differ from unchanged-query and solid-box shortcuts.
- Retain `workspace/reference_probe.py` as an implementation-independent parser/oracle for future review and tests.

The final generator hash and all measured limitations are recorded in the packet-level `REVIEW.md` and `DECISIONS.md`.
## Current reviewer considerations

Source SHA-256: `321f6c97ac908411af57a794f5c0e336ee5a79858e5191ebf646aab37e0a0205`.

# Distribution and implementation decisions — f7a512650552

Final generator version: `3.0.0`
Final generator SHA-256: `321f6c97ac908411af57a794f5c0e336ee5a79858e5191ebf646aab37e0a0205`
Pinned canonical rule hash: `25622d47ca31`

## D1 — Preserve the canonical authority and row-first ambiguity behavior

**Choice.** Keep the Racket rule unchanged and mirror its exact branch order: when the worked result equals row closure, choose row mode even if column closure is also equal.

**Original rationale.** The baseline asserted that every source must distinguish row and column closure, but that rationale was incompatible with canonical train pair 0. The reason for the canonical ambiguous source is not documented; authority behavior is nevertheless explicit.

**Alternatives considered.** Rewrite the Racket rule, alter the canonical pair, or continue rejecting the ambiguous pair. All three would change authority or exclude labeled data and were rejected.

**Probe/evidence.** Canonical-parity tests cover all three labeled pairs; final self-check and profile-floor accept 3/3. Rule smoke compares the independent mirror with Racket on 120 draws and reports 0 mismatches.

**Failure mode/limit.** A canonical ambiguous worked example does not itself teach branch selection. Generated examples therefore distinguish branches, but canonical support remains intentionally broader than the generated strict domain.

## D2 — Advertise only four exact, observable controls

**Choice.** Public `AXES` are `grid_h`, `example_w`, `query_w`, and `mode`. Each is integer-valued, has a finite exact range, changes returned pixels, and is recovered by `observe_overrides()`.

**Original rationale.** Baseline v2 advertised nine controls, but several were dead, unprobeable, ignored, or not observable. No evidence supported keeping `density`, palette textures, requested object sizes, or requested color counts as exact controls.

**Alternatives considered.** Implement all legacy controls, mark them diagnostic, or retain them as aliases. Implementing them would add complexity unrelated to the rule; diagnostic/alias controls would still invite callers to rely on nonexact behavior. They were removed and now fail closed as obsolete keys.

**Probe/evidence.** Final override matrix: 398 cases × 30 seeds × 3 bands = 35,820 accepted draws, zero findings/warnings; explicit regression tests cover minimum, maximum, canonical, malformed, Boolean, unknown, and obsolete values.

**Failure mode/limit.** Object size, exact color pair, and placement remain deterministic nuisance variation rather than user-controllable axes.

## D3 — Bound geometry by construction

**Choice.** `grid_h` is 6–20, `example_w` is 3–8, and `query_w` is 3–12. Total width is `2*example_w + 2 + query_w`, hence at most 30.

**Original rationale.** Baseline ranges allowed generated widths of 31 and 32. The old minimum height 5 also left too little space for a universal constructive teaching fallback.

**Alternatives considered.** Clamp oversized draws, resample until legal, or declare incompatible axis combinations. Clamping violates exact overrides; broad rejection complicates the contract; repeated rejection creates hidden support bias. Smaller independent ranges make every Cartesian combination legal.

**Probe/evidence.** Defect lint is clean; exhaustive override generation includes the 20×30 maximum and 6-row minimum; task tests assert all outputs remain inside 30×30.

**Failure mode/limit.** This deliberately omits very narrow/tall or 21–30-row layouts. The canonical and broad profiles still cover 78 input shapes in the final diversity sample.

## D4 — Use connected random polyominoes with a constructive fallback

**Choice.** Generate normalized four-connected shapes from a deterministic RNG, accept only shapes that fit and teach the selected branch, and fall back to a known connected 3×3 witness after bounded search.

**Original rationale.** Baseline used random polyominoes but returned an unrelated fixed row-mode grid when search failed. The original reason for that fallback is unknown; it violated requested controls and could hide failure domains.

**Alternatives considered.** Unbounded rejection, a fixed library only, or returning an error. Unbounded rejection risks hangs; a fixed library reduces diversity; errors would make legal advertised combinations nonconstructive.

**Probe/evidence.** All 35,820 exact override draws construct successfully; task tests cover extreme dimensions in every band. Sorted set choices and a cross-process test make generation invariant to `PYTHONHASHSEED`.

**Failure mode/limit.** Search is finite and the fallback family is small. It is used only when random search cannot find a teaching shape; the gate does not report fallback frequency separately.

## D5 — Require source and query semantic witnesses

**Choice.** Generated source shapes must have distinct row/column closures and the selected closure must add cells. Generated queries must additionally produce a selected result that is not their solid bounding box.

**Original rationale.** Baseline correctly aimed to make the worked example decidable, but did not require the query label to distinguish closure from copy or solid-box shortcuts. The canonical labels themselves allow `solid_bbox` on all three pairs and `always_row` on all three.

**Alternatives considered.** Rely on lesson-level mixing alone, allow nonteaching individual queries, or add many ad hoc rivals. Requiring local witnesses is cheap and makes every label informative; the lesson hook then handles branch-specific rivals.

**Probe/evidence.** In the 600-draw semantic scan, `closure_changes_query` and `non_rectangular_result_refutes_solid_bbox` fire 600/600. Declared canonical shortcut `solid_bbox` fits 3/3 canonical labels and is refuted by generated witnesses.

**Failure mode/limit.** The four declared competitors are not exhaustive. In particular, a richer solver could condition on placement, colors, or schedule features.

## D6 — Alternate semantic mode and anchor canonical profiles

**Choice.** Default mode is `sample_index % 2`. Samples with residues 0 or 1 modulo 6 use dimensions `(9,7,7)`, giving a 9×23 input; other residues draw difficulty-shaped broad dimensions.

**Original rationale.** Baseline selected mode randomly and produced zero exact canonical-profile hits in 60 draws. The reason for its particular difficulty ranges is not documented beyond diversity.

**Alternatives considered.** Random mode plus rejection, all-canonical dimensions, or rare probabilistic anchors. Deterministic alternation guarantees branch coverage in every four-pair window; deterministic anchors guarantee profile support in every band without collapsing the rest of the distribution.

**Probe/evidence.** Semantic scan sees 291 row and 309 column examples over 600 draws. Profile floor gets exact hits in every band (5/20 easy, 11/20 medium, 6/20 hard). The census covers all six start residues in each band.

**Failure mode/limit.** Mode is predictable from sample-index parity inside generator internals. The pixel task remains independently specified, but schedule-adaptive proxies are not universally excluded; the `d62a0e470ae8` audit demonstrates why future shared gates should search for them.

## D7 — Keep color and placement as nuisance variation

**Choice.** Source/worked-result and query use two distinct colors sampled from `{1,2,3,4,6,7,9}`. Color 5 is reserved for separators, 8 for output, and 0 for background. Source and query placements are drawn independently within panels.

**Original rationale.** Baseline already reserved 0/5/8 and varied colors/placement. This was retained because it is lawful, broadens inputs, and is not a semantic control.

**Alternatives considered.** Fixed canonical colors, palette texture controls, or allowing the same source/query color. Fixed colors encourage color shortcuts; texture controls were dead; same colors weaken panel-role diversity and conflict with the validator's distinct-role contract.

**Probe/evidence.** Final diversity reports 10 colors across sampled input/output pairs; self-check enforces one connected object per panel, source/result color equality, and query/source color inequality.

**Failure mode/limit.** The probe does not exhaust all color permutations or numeric-color hypotheses. Output color 8 and separator color 5 are semantically fixed and intentionally not permuted.

## D8 — Four-pair lessons: three demonstrations, one query, rotation-safe

**Choice.** `EXAMPLES_NEEDED = 3`. A production lesson uses four consecutive accepted pairs, three ordered demos and one query. The retained census also holds out each of the four pairs once and preserves the remaining order; rotations are required, not diagnostic-only.

**Original rationale.** The packet's default floor is three demonstrations. Baseline had no lesson hook, so its teaching sufficiency was unknown.

**Alternatives considered.** Two demos, a fixed query position only, or more demonstrations. Two demos can leave one branch competitor alive; fixed query position can hide schedule/order shortcuts; more demos increase cost without being required for the four declared rivals.

**Probe/evidence.** Task tests exhaust 12 consecutive starts × four bands × four query positions. The source-bound census materializes 100 lessons per band: 300 production lessons, 1,200 pairs/unique inputs, and 1,200 required rotations, all identifiable against the declared rivals with zero errors.

**Failure mode/limit.** The census is finite, uses the production sampler, and does not enumerate every possible seed. Rotation reuses the same four-pair bundle; it does not create new draws or certify against undeclared adaptive rivals.

## D9 — Keep the Racket authority as the label source

**Choice.** Python mirrors and rival functions are review/test aids only. Racket remains the authority for battery labels, lesson census, solve generation, and audit counterexamples.

**Original rationale.** This is the repository's authority contract and avoids circularly validating Python against itself.

**Alternatives considered.** Replace Racket with the Python mirror or use private runner internals. Both were rejected.

**Probe/evidence.** Rule smoke has 120/120 mirror parity; authority-sync reports selected sources synchronized and execution parity `PASS`.

**Failure mode/limit.** One archival base-bank `raw_code` copy is divergent but unselected. It remains documented rather than rewritten outside assignment scope.
