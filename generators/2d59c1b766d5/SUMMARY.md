# 2d59c1b766d5 — fill local chambers from gates

Two color-8 rectangular frames contain gray walls, one colored gate each, and zero-valued floor. The target fills only zero cells reachable from each gate by four-neighbor motion inside its own frame.

Version 3.0.0 generates canonical-scale 15–17×20–22 scenes with two 7–8×7–9 frames. A five-demonstration/one-query, period-three schedule alternates `open`, `sealed`, and `diagonal` wall topologies. Every query rotation retains all three profiles, separating the intended rule from both “fill every interior zero” and eight-neighbor flood fill. Exact controls are canvas height, canvas width, and topology profile.

Canonical Racket authority is unchanged and pinned by `RULE_HASH = 61c97755a0ea`. See `notes.md`, `workspace/probe_curriculum.py`, focused tests, and the retained counterexamples for limits and evidence. Approval remains catalog-derived; this summary is not approval.
