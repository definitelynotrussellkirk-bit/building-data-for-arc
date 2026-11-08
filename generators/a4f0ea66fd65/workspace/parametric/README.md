# Native vector-copy repeat family

`single` is the exact selected canonical program. `decoy_size` preserves the
red-to-green vector and cyan-source reasoning, but first measures the connected
color-6/7 decoy and uses its occupied-cell count as the number of successive
vector copies to paint.

The sampler is deterministic and setting-neutral, supports 2–6 demonstrations
and 1–4 prefix-stable queries, and reserves a distributed 30×30 scene as query
four. `fixed-three-counterfactual.rkt` replaces the measured repeat count with 3.
