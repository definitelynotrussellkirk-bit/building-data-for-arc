# Parametric motif-order family

The canonical default is byte-identical to the selected `2314acbb67be` Racket
rule. `order_key` chooses descending occupied-cell count or descending bounding-
box area. Inputs are matched across settings for the same seed and count request.

Sequential dependency: A discovers each motif, crops it, measures the selected
input-dependent score, and produces a deterministic ordered crop list. B cannot
pack the gallery until it consumes that order; the protected witness substitutes
the cell-count order for the area order as a `wrong_order` counterfactual.

The deterministic sampler supports 2–6 demonstrations and 1–4 queries. Every
scene contains a size/area inversion, and the four-query schedule ends with an
exact 30×30 scene containing 54 motif cells. `audit.py` checks a finite plausible
rival set and grants no owner acceptance or training admission.
