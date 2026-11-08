# 892ae3bfe537

A black (`0`) grid contains two or three foreground colors. Every foreground
color appears exactly twice; its two cells identify opposite corners of an
axis-aligned bounding box. The output fills each complete inclusive box with
that color. A horizontal or vertical pair therefore becomes a line, while a
pair spanning both axes becomes a solid rectangle.

Generator version: `3.0.0`. Canonical rule hash: `5b511829e91b`.

## Curriculum

Every ordinary input contains exactly one true area pair plus one or two
collinear pairs. Their bounding boxes are disjoint and each box contains at
least three cells. This simultaneously refutes “fill only diagonal pairs,”
“fill only lines,” and “draw only the border.” Easy, medium, and hard anchor the
three canonical size/palette profiles `(6,9,3)`, `(8,8,3)`, and `(10,10,4)`
where the third coordinate counts background. Unbanded draws cycle through the
same three profiles.

Live exact override axes:

- `grid_h`: `6..10`
- `grid_w`: `8..10`
- `n_pairs`: `2..3`

Unknown, non-integral, and out-of-range overrides fail loudly. The sampler is
constructive at every advertised combination, with no rejection loop or silent
pair omission.

## Contracts

The module pins the canonical authority, exposes exact override observation,
validates the complete task-linked input grammar, provides an independent
Python bbox-fill oracle, and declares executable witnesses/rivals plus a
two-demo lesson-identifiability check. The canonical Racket authority was left
unchanged.

Final review evidence: 96 task-local tests pass; all 12 battery stages are
green; strict semantic support is 600/600; all 12 sampled lessons are
identifiable; the exact override matrix accepts 3960/3960 draws; and the
retained 100-lesson-per-band probe reports zero surviving declared rivals.
