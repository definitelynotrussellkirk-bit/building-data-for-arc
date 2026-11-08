# 142a3a64b02a

Version `3.0.0` generates a sparse color-0 background with three isolated objects: one straight red (`2`) component of length 3–6, one non-straight red tree, and a one- or two-cell non-red decoy. The non-straight component cycles deterministically through T, L, and stair profiles, with dihedral variants and canonical-scale grid sizes.

The rule acts on **whole 4-connected red components**. If an entire red component lies in one row or one column, recolor its two extrema yellow (`4`) and leave its interior red. Leave every non-straight red component and every non-red object unchanged. This is intentionally different from recoloring endpoints of each local horizontal or vertical run inside a branching object.

Declared exact controls are `grid_h` (`7..12`), `grid_w` (`8..13`), and `scene_profile` (`tee|ell|stair`). Every ordinary draw contains both a positive straight component and a negative non-straight witness, so the intended object-level boundary is teachable in any query rotation.

Kind: `per_puzzle`. Reviewed version: `3.0.0`. Canonical rule hash: `ffb5719ce1e2`.
Approval remains a catalog/maintainer decision; passing review checks does not itself admit training data.
