# 8b6543be4517 — mirror closure across a full 8 divider

Find the unique full row or column of color 8. For every original color-7 cell,
keep the source and paint its in-bounds reflection 7. An occupied reflection
**target is overwritten**, including a differently colored distractor. All
non-target cells stay unchanged. Skip out-of-bounds reflections without deleting
the source. The unchanged canonical Racket program supplies training labels.

Kind: `per_puzzle`. Candidate version: `4.0.0` (previously `3.0.0`).
Canonical normalized rule hash: `4b5d3dcd179a`.

The sampler preserves all 12 legacy `scene_profile` values and adds two exact,
visibly centered profiles shared across the difficulty bands. Counts, completed
pairs, clipped sources, and occupied targets vary rather than reproducing the
old six-input-marker/nine-output-marker template on every draw.

Use **four consecutive demonstrations** for the default curriculum. This covers
both orientations, centered and clipped cases, occupied and clean targets, and
both two-addition and more-than-three-addition cases. `EXAMPLES_NEEDED = 4` is a
lesson contract, not an automatic change to the public CLI's three-demo default.
An exact `scene_profile` override intentionally restricts geometry and does not
promise full lesson coverage.

Approval remains derived from the catalog and retained evidence; this review
has not promoted the generator or changed approval metadata.
