# 11c53dabb028 — negative tiling with ordered color selection

Version: **2.0.0**. Canonical task: `48131b3c`. Rule hash: `573d7b5ea64c`.

The canonical Racket rule selects the first nonzero color in row-major order.
It maps input zeros to that color and all nonzero cells to zero, then repeats
that tile twice vertically and twice horizontally. An `h × w` input produces
`2h × 2w`; this is periodic tiling, not cell enlargement or reflection.

## Supported input domain

A nonempty rectangular list/tuple grid of strict integer colors `0..9`, with
both dimensions in `1..15`, area at least two, and at least one zero and one
nonzero cell. Booleans, floats, malformed rows, oversized grids, all-zero and
all-filled inputs are rejected. Sparse masks and one-dimensional grids are
lawful. The four canonical inputs remain accepted.

## Default lessons

Five demonstrations plus one query draw from a six-profile schedule:
monochrome 2×2; middle-ranked first color in a wide rectangle; minimum first
color; monochrome 3×3 or 4×4; middle-ranked first color in a tall rectangle;
maximum first color. Middle profiles make the selected color a minority;
extreme profiles make it a unique majority. Both retain a different actual
column-major first color and a different last color. Geometry, color identities,
occupancy and placements vary, with difficulty weighting and a broad size tail.

The redundancy retains demonstrations against the ten declared rival rules
when any one of the six pairs is held out. This is a finite teaching contract,
not a proof of identifiability against arbitrary programs.

## Explicit controls

`grid_h` and `grid_w` are exact throughout `1..15`, independent of difficulty;
`fg_color` is the first row-major nonzero color; `multi_color` is a strict bool.
`fg_density` requests final occupancy
`min(area-1, max(1, round(area * value)))` for finite numeric values in `0..1`.
`texture` selects a documented mask preference before exact occupancy is imposed;
it does not guarantee the final named geometric shape. Removed controls
`bg_density` and `noise_overlay`, unknown keys and invalid texture modes fail
loudly. Free dimensions are selected from feasible choices before drawing.
Truly incompatible combinations raise `ValueError` with relevant axes attached.
Explicit controls use the general lawful domain and do not promise the default
lesson schedule. See `notes.md` and `workspace/REVIEW_PROBE_USAGE.md` for evidence
and replay instructions.

Approval remains a catalog/maintainer decision. The review retains a strict
linter blocker for two mutation heuristics despite reference-proven lawful
counterexamples; see the return's `REVIEW.md` and `FEEDBACK_TO_CODEX.md`.
