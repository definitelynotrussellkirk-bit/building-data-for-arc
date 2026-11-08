# Proposed `output_transform` prototype

This task-local prototype keeps the production input family and chooses one
hidden output transformation once per episode:

- `identity` — the exact canonical Racket program and default setting;
- `horizontal_mirror` — crop the left panel, then mirror columns;
- `vertical_flip` — crop the left panel, then reverse rows.

Every retained input is lawful under the production generator and is filtered
so all three settings produce pairwise-distinct outputs. Demonstration and query
counts are independent. Public files contain labeled demonstrations and query
inputs only; their opaque names are SHA-256 hashes of those exact visible bytes.
The setting, seed, Racket source, and query answers remain private. Batch exports
are sorted by public ID and fail rather than emit duplicate visible payloads.

From the outer extraction directory, build one exact Racket-backed episode per
setting with four distinct queries each:

```bash
python3 review.py run python3 generators/5d1263287a4f/workspace/parametric/verify.py \
  --out ../checks/parametric/5d1263287a4f-output-transform-v1 \
  --start-seed 20261023 --demo-count 4 --query-count 4
```

This is a proposed extension, not approval of alternate rules or a change to the
canonical production authority.
