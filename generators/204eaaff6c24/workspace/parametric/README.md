# Native parametric family: total count → anchor-indexed component count

`count_mode=all_cells` is the exact canonical rule: find the sole nonzero color,
count all of its cells, and output a horizontal bar of that length.

`count_mode=anchor_indexed_component` adds a non-collapsing sequential dependency:
segment the same-color four-connected components in row-major order, measure the
first component, use its size as a cyclic one-based selector among the remaining
components, then count the selected component and emit the same-color bar.
The selected component changes across examples; it cannot be known before the
anchor size is measured.

The input sampler is matched across settings, supports 2–6 demonstrations and
1–4 independently revealed queries, and is prefix-stable in both counts. The
first two constructive demonstrations use anchor sizes 1 and 3 and select target
sizes 2 and 5, defeating fixed-position, extreme-size, anchor-only, all-cells,
and off-by-one selector shortcuts. Query four is a substantive 30×30 scene with
eight components and the canonical lawful maximum of 30 foreground cells touching every boundary.

`adapter.py` is the native promotion boundary. `audit.py` checks the finite
rival set, prefix/public projection, protected-Racket labels, and an off-by-one
wrong-intermediate counterfactual. Native qualification and exact-source owner
acceptance remain separate; training admission is false.
