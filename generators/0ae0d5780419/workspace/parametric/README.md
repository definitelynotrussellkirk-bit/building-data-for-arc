# 0ae0d5780419 transform-matching family

This proposed native family keeps the source task's three-panel analogy. The
private episode setting `match_policy` changes how transformed A is matched to B:

- `first_exact`: exact canonical Racket bytes; choose the first exact colored match.
- `last_exact`: choose the last exact colored match in the same six-code order.
- `first_shape`: ignore colors while matching shapes, then apply the first match.

All settings crop A, B, and C first. The inferred transform code is an
input-dependent intermediate that must be computed before C can be transformed.
Inputs are matched across settings and support 2–6 demonstrations plus 1–4
queries. The first two demonstrations respectively expose transform-priority
ambiguity and a recolored shape-only relation, so they identify all three
settings. Four queries cover 8×17, 14×23, 24×29, and substantive 30×29 inputs.
Exact 30-column width is impossible under three equal-width panels plus two
one-column separators (`width = 3n + 2`); 30×29 is the lawful maximum stress.
