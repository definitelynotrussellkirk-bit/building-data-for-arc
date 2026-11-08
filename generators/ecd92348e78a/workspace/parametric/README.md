# Parametric bar-chart prototype for `ecd92348e78a`

This task-local proposal preserves the original family’s objects and measured
quantity: each nonzero input color contributes a bar whose length is its
bounding-box **height**. It adds two episode-level rule parameters:

| Parameter | Values | Canonical default |
| --- | --- | --- |
| `sort_order` | `descending`, `ascending` | `descending` |
| `bar_alignment` | `top`, `bottom` | `top` |

The two values are chosen once per episode, never per pair. The four resulting
Racket rules are minimal source mutations of the selected canonical rule. Reversing
sort order also decouples canvas height from the first column so taller later bars
are not truncated.
Every retained episode contains three demonstrations that distinguish the chosen
setting from all three alternatives, plus a held-out query on which all alternatives
also differ. Python oracles are checked against actual Racket execution before any
label is written.

Run from the packet root:

```sh
python3 review.py run python3 \
  generators/ecd92348e78a/workspace/parametric/prototype.py \
  --seeds 0 1 2 3 \
  --out-dir generators/ecd92348e78a/workspace/parametric/evidence
```

`episode-*-public.json` contains visible demonstrations and an unlabeled query.
`episode-*-private.json` retains parameters, the query label, source hashes,
program hashes, and rival-difference evidence. `rules/*.rkt` contains the four
matching executable rules. `summary.json` indexes the bundle.

This prototype is deliberately separate from `generator.py`; the selected
production default remains descending/top. The evidence is finite and does not
claim that these are the only plausible rule parameters.
