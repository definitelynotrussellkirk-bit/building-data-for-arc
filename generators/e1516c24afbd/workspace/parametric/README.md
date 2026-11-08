# Proposed episode-level rule parameters for `e1516c24afbd`

This directory is a task-local, **unapproved** prototype. It does not modify the
selected production Racket rule or the generator's canonical API.

The prototype chooses two small values exactly once per episode:

| parameter | values | canonical default |
|---|---|---|
| `target_state` | `00`, `11` | `00` |
| `output_color` | `2`, `3` | `2` |

`00` means both aligned cells in the stacked panels are empty; `11` means both
are occupied. Every retained input uses panel colors 1 and 9 and contains all
four occupancy states (`00`, `10`, `01`, `11`). Consequently, each labeled
training pair refutes each of the other three parameter settings. The default
materialization is byte-for-byte the canonical Racket source.

Run the retained executable check from the packet root:

```bash
python3 review.py run python3 generators/e1516c24afbd/workspace/parametric/verify.py \
  --out ../checks/parametric/report.json \
  --artifact-dir generators/e1516c24afbd/workspace/parametric/materialized
```

The verifier replays the canonical labeled pairs with Racket, executes all four
materialized Racket rules on every retained pair, cross-checks them against the
Python mirror, and writes public challenges without parameter metadata, source,
or query labels.
