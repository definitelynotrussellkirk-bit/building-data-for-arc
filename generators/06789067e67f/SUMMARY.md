# 06789067e67f

Version `3.0.0` generates 2–4 isolated monochrome components and applies the
canonical rule: crop each component, sort by `(hole count descending, area
descending, color ascending)`, and pack the crops left-to-right, top-aligned,
with one blank column. The generator now strictly validates its declared
`10..18 × 12..22`, component-count, texture, type, and difficulty controls and
constructively realizes their lawful corners.

The native parametric family preserves that exact canonical default and adds a
sequential `rank` setting: canonical packing produces an input-dependent
intermediate, then packed components are recolored `1..4` by left-to-right rank.
It supports 2–6 distinguishing demonstrations and four sequential private
queries, including a substantive 30×30 stress case. Reviewer evidence is
source-bound and protected-Racket-backed; owner acceptance and training admission
remain separate.
