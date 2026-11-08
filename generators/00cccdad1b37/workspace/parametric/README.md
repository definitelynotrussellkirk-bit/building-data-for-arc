# Parametric shortest-path family

`route_segment=whole` is the exact canonical rule: mark every background cell
that lies on every shortest path from red start to green goal. The alternative
`route_segment=after_gate` first computes those mandatory cells, selects the
input-dependent one nearest the route midpoint (ties favor progress toward the
goal), then marks cells mandatory on the selected gate-to-goal suffix.

The input sampler is independent of the setting. It creates two to four full
barriers with distinct gaps, alternates orientation and direction, retains
partial shortest-path cells, supports 2–6 demonstrations and four distinct
queries, and includes a substantive 30×30 query.

From the packet outer directory:

```bash
python3 review.py run python3 -m pytest \
  generators/00cccdad1b37/tests/test_parametric_shortest_paths.py -q
python3 review.py run python3 -m arcpuzzles.review_base_preflight \
  00cccdad1b37 --out ../checks/00cccdad1b37/qualification
```

This is authoring evidence only. Owner source review, native acceptance, and any
training admission remain separate.
