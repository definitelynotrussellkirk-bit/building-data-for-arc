# 2e02ca69563c native parametric relay

The family preserves the exact canonical `all_local_pairs` program and adds
`relay_hit_color` on byte-identical inputs.

In the relay setting, the unique pair in the largest frame is routed first. Its
horizontal-then-vertical path crosses exactly one of two singleton cue colors.
That hit color is the input-dependent intermediate; only the matching endpoint
pair is then routed in every smaller frame. The canonical setting instead routes
both local pairs in every target frame.

Two through six demonstrations and one through four queries are supported. The
first two demonstrations hit opposite candidate roles, the second has multiple
target frames, and the fourth query is a substantive 30×30 scene with three
target frames. `audit.py` checks matched inputs, declared finite rivals, count
boundaries, output separation, and scene invariants; native preflight separately
executes every label through protected Racket.
