# Framed Voronoi distance-metric family

**Status:** proposed source-bound authoring artifact; not owner-qualified,
accepted, or admitted to training.

The private episode setting `metric` is fixed across all pairs:

- `manhattan` — exact byte-for-byte canonical default;
- `chebyshev` — distance is `max(|dr|, |dc|)`;
- `euclidean_sq` — distance is `dr² + dc²`.

The same input bank is used for every setting. For each interior cell, step A
computes the complete seed-distance vector under the selected metric. Step B
uses that input-dependent vector to find the minimum and either paint the unique
winning seed color or retain black for a cross-color tie. The first two
constructive demonstrations distinguish all three metrics and refute same-metric
lowest/highest/first-seed tie rules plus vertical-only, horizontal-only, and two
weighted-axis distances.

The family accepts 2–6 demonstrations and exactly four queries. Query generation
is independent of demonstration count and shuffles a complete role bank before
sequential presentation. The four roles cover a substantive 30×30 scene, 9×26
thin-wide geometry, 26×11 tall-narrow geometry, and a boundary-seed mixed case.
All scenes contain distinct-colored seeds, visible ties under every declared
metric, and territory for every seed.

From the packet root, protected-Racket evidence can be generated with:

```bash
python3 review.py run python3 \
  generators/9ea9f1e62275/workspace/parametric/prototype.py \
  --all-settings --seed 0 --seed 17 --demos 2 --queries 4 \
  --out ../checks/9ea9f1e62275/racket-example
```

Native source inventory and authoring preflight remain separate owner-facing
steps. Programs, settings, future inputs, answers, and evidence files are
controller-private; public projection uses the packet's shared preview helper.
