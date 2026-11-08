# Review workspace for `a7a47f5cee60`

`review_probe.py` is an independent component/contact-graph analyzer for future reviewers. It does not import graph or articulation helpers from `generator.py`.

Examples from the packet repository root:

```bash
python3 generators/a7a47f5cee60/workspace/review_probe.py --seed 19 --sample-index 2 --texture cycle
python3 generators/a7a47f5cee60/workspace/review_probe.py --input path/to/grid.json
```

The durable regression suite is `../tests/test_articulation_curriculum.py`. It covers canonical ownership, independent rule equivalence, every exact-control corner and rejection, malformed inputs, topology profiles, three declared rivals, all query rotations, input-cyan frequency, explicit degenerates, and this probe's consistency.

Important retained failure: `../counterexamples/query-rotation-v3.0.0.json` is the exact lesson that forced the final two-cycle schedule. Do not simplify the four-slot schedule without rerunning the 100-lessons-per-band census with `--rotate-query` and the all-holdout task test.
