# Native parametric family: `99e7ba062bec`

`application=forward` is the exact selected canonical program: infer the
unique transform mapping panel A to panel B, then apply that command to panel C.
`application=inverse` carries the same input-derived command through its inverse
mapping before applying it to C; quarter-turn commands 2 and 4 exchange, while
the self-inverse transforms remain unchanged.

The adapter accepts 2–6 demonstrations and 1–4 queries independently. Inputs are
identical across settings for a fixed seed/count request, demo/query prefixes are
stable, and the first two demonstrations deliberately expose commands 2 and 4 so
the two settings are distinguishable at the minimum count. A and C use separate
colors and transform-discriminative, orbit-disjoint masks. The fixed four-query
bank ends with a dense 30×30 scene whose three panels occupy distributed rows.
Pair labels are deterministic Python claims; native qualification independently
re-executes every label through protected Racket.

The bounded `audit.py` checks matched inputs, two-demo identifiability, all seven
fixed-transform shortcuts, copy-panel and recoloring shortcuts, orbit separation,
and the 30×30 case. It does not establish universal uniqueness or measured
training benefit.
