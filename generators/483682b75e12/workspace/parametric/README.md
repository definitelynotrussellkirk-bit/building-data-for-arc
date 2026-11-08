# Parametric component motion for `483682b75e12`

`motion_mode=own_size` is the exact selected canonical Racket rule: each
non-7/non-8 4-connected component moves upward by its own cell count.

`motion_mode=complement_to_largest` first discovers all components and computes
the input-dependent largest size `K`; only then can it move a component of size
`s` upward by `K - s + 1`.  Thus the global maximum is a causal intermediate,
not an episode label or cosmetic second step.

The sampler is independent of the private setting, supports 2–6 demonstrations
and 1–4 distinct queries, and keeps a fourth 30×30 boundary-spanning query.
The first two demonstrations contain multiple sizes and multicolor connectivity,
so both admitted programs and the declared shortcut inventory are distinguished
from demonstration labels alone.  Public consumers receive only visible
train/test challenge content; settings, programs, future queries, and query
answers remain private in the native exporter.
