# 664a918eb273 — preserve and concatenate orthogonal paths

Version: `4.0.0`. Canonical ARC identity: `d017b73f`; rule hash: `0bf6f91bb8f8`.

Zero is background. The input contains two to five spatially separated monochrome
paths in disjoint column bands; disconnected paths may share a color. Each path
has a unique leftmost entry endpoint and a rightmost exit endpoint. Keep the first
path in place, then translate each later entry to the cell immediately right of
the preceding exit, at the same row. Preserve shapes, colors, and input height;
trim only the unused right edge. Racket remains the label authority.

The generator constructs a safe packed chain first, then spreads the input bands
and independently moves later pieces vertically. It does not clip, overwrite,
or silently discard pieces. A structural self-check verifies eight-connected
object extraction, four-neighbor connectivity and degrees, endpoints, separated
bands, and the resulting translations' bounds and non-overlap.

Default even sample indices produce canonical-style three-row scenes, widths
9–11, three or four paths, a zero left margin, and lengths 2–4. Odd indices
produce heights 4–12, widths 14–30, two to five paths, positive left margins,
and longer paths. Repeated colors occur in both profiles. Difficulty controls
the expanded path-length cap: easy 5, medium 8, hard 11, unspecified 9.

Public integer overrides are `grid_h` 3–12, `grid_w` 8–30, `n_paths` 2–5,
`n_distinct_colors` 1–5, `gap` 1–3, and `anchor_col` 0–3. Feasible requests are
realized exactly; conflicting requests raise a structured `IncompatibleLayout`.
Unknown names, booleans, and out-of-domain values are rejected.

Executable rival rules test left-justification, color-as-object-identity, and
horizontal-only compaction. These diagnostic competitors never supply labels.

Acceptance evidence from this review: 12/12 battery stages green, 29 focused
tests passing, 9,000 generated inputs with no detected geometry defects, and
450 actual Racket executions with no pixel loss or safe-geometry disagreement.
These are finite checks, not training-admission approval or a measured learning
improvement. The sampler intentionally does not cover arbitrary nonmonotone paths.
Approval remains derived by the catalog from current code and retained evidence.
See the return's `REVIEW.md`, `DECISIONS.md`, and task-local workspace tools.
