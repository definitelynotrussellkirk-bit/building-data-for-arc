# `e2bc70324918` parametric endpoint-stamp family

`stamp_mode` is selected once per episode.

- `copy` — exact canonical default: extract the normalized sparse glyph and stamp it at both line endpoints.
- `dilate4` — stage A extracts the same input-dependent glyph and computes its one-cell orthogonal dilation; stage B stamps that resulting cell set at both endpoints.

The minimum two-demo lesson deliberately uses distinct source templates with the same 3×3 bounding box, so neither a fixed stamp nor a bounding-box-only rule can replace stage A. The sampler uses identical visible inputs across settings, supports 2–6 demonstrations and exactly four queries, keeps the query bank independent of demo count, and reserves the final query for a substantive 30×30 stress case. `adapter.py` emits claims; protected Racket parity is retained in `evidence/self-audit.json`, the authoring preflight, and the causal witness.
