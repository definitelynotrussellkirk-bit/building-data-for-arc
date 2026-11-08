# Pairwise-intersection gallery order

This native proposal keeps the exact canonical program as
`gallery_order=fixed_pairs` and adds `largest_overlap_first`.

The canonical rule computes the three binary intersections `AB`, `AC`, and
`BC`, paints them cyan, and emits them in that fixed order. The alternative
computes the same three masks, counts their occupied cells, and stably sorts
those derived masks by decreasing count with canonical `AB < AC < BC` ties.
Inputs are identical across settings; only demonstration outputs reveal the
private episode-fixed rule.

## Causal dependency

1. **A:** compute all three pairwise intersection masks and their occupied-cell
   counts from the three input panels.
2. **Intermediate:** the ordered source list `[(AB, mask, count),
   (AC, mask, count), (BC, mask, count)]`.
3. **B:** under `largest_overlap_first`, sort those derived records by count and
   stable pair identity, then hstack the masks.

B cannot choose its output order before A supplies the input-dependent overlap
counts. The retained protected-Racket witness replaces those counts with a
wrong fixed ranking and changes the final gallery.

## Supported requests and stress

`generate(seed, settings, demos=3, queries=4)` accepts exact seeds in
`0..2**63-1`, 2–6 demonstrations, and 1–4 queries independently. Query and
training prefixes are stable and setting-independent. The first demonstration
has three distinct overlap sizes; the second has an `AC/BC` tie that teaches the
stable tie break. Four queries cover heights 5, 13, 23, and 30. The 30×17 query
contains more than 210 foreground cells and touches every outer boundary.

Exact 30×30 is not lawful for the exact canonical authority: it slices three
fixed five-column panels at columns `0..4`, `6..10`, and `12..16`, so its
semantic input width is 17. The separate sampler therefore extends the natural
height boundary to 30 without adding ignored columns or making the private
setting visible from input dimensions.

`public_turn` exposes all demonstrations and exactly one selected query input.
It includes no settings, program, answer, future query, query index, or total
query count; the first turn is byte-identical for one-query and four-query
requests.

## Reproduce

From the outer packet folder:

```bash
python3 review.py run python3 -m pytest -q \
  generators/1216927d148b/tests/test_parametric_gallery_order.py
python3 review.py run python3 \
  generators/1216927d148b/workspace/parametric/audit.py \
  --seed 19 --out ../checks/1216927d148b/self-audit
python3 review.py run python3 -m arcpuzzles parametric qualify 1216927d148b \
  --out ../checks/1216927d148b/qualification --summary
```

Qualification and bounded self-audit are reviewer evidence only. Exact-source
owner acceptance remains pending, and training admission remains false.
