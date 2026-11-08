# Workspace

The selected implementation is `../generator.py`; workspace files are retained probes and are not selected automatically.

## `reference_probe.py`

A source-bound independent audit for the selected generator. It:

- recomputes canonical outputs with an independent BFS oracle;
- verifies every declared canonical shortcut really fits every canonical pair;
- enumerates all five cyclic schedule starts in easy/medium/hard;
- holds each of the six materialized pairs out as query and checks every declared rival;
- exercises exact override boundaries and observes them back from emitted grids;
- optionally checks canonical grids and the exact tie counterexample through the public Racket catalog API.

Run from `repo/` through the packet wrapper:

```bash
python3 ../run_with_racket.py python3 generators/28f91ad53b1b/workspace/reference_probe.py \
  --seeds-per-band 20 --racket --out ../checks/reference-probe-final.json
```

The final retained report is bound to generator SHA-256 `74d9067b1305a5990585f0ddd5739405b51d92c2d46f8eeb4379a6632d2e2dd3` and records the exact canonical-fitting tie shortcut counterexample used in `QUESTION_ANSWER.md`.
