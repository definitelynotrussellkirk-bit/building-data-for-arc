# Parametric framed transform transfer

The private episode parameter `applications` has two values:

- `once` is the exact selected canonical Racket program: infer the transform
  mapping framed interior A to B and apply it once to C.
- `twice` infers the same input-dependent transform and applies it twice to C.

Inputs are matched across settings.  Two through six demonstrations are
supported independently of one through four stable query prefixes.  The fourth
query is a substantive 30x30 scene with three 30x9 frames and dense 28x7
interiors; it uses a shape-preserving reflection so the canonical parser and
both programs remain lawful.

The first two demonstrations are constructive teaching witnesses: a
color-keyed quarter turn whose occupancy alone is fully symmetric, followed by
an asymmetric left-right reflection.  Together they distinguish once/twice and
reject the finite rivals declared in `adapter.py` without consulting query
answers.
