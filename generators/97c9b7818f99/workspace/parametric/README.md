# Parametric family for `97c9b7818f99`

This family keeps one private, episode-fixed `finish` setting:

- `fill_only` executes the byte-exact canonical Manhattan-nearest-seed fill.
- `highlight_smallest_region` first constructs the same unique-owner Voronoi
  partition, counts each seed's owned cells, selects the unique smallest region,
  and recolors all cells owned by that seed to `9`. Geometric tie cells remain `5`.

The alternative is deliberately sequential: the selected seed cannot be known
until the input-derived ownership partition and region-size table exist. The
counterfactual `skip_region_sizes.rkt` skips that intermediate and selects the
lowest seed color instead; the retained protected-Racket witness changes the
final grid.

The adapter supports 2–6 demonstrations and 1–4 requested queries. Production
qualification uses three demonstrations and four queries. For a fixed seed and
counts, both settings receive identical inputs. The fourth query is a substantive
30×30 scene; all ten maximum-count inputs are distinct. Public projections expose
only demonstrations and the currently revealed query input—not settings, program
text, query answers, future queries, seeds, or total-count hints.

From the packet extraction root:

```bash
python3 review.py run bash -lc \
  'PYTHONPATH=shared/runtime:src pytest -q generators/97c9b7818f99/tests/test_parametric_smallest_region.py'
python3 review.py run python3 generators/97c9b7818f99/workspace/parametric/audit.py \
  --out generators/97c9b7818f99/workspace/parametric/evidence/current/authoring-audit.json \
  --seed-start 0 --seed-count 18
python3 review.py run python3 -m arcpuzzles parametric qualify 97c9b7818f99 \
  --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/97c9b7818f99/qualification --summary
```

The finite rival audit is evidence for the declared hypotheses only; it is not a
proof that no other rule can fit the demonstrations. Qualification and this
inventory do not grant owner acceptance or admit data to training.
