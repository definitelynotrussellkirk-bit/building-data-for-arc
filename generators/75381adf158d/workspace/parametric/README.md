# Native parametric family: enclosed holes and largest-hole escape

The default `canonical` setting is the selected program byte-for-byte: fill all
zero-regions that cannot reach the grid border with color 8.

`largest_escape` is deliberately sequential. Stage A performs the canonical
fill. Stage B reads the new color-8 components, selects the unique largest
filled hole, and paints a straight color-8 escape line from its center to the
nearest outer border. Inputs contain no color 8, so Stage B has no trigger
without Stage A. `smallest_escape.rkt` is retained as a protected
wrong-intermediate counterfactual.

The matched sampler provides 2–6 demonstrations and 1–4 private queries,
including a distributed 30×30 case. `audit.py` checks matched inputs,
identifiability against named rivals, count boundaries, causal separations, and
scene diversity over a bounded seed sweep.

This is reviewer-side authoring work only. Owner source integration, native
qualification/acceptance, variant approval, and training admission remain
separate.
