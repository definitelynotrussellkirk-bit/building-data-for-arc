# b7564fb4b95d native parametric family

`transform_order=command_only` is the exact selected canonical Racket source.
`transform_order=command_then_reflect` first rotates the selected normalized
source according to the command marker, then horizontally reflects that
input-dependent orientation before centering it inside every frame.

Inputs are identical across settings. The sampler supports 2–6 demonstrations
and 1–4 queries with stable prefixes. The first two demonstrations use 90° and
270° commands on asymmetric source shapes, so they distinguish both settings
and refute identity, reflection-only, wrong-order, wrong-axis, and frame-only
shortcuts. The fourth query is a substantive 30×30 scene with three large,
distributed frames.

Sequential dependency: A selects and command-transforms the source; the
intermediate is the normalized command result; B reflects that exact result and
stamps it. The retained counterfactual reflects the source before the command,
which changes the final output because reflection and quarter-turn rotation do
not commute.
