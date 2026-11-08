# Solve work log

## Exposure declaration before solving

I had not opened task `0281fbec1cf2`'s generator, Racket rule, notes, solutions,
audit records, or private labels. I only read the packet's assignment instructions
and then `solve-blind/challenge.json`.

## Revision 1 — projected rectangle with directional veto markers

### Observation

Each input contains one solid red (`2`) rectangle and one or more isolated pixels
of another color. In every visible output, the rectangle is projected to the grid
edges in both axes:

- every row occupied by the rectangle is normally filled across the whole width;
- every column occupied by the rectangle is normally filled across the whole height.

An isolated non-red colored pixel aligned with one rectangle row or column vetoes
the entire projection ray on the side where it lies. The marker itself and the
background gap between it and the rectangle remain unchanged. Projection in the
opposite direction still occurs.

Visible evidence:

- train 1: the marker to the right of the bottom rectangle row suppresses only that
  row's rightward projection; its leftward projection remains;
- train 2: the marker below one rectangle column suppresses only that column's
  downward projection; upward projection remains;
- train 3: the marker above one rectangle column suppresses only that column's
  upward projection; downward projection remains.

### Competing hypotheses considered

1. **Fill only until reaching the marker.** Rejected: the cells between rectangle
   and marker stay background in all three examples.
2. **The marker blocks the whole row/column in both directions.** Rejected: the
   opposite projection direction is visibly filled.
3. **Extend only the rectangle's border.** Rejected: every rectangle row and every
   rectangle column participates, creating full-width/full-height bands.

### Planned implementation

Find the bounding box of all red cells, copy the input, and inspect marker positions
in the original grid. For each rectangle row, fill left and/or right only when that
side has no nonzero non-red marker. Do the analogous operation above/below for each
rectangle column. Marker tests use the original grid so newly painted red cells
cannot affect later decisions.

### Probe

I created a temporary visible-example test that imports the untouched starter
`solution.py` and compares all three training outputs. It failed with the expected
`NotImplementedError`, establishing a red test before implementation.

Remaining uncertainty: the visible examples do not show multiple markers on the
same ray or markers not aligned with the rectangle. The natural local rule is that
any marker on a ray vetoes that ray, while unaligned markers have no effect.
