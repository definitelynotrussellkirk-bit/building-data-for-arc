# Working notes: f283b8535697

## Current parametric work

The selected canonical generator remains version 3.4.0 with the exact registered
Racket reconstruction rule. `workspace/parametric/` adds an opt-in native adapter:
`output_mode=patch` preserves that exact program; `largest_object` reconstructs
the hidden patch, selects its unique largest same-color four-connected component,
isolates it, and crops its bounding box. The recovered component membership and
sizes are an input-dependent intermediate needed to choose the final extraction.

The prototype reuses the selected symmetric-field generator, then injects
multicolor recovered patches by reflection orbit. The marker stays solid blue
5×5 and crosses at most one center axis. Inputs remain even-sided 10..30.
The first two demonstrations cross opposite axes and jointly refute finite
reconstruction and selection rivals; a third demonstration anchors the source
style. Independent counts support 2–6 demonstrations and 1–4 novel queries,
ordinarily three and four. Query inputs are independent of the private setting
and of the requested demonstration count, with stable one-query prefixes.

Self-review found genuine two-demo shortcuts: choosing the most frequent patch
color or the largest component bounding-box area. Both original witnesses were
confirmed in protected Racket. Their executable rivals now enter the two-demo
cover, without increasing demonstration count. The bounded follow-up audit found
no query-disagreeing survivor among its tested alternatives. Retained evidence is
`checks/f283b8535697/self_review/` in the return; current commands and limits are
in `workspace/parametric/README.md`.

Outputs remain at most 5×5; the verified 30×30 cases exercise full input content
and do not solve the training mixture's large-output gap. No new production
override or production distribution is claimed. Partial-mirror alternatives are
tested; 180-degree-only reconstruction is equivalent on this grammar. Larger
grammar claims, universal identifiability and measured training gains remain
unestablished. Owner qualification and exact-source acceptance follow intake.
