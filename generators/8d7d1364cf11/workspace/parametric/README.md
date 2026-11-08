# Proposed episode-level anchor and canvas parameters

This is a **prototype**, not part of the selected canonical generator or its
approval path. It preserves the family’s core reasoning: identify multicolor
source templates, use singleton-dot colors to select a template, translate a
whole template to every productive dot, and ignore absent-color decoys.

Two bounded values are chosen once per episode and remain fixed across all
three demonstrations and the query:

| parameter | values | canonical/default |
|---|---|---|
| `anchor_mode` | `matching_cell`, `template_origin` | `matching_cell` |
| `canvas_mode` | `clear`, `preserve_input` | `clear` |

`matching_cell` aligns the uniquely color-matched source cell to the dot;
`template_origin` aligns the source bounding-box origin. `clear` stamps onto a
fresh all-4 grid; `preserve_input` stamps onto a copy of the input. The four
exact Racket programs are materialized independently. Episode construction
retains only lawful inputs where all four settings produce different outputs,
so every demonstration rejects all three declared parameter rivals before the
query. Public challenge files omit the hidden values, Racket text, and query
answers.

From the packet root:

```bash
python3 review.py run python3 \
  generators/8d7d1364cf11/workspace/parametric/verify.py \
  --seed 20261019 \
  --out ../checks/parametric/report.json \
  --artifact-dir generators/8d7d1364cf11/workspace/parametric/materialized
```

The report records source hashes, exact Racket text and hashes, the bundled
runtime identity, 16 complete episode pairs, 64 Racket executions, all declared
rival outputs, and an explicit lawful disagreement. This finite four-setting
probe does not add a production parametric API or approve the variants.
