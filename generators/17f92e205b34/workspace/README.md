# Workspace

The selected implementation is `../generator.py`. This directory contains a
reusable input-support probe; it does not select a draft or compute training
labels.

From the extracted packet's outer directory:

```sh
python3 review.py run python3 generators/17f92e205b34/workspace/probe_distribution.py --seed 0 --per-band 200 --out ../checks/distribution-replay.json
```

The wrapper runs the payload from `WORK/repo`. Use an output path that does not
replace retained evidence. The script loads the selected generator, iterates its
actual axis and witness declarations, and records the source hash, seed, exact
indices, profile counts, axis histograms and distinct input hashes per band.
The recorded final run used seed 0 and indices 0..199 in each of easy, medium and
hard: 600 valid draws, 200 distinct inputs in each band. Uniqueness is per band;
this report does not establish 600 globally distinct inputs.

For actual Racket labels and lesson checks use the public `arcpuzzles apply` and
`lesson-census` commands recorded in the review's `RESULTS.json`. The input probe
cannot establish label correctness or lesson identifiability. Portable task
regressions live in `../tests/test_reflection_distribution.py`; minimized semantic
examples with retained actual Racket outputs live in `../counterexamples/`.
