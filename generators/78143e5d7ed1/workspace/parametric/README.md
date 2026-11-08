# Native parametric sort-and-pack family

`sort_direction=smallest_first` is the exact canonical Racket program.
`largest_first` reverses the complete `(cell count, bbox height, bbox width,
color)` lexicographic order while retaining tight crops, one-column separators,
and bottom alignment.

The sampler is setting-independent. Its first two demonstrations jointly expose
all four sort keys and a sparse-bbox/cell-count conflict. Every episode has four
private queries; the fourth is a 30×30 seven-component case with 43 foreground
cells, boundary contacts on all four sides, and a 28-column packed answer.

Causal chain: **A** extracts every component and computes its full input-derived
sort key; the **intermediate** is the ordered crop list; **B** bottom-aligns and
packs those crops. `rules/wrong_bbox_area_largest.rkt` replaces cell count with
bbox area in that intermediate and is retained only as a counterfactual witness.

Run the bounded authoring audit with:

```bash
python3 audit.py --out evidence/current/authoring-audit.json
```
