# 067f6e037e97 parametric growth scope

The default `all_nonzero` setting returns the exact canonical Racket bytes.
`largest_object_color` first selects the unique largest same-color object, uses
its color as an input-dependent intermediate, then grows every input cell of
that color (including a deliberately remote singleton).  Two demonstrations
separate the finite settings; query four is a distributed 30×30 stress case.

`wrong_anchor.rkt` is a protected-Racket causal ablation that substitutes the
second-largest object's color.
