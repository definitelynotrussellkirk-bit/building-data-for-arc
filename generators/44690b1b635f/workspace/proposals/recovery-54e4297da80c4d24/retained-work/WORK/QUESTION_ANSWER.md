# qwen9-data-value

The additional gate with the highest expected value is a **color-normalized
template-shortcut gate**. Sample a bounded number of lessons per band, map
colors to semantic roles (background, wall, unique origin marker, repeated arm
marker), and measure both unique normalized topology support and held-out
prediction by an exact/nearest role-template lookup.

A reproducible failure is this task's v3.0.0 distribution: despite correct
labels and hundreds of exact colored grids, it had only 42 role masks across
all bands, and the retained audit's normalized lookup predicted 768/768 sampled
outputs. That data can reward memorizing a tiny layout table instead of learning
reachability and distance parity.

A possible false positive is an intentionally finite anchor curriculum whose
purpose is palette invariance or exact canonical rehearsal. Mitigate it by
requiring both low normalized support **and** high held-out template accuracy,
then allow a declared anchor-only exception while still checking the broader
mixed distribution.

The cheapest test needs no model training: generate 128–256 examples per band,
reuse their existing Racket labels, canonicalize roles, split by normalized
layout, and evaluate the lookup. Flag a generator when new-layout rate is near
zero and held-out template accuracy exceeds a threshold such as 95%. Run a few
source-bound Racket spot checks only to ensure normalization did not merge
semantically different roles.
