# 24bb2221ca5c — enclosed-hole filling curriculum

A zero-background grid contains one or two closed hollow 4-connected components, optionally with a visually similar side-open decoy. Disconnected components have a one-cell moat and may reuse a color. Closed components include exact rectangular frames, a rectangle missing one corner whose interior remains enclosed under 4-connectivity, spurred frames, and a dense two-cavity mass with at least one nonrectangular cavity.

The transformation fills every zero region topologically enclosed by each component with that component's color. It uses 4-connected component identity and 4-connected background escape, fills every hole independently of shape, preserves existing nonzero cells, and leaves exterior-connected/open regions unchanged.

The default three-example curriculum is deliberately scheduled:

1. **canonical_pair** — two canonical-palette rectangular frames, including one canvas-border case;
2. **gap_contrast** — a corner-gap positive beside a side-gap negative;
3. **topology_stress** — a broad-palette dense two-cavity object with an L-shaped hole and outward spur, plus a disconnected closed component in the same color.

Together these examples distinguish the selected rule from identity, largest-only, raw bounding-box fill, rectangle-frame-only, canonical-color-only, border-skip, one-hole-per-component, merge-all-same-color-bboxes, 8-connected-hole, and rectangular-hole-only shortcuts.

Kind: `per_puzzle`. Selected version: `3.2.0`. Pinned rule hash: `514c258ab731`.

## Reviewer-ready native parametric prototype (2026-10-24)

A separate opt-in family now preserves the canonical `all` program byte-for-byte and adds two nearby topology-dependent policies: `largest_hole_area` and `most_holes`. The family supports 2–6 demonstrations and 1–4 queries, keeps inputs independent of the hidden setting, exposes only one masked query at a time, and includes a substantive 30×30 query.

Native qualification covered all three settings at seeds 0 and 17 with three demonstrations and four queries (six jobs, 78 protected-Racket evaluations). A separate finite audit checked 42 labels and five plausible rivals with zero survivors. A source-bound wrong-intermediate witness demonstrates that replacing enclosed-hole area with bbox area changes component selection and the final Racket output. This is reviewer-ready evidence only: the variants are not owner-accepted or training-admitted.
