# Workspace

`curriculum_probe.py` is a reusable, source-bound audit for the selected generator. It discovers canonical shortcuts and lesson competitors from the generator's live declarations rather than copying rival names into the tool.

From the packet root:

```bash
python3 run_with_racket.py python3 \
  generators/ed98575459d2/workspace/curriculum_probe.py \
  --seed 20261004 \
  --lessons-per-band 25 \
  --out ../checks/curriculum-probe-final.json
```

The report checks:

- every declared canonical shortcut against every official pair,
- all five cyclic starts in each of the default/easy/medium/hard schedules,
- whether every complete five-demo lesson refutes every declared competitor,
- a production-sampler census with profile and unique-input counts, and
- one ordinary generated counterexample for each canonical-fitting shortcut.

This tool uses the Python mirror for high-volume semantic comparisons. Confirm a decisive witness against the canonical Racket authority with the public `arcpuzzles apply` command, as retained under `checks/shortcut/ed98575459d2/`.
