# Native parametric family: residual component selection

The default `residual_policy=all` is the exact canonical normalized green-minus-gray subtraction. The alternative `largest_component` first computes the same input-dependent residual, then selects its unique largest four-connected component before cropping and painting it green.

The family supports 2–6 demonstrations and 1–4 queries with matched inputs across settings. Every episode stores four distinct controller-side queries; the fourth is a populated 30×30 stress case. The bounded audit checks prefix stability, public first-turn invariance, named rivals, matched inputs, and protected-Racket labels.

Sequential dependency: normalized subtraction produces the residual cell set; only then can component membership and size be computed. `rules/wrong_intermediate.rkt` applies the component selector to the connected source instead of the residual and is used for the protected causal witness.
