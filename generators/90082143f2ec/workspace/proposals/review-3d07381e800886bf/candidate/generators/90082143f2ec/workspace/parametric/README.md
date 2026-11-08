# Proposed `axis_policy` extension for `90082143f2ec`

Status: **task-local prototype only**. It does not edit the canonical ledger,
selected production generator, approval state, or training-admission state.

The unchanged task computes row modes, column modes, and their coherence. The
new episode-fixed parameter changes only the final selection:

| `axis_policy` | behavior |
|---|---|
| `more_coherent` | Canonical behavior. Uses the axis with greater coherence. The returned program is byte-for-byte the canonical Racket authority. |
| `less_coherent` | Uses the other axis by changing `>` to `<` in the final coherence comparison. Because the newly selected non-dominant slices may tie, this variant also lexically shadows `mode-list` with the generator mirror's explicit highest-count/lowest-color tie rule. |

For identification evidence, two fixed-axis rivals are also executed:
`always_rows` and `always_columns`. Every lawful sampled input has different
row-axis and column-axis answers, and every demonstration set covers both
orientations. Therefore three demonstrations identify either episode setting
without consulting query answers.

Adjacent seeds form an A/B pair. Seeds `2k` and `2k+1` share all input grids;
seed parity selects the setting once for the full episode. Counts are bounded to
3–8 demonstrations and 1–8 queries. All labels and rival predictions execute
through the protected Racket bridge, then are checked against a component oracle
from the unchanged generator's semantic observables. The canonical default is
not wrapped or rewritten; its source remains byte-for-byte exact.

Generate a retained 3-demo / 4-query paired witness from the outer extraction directory (the directory containing `review.py` and `WORK/`):

```bash
python3 review.py run python3 \
  generators/90082143f2ec/workspace/parametric/prototype.py \
  --pair-seed 0 --demos 3 --queries 4 --difficulty medium \
  --out ../checks/parametric/axis-policy-v1
```

`public/` contains only demonstrations and query inputs. Query answers, setting,
program text, execution records, and certificates remain under `private/` or in
`summary.json`. Public IDs hash exactly the canonical visible bytes. Batch export
rejects duplicate visible payloads before creating any files.

## Limits

- This is a proposed two-value parameter, not an approved production API.
- The certificate is complete only for the four declared variants.
- Sampling stays within the current finite generator schedule and lawful domain.
- Retained evidence establishes the recorded episodes, not universal coverage.
