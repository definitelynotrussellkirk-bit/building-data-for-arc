# Boundary-palette prototype

Status: **prototype 1.1.0**, with no production or training approval.

The hidden `boundary_palette` is fixed once per episode: even seeds select
canonical `ends1_edges4`, odd seeds select proposed `ends4_edges1`. The variant
swaps only the zero-opposing-pair and exactly-one-opposing-pair output colors.
Color-5 source cells, geometry, preserved non-5 cells, and color-2 interiors keep
their existing roles. Both retained Racket programs and production remain unchanged.

## Generate four queries

From the outer packet directory, use a fresh output path:

```bash
python3 review.py run python3 \
  generators/22d1f016cb3d/workspace/parametric/prototype.py \
  --n-train 4 --n-test 4 \
  --out ../checks/parametric-new/evidence.json \
  --write-public ../checks/parametric-new/public
```

This produces one episode per palette, each with four demonstrations and four
queries. `--n-train` and `--n-test` are independent literal integer counts in
`1..32`; both default to four. The Python API is
`build_episode(root=..., seed=..., n_train=4, n_test=4)`.

All inputs are distinct across both splits. Sampling is deterministic, has a
budget of 32 attempts per requested pair, and fails explicitly on exhausted
support. Changing only the query count preserves the demonstrations and query
prefix. Every returned output is executed through its matching Racket program;
the Python transform is an assertion mirror, with no fallback on runtime failure.

## Public and private outputs

Give consumers only the `public/` directory. Each filename is the full SHA-256
of the exact visible bytes, followed by `.json`. The shared
`reviewer_support.public_challenge_bytes` and `public_challenge_id` helpers define
both serialization and identity. Files contain only demonstration inputs/outputs
and query inputs, including a terminal newline. Parameter values, seeds, source
code, sample indices and query answers cannot affect public bytes or names.

`write_public_challenges(challenges, out=...)` sorts returned rows by public ID,
rejects duplicate visible episodes, and preflights destination collisions before
writing. It refuses overwrites. Changing pair order changes the visible payload
and its ID. The setting-to-ID map and query answers remain in the private report;
the CLI rejects a private report path within the public directory.

The two content-named files under `examples/public/` are the current 4/4 public
examples. Share only that directory. The setting-named files directly under
`examples/` are inherited private authoring fixtures: the packet prohibits
deleting baseline files. Prior one-query evidence is retained under
`evidence/reviewer-reported/`; its historical manifest describes old bytes and
is not current verification.

## Verification and limits

```bash
python3 review.py run python3 -m pytest -q \
  generators/22d1f016cb3d/tests/test_parametric_boundary_palette.py \
  generators/22d1f016cb3d/tests/test_parametric_export_counts.py
```

Current evidence and source hashes are in `evidence/manifest.json`, with the
Racket-backed episode report in `evidence/four-query-export.json`. It filters the
two allowed palettes using demonstrations only, then records survivor agreement
for each query. Query answers never filter candidate settings.

Identifiability is bounded to these two declared palette alternatives. One
rectangular demonstration does not rule out the separate neighbor-degree
shortcut. This work does not claim universal teachability, model performance,
production approval, or training admission. The supported upper bound was
exercised at 32/32 for the recorded seed; sampling exhaustion remains possible
and raises rather than silently returning fewer pairs.
