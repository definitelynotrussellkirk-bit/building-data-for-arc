# 954070a7d7ce

One or two separated hollow color-9 frames on background 0. Each has matching
1..8 markers below its top wall and inside its left wall. The unchanged canonical
rule completes the marked interior row and column within **each frame**.

Kind: `per_puzzle`. Imported version: `1.1.1`. Reviewed version: **2.0.2**.
Valid overrides: `grid_h=9..14`, `grid_w=11..20`, `n_frames=1..2`,
`n_distinct_colors=1..2` (marker colors only). One frame with two marker colors is
incompatible. Unknown/removed keys are rejected. Normal samples are never
negative texture fixtures.

Constructive placement guarantees requested counts. Four consecutive default
indices for a fixed seed include single, distinct-color, shared-horizontal, and
shared-vertical profiles. Repeated colors refute the “one cross per color” rival.
Frame sides vary from 4 through 9 subject to slot capacity. Canvas defaults mix
canonical-scale and expanded cases; explicit sizes always take precedence.

Review evidence: 12/12 battery stages green; 600 default and 1,080 override cases
checked against canonical Racket; 48 task tests. See `workspace/README.md` and the
returned packet's `REVIEW.md` for exact cohorts and limitations. These are local
review results, not automatic approval. Catalog approval/training admission
remain unchanged and require independent maintainer verification.
