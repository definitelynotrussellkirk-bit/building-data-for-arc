# Workspace for 671a9af906aa

The selected implementation is `../generator.py`; workspace files are support artifacts and are never selected automatically.

- `generator_before.py` — immutable copy of the selected baseline used for before/after comparison.
- `maze_probe.py` — compact structural/semantic sampler for individual generated mazes.
- `lesson_probe.py` — source-bound census over actual five-demo lessons. It imports the generator's declared competitors/witnesses, checks every cyclic schedule residue, reports uniqueness and domain limits, and exits nonzero below its documented quality floor.

Reproduce the final large census from packet root:

```sh
cd repo
python3 generators/671a9af906aa/workspace/lesson_probe.py \
  --repo . \
  --generator generators/671a9af906aa/generator.py \
  --out ../checks/lesson_probe_100_per_band.json \
  --lessons-per-band 100 \
  --seed-base 6710900
```

The probe uses `generator.rule_mirror` for volume; independent Racket `rule_smoke`, `semantic_gate`, and `authority_sync` reports are required corroboration. Its claims are sampled and limited to the generator's documented domain and declared rivals.

`shape_support_probe.py` checks one finite 25-scene size/profile cycle per difficulty and executes the unchanged canonical Racket rule on all six size/profile combinations per band plus canonical pairs. Reproduce from the packet root:

```sh
WORK/.venv/bin/python review.py run ../.venv/bin/python \
  generators/671a9af906aa/workspace/shape_support_probe.py \
  --out ../checks/671a9af906aa/shape_support_racket.json
```
