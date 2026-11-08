# `edge_policy` parametric prototype

This isolated **proposed prototype** keeps the canonical lattice parsing, marker
shape, and row-and-column parity selector. It varies one episode-level rule:

- `clip` — canonical/default: matching partial terminal cells are destinations;
  marker pixels are clipped to the cell bounds.
- `full_only` — matching partial terminal cells are skipped; only full 3x3 cells
  are stamped.

The production generator and canonical authority remain separate. Each retained
episode fixes one setting across **4 demonstrations and 4 distinct queries**.
Every input contains output-visible partial destinations, so the demonstrations
uniquely distinguish the two settings.

From the packet extraction root:

```sh
python3 review.py run python3 \
  generators/a76216bfa3e8/workspace/parametric/build_evidence.py \
  --demo-count 4 --query-count 4 \
  --out-dir ../checks/parametric/a762-edge-policy-v1
```

The builder executes every retained label with the bundled Racket bridge, checks
both rule settings on every pair, verifies exact canonical parity for `clip`,
and writes opaque public challenge filenames derived only from visible demos and
query inputs. Private files retain settings, seeds, Racket source, and query
answers. This evidence is bounded and does not approve or promote the variant.
