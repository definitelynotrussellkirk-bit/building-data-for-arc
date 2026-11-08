# Additive transpose with an optional mirrored-pair bridge

`mode=copy_only` is the selected canonical program byte for byte. It copies every
nonzero cell to its transposed coordinate while preserving the input.

`mode=copy_then_bridge` is sequential. Step A performs the canonical additive
transpose. Step B scans that completed intermediate for equal nonzero mirrored
pairs `(r,c)` and `(c,r)` with `r<c`, then fills the complete anti-diagonal segment
between each pair. The input sampler occupies at most one member of every
transpose orbit, so the bridge stage has no eligible pair before Step A. Skipping
Step A therefore leaves the input unchanged, while the full rule adds substantive
segments. Distinct anti-diagonal sums prevent bridge conflicts in the admitted
sampler.

The full six-demo/four-query bank is built before slicing. Inputs are identical
across settings; every pair distinguishes the settings. Counts are independent:
2–6 demonstrations and 1–4 queries. The final query is a 30×30 boundary case with
24 source orbits and long bridge spans across the canvas.

## Bounded audit

`audit.py` replays both programs with protected Racket at four seeds and then
checks matched inputs, distinct pairs, setting separation, and four plausible
rivals over a configurable seed range. The retained 256-seed run checked 512
full episodes and 5,120 setting-paired examples. It initially found seed 228,
where only distance-2/3 bridges let a midpoint-only rival survive; the sampler
now forces a span of at least four in every scene and the regression covers all
256 audited seeds. Finite screening is not a proof of unique induction.
