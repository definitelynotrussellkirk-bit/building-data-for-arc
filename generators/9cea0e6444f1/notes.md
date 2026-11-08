# Current account: 9cea0e6444f1

## Intended rule

Find the color-1 and color-2 cells separately. Normalize each set to its own bounding-box top-left, overlay the normalized masks, crop to their union, and paint the union color 3. Other colors are ignored. The canonical Racket authority and rule hash `fe554f47cd7a` were not changed.

## Reversed baseline decision

The pinned `2.0.1` generator (`06e2e54545ea8ffe0cc7b34b780c9e48c5d7b8830c40d45a796d335c355aed50`) instead taught “crop the absolute union.” That was not merely a narrow distribution: it implemented a different transformation whenever the two colors had different global origins. The retained witness is `counterexamples/absolute_union_shortcut.json`.

Version `3.0.0` replaces that manifold. It generates two connected normalized masks with genuine overlap, at least one exclusive cell from each shape, and a non-solid union; then it places the source shapes apart horizontally, vertically, or diagonally. This makes independent normalization, use of both shapes, overlap-versus-XOR, and sparse-union behavior observable in every ordinary draw.

## Distribution and controls

Exact observable axes are `grid_h`, `grid_w`, `n_one`, `n_two`, `origin_kind`, `placement_kind`, and `decoy_kind`; unknown controls are rejected. Shape sizes span 4..8 cells. `origin_kind=corner|split` varies whether the normalized masks contain their bounding-box corner. `decoy_kind=far_pair` adds two distant color-7 cells whose normalized footprint changes the all-nonzero rival; alternating `none|far_pair` scheduling ensures every consecutive three-example window includes a no-decoy refutation. No-decoy defaults anchor the canonical 9x9/11x11, three-color profile; decoy draws explore the wider declared canvas.

The Python oracle matches every canonical pair. Declared competitors are absolute-coordinate union, either source alone, intersection, XOR, solid-bbox fill, and normalization of every nonzero color. `workspace/probe_semantics.py` is the source-bound replay tool; `tests/test_generator.py` covers the retained counterexample, canonical oracle parity, exact controls, scheduling, and rivals.

## Final measured evidence

Generator SHA-256: `688ac98633654bf4c3f837dc8c8f62bf1af580600ca1239f4914abbbb1fb561f`.

- 27/27 focused task tests pass.
- Override contract: 48,150/48,150 accepted draws, 535 cases, three bands, zero findings.
- Public semantic gate: 600/600 strict draws, 5/5 canonical inputs accepted, 5/5 witness families firing, 12/12 lessons and 48/48 diagnostic query rotations free of declared-rival ambiguity.
- Larger source-bound census: 300/300 three-demonstration lessons, 1,200 labeled pairs, 1,200/1,200 query rotations, zero declared-rival ambiguities or scoring/materialization errors.
- Independent probe: 300 draws, zero core-rival agreements and zero surviving three-example all-nonzero windows.

The after battery is 10 green / 2 failed. Both remaining failures are shared authority-text synchronization findings: canonical and selected target-code texts differ exactly, although comment-stripped forms and execution parity agree. Those authorities are outside the assigned task directory and were left unchanged.

## Limits

The finite rival set is not a proof of unique induction against every possible rule. The sampler uses connected shapes inside a calibrated 4x4 normalized envelope and only one optional distractor pattern. The active authority-text divergence still needs a maintainer decision. Private-query correctness of the post-repair solve is unknown.
## Current reviewer considerations

Source SHA-256: `688ac98633654bf4c3f837dc8c8f62bf1af580600ca1239f4914abbbb1fb561f`.

# Decisions for 9cea0e6444f1

## D1 — Restore the selected semantics, not the baseline prose

**Prior choice:** version 2.0.1 collected color-1 and color-2 cells in absolute coordinates and cropped their joint bounding box. The original rationale is not recorded beyond the stale summary.

**New choice:** independently normalize each color to its own top-left before union. The five canonical pairs and the selected Racket program agree on this interpretation. The retained counterexample makes the two rules produce different output shapes. Rejected alternative: preserve the absolute-union generator and alter the rule; that would change authority to fit a defective sampler.

## D2 — Use two connected, partially overlapping normalized masks

Each shape has 4..8 cells and is grown in a calibrated 4x4 normalized workspace. The masks must overlap, and each must also contribute private cells. Their union must leave at least one bbox cell empty.

This simultaneously rejects one-color-only, intersection-only, XOR-only, and solid-bbox-fill shortcuts on every generated input. Rejected alternatives were independent random point clouds, which weakened object identity, and fully overlapping shapes, which made one source redundant. The 4x4 envelope is a deliberate tractability bound, not part of the canonical rule.

## D3 — Separate the source objects in observable placement families

The pre-normalized shapes are placed with at least one blank row or column between them. `placement_kind` cycles through horizontal, vertical, and diagonal arrangements; order within each arrangement is randomized.

This makes absolute-coordinate cropping disagree with independent normalization while avoiding contact that could merge the visual objects. Rejected alternative: allow overlapping source bounding boxes, because `observe_overrides` would no longer recover an exact placement family and the teaching distinction would be less clear.

## D4 — Vary normalized-corner occupancy

`origin_kind=corner` makes both normalized masks contain `(0,0)`; `split` makes neither contain it while preserving a zero-free bounding extent in both axes. This avoids teaching that every cropped shape must occupy its literal top-left cell.

A mixed one-at-corner/one-not-at-corner family was rejected for this repair because it would add another axis state without addressing a declared shortcut. It can be added later with an explicit witness.

## D5 — Add a lawful ignored-color witness

`decoy_kind=far_pair` adds exactly two color-7 cells separated by four rows and four columns. Their independently normalized footprint changes the “use every nonzero color” rival while the selected rule ignores them. A deterministic `none|far_pair` schedule ensures every consecutive three-example window contains a refuting pair.

Rejected alternatives included random singleton noise, whose normalization often coincides with `(0,0)` and can accidentally leave the rival output unchanged, and dense distractors, which would dominate the visual task.

## D6 — Preserve canonical-profile anchors while widening the canvas

Every no-decoy default draw is 9x9 or 11x11 with palette `{0,1,2}`, matching a canonical input profile. Alternating decoy draws use broader difficulty-shaped dimensions up to 16x18. This makes the profile-floor check reliable without reducing all examples to one size.

Rejected alternative: sample all dimensions uniformly. It had adequate geometric diversity but too weak a guarantee that each small battery band would hit a canonical profile.

## D7 — Advertise only exact, recoverable controls

The seven axes are dimensions, both shape sizes, normalized-origin family, placement family, and decoy family. Every override goes through a strict keyed draw, `observe_overrides` recovers it from the returned grid, and unknown names raise `ValueError`.

Stale baseline axes such as texture/density were removed rather than left inert. The final override gate exercised 535 cases and 48,150 draws with zero findings.

## D8 — Three-example lesson composition is explicit

`EXAMPLES_NEEDED=3`. Core geometric rivals are refuted per input. The decoy-dependent rival is handled by deterministic scheduling, not chance. The production census materialized 300 lessons (100 per band), 1,200 unique pairs, and all 1,200 held-out query rotations without a declared-rival ambiguity.

Limit: this is evidence against seven named programs only. It does not prove unique induction against all programs or all cyclic starts outside the sampled seeds.

## D9 — Keep authority unchanged and surface the synchronization blocker

No Racket source changed. The canonical and selected target-code authorities have different exact text but identical comment-stripped form and passing execution parity. Editing shared authority files would violate the task-local scope, so the return is marked `Acceptance: needs attention` rather than concealing the two failed stages.
