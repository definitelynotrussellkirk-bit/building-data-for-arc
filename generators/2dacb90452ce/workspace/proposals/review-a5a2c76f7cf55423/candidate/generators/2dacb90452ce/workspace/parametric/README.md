# `2dacb90452ce` scale-factor prototype

This is an isolated **proposed** parametric extension. It does not modify the
approved production generator or canonical authority.

The episode-fixed parameter is:

- `scale_factor=2` — the exact canonical Racket program, byte for byte.
- `scale_factor=3` — the same cellwise uniform expansion rule with each input
  cell replaced by a solid 3×3 block.

The object roles and reasoning stay unchanged: inspect each input cell, preserve
its color, and expand it uniformly in both axes. Only the small repeat count
changes. Inputs come from the selected production generator and are independent
of the hidden setting. Each retained episode has two labeled demonstrations and
four distinct unlabeled public queries. All chosen and counterfactual labels are
executed through the bundled Racket bridge.

From the packet's outer directory, build evidence with:

```bash
python3 review.py run python3 \
  generators/2dacb90452ce/workspace/parametric/prototype.py \
  --seed 20261022 \
  --demo-count 2 \
  --query-count 4 \
  --out ../checks/parametric/scale-factor-v1
```

Public filenames are hashes of exact visible challenge bytes. Public files omit
seeds, parameter values, Racket programs, private metadata, and query answers.
The command refuses to overwrite an existing evidence directory.
