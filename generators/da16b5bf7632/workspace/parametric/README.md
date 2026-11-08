# Native parametric hole-sort family

`sort_direction=most_holes_first` is the exact canonical Racket program.
`fewest_holes_first` reverses only the input-derived enclosed-hole ordering;
reading-order ties, tight crops, top alignment, and one-column separators remain
unchanged.

The sampler is setting-independent. Its first two demonstrations include hole
counts 0–3, equal-hole ties, sparse bounding boxes, and source-order/color
decoys. Every episode has four private queries; the fourth is a 30×30 six-object
case with 55 foreground cells, all four boundary contacts, and a 27-column
packed answer.

Causal chain: **A** crops every component and counts its enclosed zero regions;
the **intermediate** is the hole-count-ordered crop list; **B** top-aligns and
packs that list. `rules/wrong_bbox_area_fewest.rkt` substitutes bounding-box area
for hole count and is retained only as a protected-Racket counterfactual.

Run the bounded authoring audit with:

```bash
python3 audit.py --out evidence/current/authoring-audit.json
```
