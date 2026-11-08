# 510b12f6a12a

An 8–9 by 8–10 zero-background grid contains 2–4 color-2 emitters on the top edge and 2–4 color-1 emitters on the left edge. Interior color-5 cells are blockers. Top emitters cast rays downward; left emitters cast rays rightward; each ray stops immediately before its first blocker. The output is a same-size zero grid with color 6 exactly where a surviving vertical ray and horizontal ray intersect.

The default curriculum cycles through eight exact, deterministic profiles. Every profile uses one of the canonical height/width/palette-cardinality combinations; the cycle includes blocker-free anchors, functional blockers in both ray directions, and 3–4-emitter counterexamples to the canonical-fitting “first two emitters only” shortcut. Difficulty changes the phase of this shared profile cycle rather than changing the rule.

Exact observable overrides: `grid_h`, `grid_w`, `n_v`, `n_h`, `n_blockers`. Unknown, non-integer, and out-of-range overrides fail closed. `RULE_HASH` is pinned to `8686bcf8a89a`.

Kind: `per_puzzle`. Selected generator version: `3.0.0`.
