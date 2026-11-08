# Working notes: 2e0d26e28a50

## Review `review-fb122afeebaf6bb8`

- Repaired the base generator from `2.0.1` to `3.0.0`. The prior metadata named
  inert palette/density/texture axes, silently accepted unknown controls and
  unsupported difficulties, did not mirror the labeled rule, and only checked
  that some color-2 and one color-1 cell existed.
- The repaired base exposes only observable controls (`grid_h`, `grid_w`, and
  `motif_size`), rejects coercions and unknown axes, generates deterministic
  separated connected motifs up to 30×30, validates connectivity and stamp
  bounds, and implements the exact bottom-right-anchor rule mirror. All three
  original labeled pairs remain unchanged.
- The canonical Racket program is preserved byte-for-byte (`660fb38aeca3…`).
  The native parameter `anchor_policy` adds `key_count_corner`: a connected
  color-3 key object of size 1, 2, 3, or 4 selects top-left, top-right,
  bottom-left, or bottom-right of the color-2 motif bounding box.
- Sequential dependency: A counts the key and produces the selected corner; B
  computes motif offsets from that corner and stamps them at the color-1 marker.
  The protected `always_bottom_right.rkt` counterfactual supplies the wrong
  corner and changes the qualified output.
- The family supports 2–6 demonstrations and exactly four distinct queries,
  matched inputs across settings, all four corners, distractors, and a 30×30
  query with 12 motif cells and 24 distractor cells.
- Bounded audits at seeds 0 and 17 refuted eight named shortcuts, including all
  fixed corners, reversed count, off-by-one, key-bounding-box area, and wrong
  output color. The final sweep covered 50 parametric episodes and 120 extreme
  base-control cases, including 7×7 and 30×30 boundaries.
- Source-bound authoring preflight, protected witness replay, 16-view public
  projection, and 24 first-turn invariance checks passed. These remain
  reviewer-only evidence, not owner acceptance or training admission.

Next action: integrate the exact repaired base and family, rerun native owner
qualification, and freshly accept only after reviewing the stricter base domain
and the key-count corner semantics.
