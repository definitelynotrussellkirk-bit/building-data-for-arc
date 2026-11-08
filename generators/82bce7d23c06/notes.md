# Working notes: 82bce7d23c06

## 2026-10-24 review `review-7944861aa83ee6b1`

Repaired exact-count and validation defects in version `2.1.0`. Position bias is
now an ordering preference rather than a truncated candidate domain, so every
layout/bias pair returns the requested number of distinct columns. `grid_w` and
`nz_count` use strict typed gates with `nz*width <= 30`; invalid values and
unknown overrides are not coerced or clamped. Ordinary all-zero inputs are
rejected because they imply an undefined 0×0 output. Added an independent rule
mirror.

Twenty-four focused tests cover all six labeled canonical pairs, all 20
layout/bias combinations at `width=6,nz=5`, zero-active rejection, typed bounds,
width endpoints, and determinism. Protected Racket replay checked six canonical
and four generated cases. A bounded 640-case probe covered widths 2–10, every
lawful count, and all five layouts by four biases with no observed failure. The
probe is finite and does not establish behavior outside the declared domain.

## 2026-10-25 native parametric review `review-47be421bacbfeadd`

Preserved the approved production generator byte-for-byte at
`ecf4304f433ac7518867f38df895f43843c4dca7304a3790702d0b9ac8936304`.
Built the task-local native `finish` family under `workspace/parametric/`:
`project_only` returns the exact canonical diagonal projection, while
`component_count_relay` counts same-color 8-connected components in that
produced projection, uses the count as a 1-indexed selector over source nonzero
cells, and recolors only the selected source cell's projected diagonal color 9.
The wrong-intermediate witness substitutes source nonzero count for projected
component count; protected replay selects a different diagonal and changes 35
final cells.

The sampler supports 2–6 demonstrations and four distinct controller queries,
keeps inputs identical across settings, and includes an exact 30×30 projection
with substantial occupancy and all four boundary contacts. The bounded
self-audit passed 18 jobs (seeds 0, 17, 97; demo counts 2, 3, 6; both settings),
rejected all nine declared shortcuts using demonstrations only, and matched 147
protected Racket labels. Native qualification passed four jobs and 32
protected-Racket labels; 16 sequential public views, 24 first-turn invariance
mutations and four positive controls passed. Final focused tests passed 52/52.

Status is reviewer-ready only. Exact-source owner qualification/acceptance is
still required, and this work grants no training admission. The finite shortcut
set and bounded seeds do not prove universal identifiability.
