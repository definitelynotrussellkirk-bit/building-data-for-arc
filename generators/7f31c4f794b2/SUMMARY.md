# 7f31c4f794b2

Constructive per-puzzle generator for the rule: extract same-color 4-connected nonzero components and recolor an entire component to 7 exactly when at least one of its cells touches the outer grid border. Interior components keep their original color.

Version `3.0.0`; `RULE_HASH = "187a145d27eb"`. Default inputs are 8–14 by 8–14 zero-background grids with 2–3 border-touching and 2–3 interior polyominoes. Rotations/reflections of L3, S4, T4, V5, and W5 provide sizes 3–5. Every draw includes a horizontal-edge-only component, a vertical-edge-only component, mixed border/interior status, and one color reused across a border and an interior component.

Exact public controls: `grid_h`, `grid_w`, `n_border_components`, and `n_interior_components`. Unknown, mistyped, and out-of-range controls fail loudly. The executable semantic contract targets global-border-color, top/bottom-only, left/right-only, and all-nonzero rivals.

Review `review-02c41d03f07a1b47`: after battery 12/12 green; task tests 31/31; lesson census 300 lessons and 1,200 query rotations with zero declared-rival ambiguities. Final generator SHA-256 `4e3177bab6a537619394175d91588775cc0b9a60c7b520387fc27e4b53f9c87d`. No Racket/canonical authority changed. See top-level `REVIEW.md`, `DECISIONS.md`, and `checks/` in the retained return for evidence and limitations.

Approval is derived by the catalog from current code and retained evidence; this review does not itself admit the generator to training.
