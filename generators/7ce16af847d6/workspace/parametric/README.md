# 7ce16af847d6 native waypoint family

`canonical` preserves the exact selected rule: recolor only four-connected
color-1 components that are exactly nine cells in a 3×3 bounding box.

`bridge_centers` executes that rule first. It then reads the color-3 components
created by stage A, orders their centers by reading order, and connects adjacent
centers with horizontal-then-vertical color-3 paths. Inputs contain no color 3,
so skipping stage A leaves no waypoints and changes the answer.

The family supports 2–6 demonstrations and 1–4 queries with count-independent
prefixes. Inputs are matched across settings, include blue and nonblue 3×3
counterexamples, vary target counts and canvas sizes, and reserve the fourth
query for a substantive 30×30 scene. `audit.py` checks matched inputs, finite
rivals, count boundaries, distinct setting outputs, and sampled causal
separation. Native authoring preflight independently executes every label with
protected Racket.
