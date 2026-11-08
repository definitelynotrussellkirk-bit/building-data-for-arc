# 84aeaf4792a8 — Compare all components up to rotation

Version: `4.0.0`. Selected Racket authority: `f2869336c461` (unchanged).

Find monochromatic, four-connected foreground components on background 0. Order
them by the minimum row of their bounding box, then its minimum column. Compare
their occupied coordinates after translation and any of the four rotations;
reflections are distinct. Return an N×N matrix with 5 on the diagonal, 8 for a
matching pair, and 0 otherwise. Component colors do not determine shape identity
or output order.

The input sampler emits 2–6 components of 3–5 cells, each fitting a 3×3 box.
It includes all 19 rotation classes in that domain, including chiral pairs.
An 8–18 by 12–22 canvas uses six separated placement slots; repeated component
colors are allowed. The exact controls are `grid_h`, `grid_w`, `n_components`,
`n_families`, and `n_distinct_colors`. Family and color counts cannot exceed an
explicit component count; otherwise the component count grows to accommodate
them. Unknown controls and noninteger values fail visibly.

Default four-pair lessons use three demonstrations and one query. Even indices
teach chiral nonmatches and quarter-turn matches in four-component canonical
size/palette profiles; phases 0 and 2 use partitions (2,1,1) and (2,2). Odd indices
broaden counts, colors, and set-partition proposals. Every four consecutive
unconstrained draws preserve refutations of the six declared rivals when any
single pair becomes the query. This finite rival contract does not promise
universal identifiability or hold under arbitrary exact overrides.

The six-slot placement restriction and weighted size distribution are deliberate.
Exact uniformity of final output matrices is not claimed. Current rationale and
validation pointers are in `notes.md`; the reusable authoring probe is in
`workspace/probe_distribution.py`. Catalog approval remains independently derived.
