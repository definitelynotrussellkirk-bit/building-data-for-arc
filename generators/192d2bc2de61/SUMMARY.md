# 192d2bc2de61

Read every nonzero cell in row 0 from left to right as a three-color legend. For each legend color, find all four-connected components strictly below row 0, select the uniquely largest component (ties use top row, then left column), crop its bounding box, and pack the three crops horizontally in legend order with one zero column between crops.

Version `4.0.0` uses one exact control, `scene_profile`, with four deterministic curriculum profiles. All profiles use canonical canvas sizes and three nonzero colors. `prefix_10x13` is a canonical-core case with one body component per legend color. `spaced_10x14`, `offset_11x14`, and `wide_11x15` use sparse or shifted legends and add earlier same-color singleton decoys, while placing the uniquely largest components in a body order different from legend order. These contrasts refute “take the first component,” “read only a contiguous legend prefix,” and “pack by body position.”

Two demonstrations plus one query are the declared lesson shape. The four-profile schedule is phase-shifted across difficulty bands; every tested cyclic window and every tested query rotation retained the required counterexamples.

Kind: `per_puzzle`. Selected version: `4.0.0`. Canonical rule hash: `5ea0808c0383`.
Catalog approval remains external; passing review checks does not approve training use.
