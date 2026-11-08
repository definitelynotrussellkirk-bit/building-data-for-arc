# 92f4d4eb0dbb

## Rule

Find the minimum and maximum rows containing color 1. Recolor a color-1 cell
to color 2 exactly when `2 * row > min_row + max_row`; preserve all other
cells. The canonical Racket authority is unchanged and pinned by rule hash
`5e129c41777b`.

## Generator v3.1.0

The sampler emits one connected, non-solid color-1 shape on a 7..14 × 7..14
zero-background grid. Generated occupied boxes are five columns wide and 5..7
rows high. Five observable morphologies are available: `frame`, `ladder`,
`diamond`, `zigzag`, and `notched_frame`, with free lawful placement and
optional horizontal reflection.

A four-position schedule alternates canonical-scale and broader canvases and
even/odd occupied heights. Odd profiles use the asymmetric notched frame. Thus
every three-demonstration lesson contains both an occupied midpoint-row witness
against `row >= midpoint` and a centroid-shift witness against splitting at the
mean row of occupied pixels.

Exact controls remain `grid_h`, `grid_w`, `span`, and `shape_kind`. Calls now
reject invalid seed, sample-index, and difficulty scalar values.

## Separate parametric proposal

`workspace/parametric/` contains a non-selected two-parameter prototype:
`side ∈ {lower, upper}` and `boundary ∈ {strict, inclusive}`, with canonical
default `lower + strict`. One setting is selected per episode. Four retained
episodes and 16 unique inputs are exact under Racket; every demonstration
refutes every other setting and every query is setting-sensitive.

## Final evidence

- Final generator SHA-256: `c71752cd690b3548856be0b1927f7381b245ab2009542f27e49b0d15ba540dda`.
- Strict after battery: 12/12 stages green.
- Portable task tests: 85/85 passed.
- Lesson census: 300/300 production lessons and 1,200/1,200 query rotations
  unambiguous against both declared rivals; 735 unique inputs.
- Profile floor: 30/60 exact and 40/60 envelope hits, with support in every band.
- Override matrix: 21,060/21,060 accepted draws and zero findings.

Finite rival checks do not prove universal identifiability. The prototype is a
proposal, not a catalog change, and training approval remains a maintainer decision.
