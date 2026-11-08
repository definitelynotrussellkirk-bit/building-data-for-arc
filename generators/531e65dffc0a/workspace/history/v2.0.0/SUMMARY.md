# 531e65dffc0a

A compact asymmetric prototype (one color outside `{0,2,3,4,5}`) appears with 2–4 isolated, distinct anchor cells. Anchor colors are transform codes: `2=id`, `3=CW90`, `4=180`, `5=CCW90`. The output is a fresh same-size grid containing prototype-color stamps whose normalized bounding-box origins are the anchor cells; source prototype and anchors are erased.

Selected generator version: `2.0.0`. Canonical Racket authority remains unchanged and is pinned by `RULE_HASH = "4acd30f1e03a"`.

The sampler uses exact observable axes (`grid_h`, `grid_w`, `n_anchors`, `proto_size`), canonical-profile scheduling, four-orientation prototypes, non-clipped/disjoint stamps, and a code schedule in which every ordinary three-example window covers all four transform codes. Executable semantic rivals and witnesses include the canonical-compatible shortcut `code_4_as_identity`.

Review evidence: `checks/after/`, `checks/lesson-census.json`, and `workspace/distribution_before_after.json`.
