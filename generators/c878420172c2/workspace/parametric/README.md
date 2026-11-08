# Normalized-overlap component family — c878420172c2

`overlap_mode` is episode-fixed:

- `all_overlap` is the exact selected canonical rule: normalize the color-2 and
  color-3 shapes to their top-left origins and paint every common cell in 8.
- `largest_component` computes that same normalized overlap, then retains only
  its largest four-connected component; row-major top-left breaks size ties.

Every teaching profile uses two separate connected source shapes whose
normalized intersection has a unique larger component, a two-cell secondary
component diagonally adjacent under 8-connectivity, and a remote singleton.
This refutes both “delete singletons” and 8-connected-component shortcuts while
teaching the intended four-connected largest-component rule. Inputs match across
settings. Four query profiles include a 30×30 case with substantial source
content touching all boundaries and all quadrants.

Sequential dependency: **A** derives the exact normalized intersection set. That
set is the intermediate. **B** computes components and selects the largest one.
Skipping A and feeding normalized color 2 directly to B selects the whole source
shape instead, changing the protected-Racket result.
