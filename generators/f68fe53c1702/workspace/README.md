# Authoring probes for f68fe53c1702

These tools are for generator review, not visible-only solving.

- `probe_geometry.py` checks every declared bbox size/count combination for rich-layout capacity and extrema, plus public-generation canvas boundaries. It computes no reference labels. Pass `--out PATH` to retain its source-bound JSON report.
- `reproduce_witness.py` replays the generated seed-117, sample-1 4x5 counterexample, checks both declared shortcuts against all labeled canonical pairs, and verifies the witness through the public Racket API. It reads canonical labels and must stay closed during solves.

From the outer packet root, payloads run in `WORK/repo`:

```sh
python3 review.py run python3 generators/f68fe53c1702/workspace/probe_geometry.py --out ../checks/geometry-new.json
python3 review.py run python3 generators/f68fe53c1702/workspace/reproduce_witness.py --out ../checks/witness-new.json
```

Use a fresh output filename for another evidence run. The retained witness is `../counterexamples/distributed-extrema.json` relative to this workspace. Python 3.12+, NumPy, Pillow and the packet's Racket wrapper are sufficient for these probes; pytest is needed for the separate focused regression suite. Exact executed commands and interpreter paths are in the return's `RESULTS.json`.
