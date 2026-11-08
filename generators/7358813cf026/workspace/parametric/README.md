# 7358813cf026 parametric singleton policy

The default `erase_all` setting returns the exact canonical Racket bytes.
`protect_largest_color` first selects the unique largest same-color object,
uses its color as an input-dependent intermediate, and then preserves remote
singletons of that color while erasing all other singletons. Two demonstrations
separate the finite settings; query four is a distributed 30×30 stress case.

`wrong_anchor.rkt` is a protected-Racket causal ablation that substitutes the
second-largest object's color.
