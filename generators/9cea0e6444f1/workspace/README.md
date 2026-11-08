# Workspace

The selected implementation is `../generator.py`.

`probe_semantics.py` is a source-bound, Racket-free regression probe. It samples all three difficulty bands, checks that every declared core rival disagrees with the Python oracle, measures exact axis support, and scans consecutive three-example windows for the decoy-dependent all-nonzero shortcut. The Racket-backed semantic gate and lesson census remain the labeling authority.

Example from the packet `WORK/repo` directory:

```bash
PYTHONPATH=src:shared/runtime python3 generators/9cea0e6444f1/workspace/probe_semantics.py --per-band 100 --out ../checks/semantic-probe.json
```
