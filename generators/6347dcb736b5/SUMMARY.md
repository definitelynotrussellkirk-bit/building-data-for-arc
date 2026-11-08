# 6347dcb736b5

Construct 2–5 separated same-color 4-connected objects on background 0. The
output redraws **each connected object's** axis-aligned bounding-box perimeter in
its original color on a fresh blank canvas.

- Kind: `per_puzzle`
- Generator version: `2.0.0`
- Rule hash: `6bba75bb466d`
- Public axes: `grid_h` 6–14, `grid_w` 9–16, `n_blobs` 2–5
- Teaching guarantees: every grid distinguishes outline from fill/overlay; two
  of every three schedule slots distinguish connected components from global
  color grouping.
- Canonical profile anchors: `(6,9,3)`, `(8,9,3)`, `(8,10,4)` as
  `(height,width,palette-size including background)`.

The selected Racket rule remains authority. `generator.py::rule_mirror` and
`workspace/reference_probe.py` are review/test mirrors only.
