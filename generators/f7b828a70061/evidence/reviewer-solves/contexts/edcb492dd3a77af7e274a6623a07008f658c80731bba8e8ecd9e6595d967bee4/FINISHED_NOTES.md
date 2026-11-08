# Solve work log

## Exposure declaration

I had already worked on this assigned generator before this visible-only solve,
so I had earlier exposure to the task's intended semantics. During this solve I
did not reopen the generator, Racket rule, canonical examples, reference
solutions, private query labels, or earlier solution explanations. I used only
the seven visible training pairs printed by `solve prepare`, the visible
challenge file, and local execution against those visible outputs.

## Revision 1 — select by component cell count, crop, then decode the command

**Visible observations.** Every input has an isolated nonzero cell at `(0,0)`
and two spatially separated nonzero body components. Both body components span a
3×3 bounding box in the displayed lessons, so “pick the largest bounding box”
does not distinguish them. The output always contains the component with more
nonzero cells, including its internal zeros after cropping to that component's
bounding box. The smaller, earlier/left component disappears.

Across examples with the same body operation, the corner values determine the
orientation: `2` leaves the crop unchanged, `3` rotates it 90° clockwise, `4`
rotates it 180°, and `5` rotates it 90° counter-clockwise. The corner cell is
cleared before object extraction and never appears in the output. Connectivity
is orthogonal: diagonally touching nonzero cells do not merge.

**Hypothesis/program.** Clear `(0,0)`, find all 4-connected components of any
nonzero colors, choose the component with greatest cell count (reading-order
tie break), crop the cleaned grid to its bounding box, and apply the command's
rotation.

**Probe.** A local visible-pair regression first failed on the untouched
`NotImplementedError`, then matched all seven visible outputs after this single
implementation revision. I retained the full colors inside the crop rather than
binarizing because the visible outputs preserve them.

**Alternatives rejected.** Selecting the left component, all nonzero cells, or
the largest bounding-box area contradicts the visible pairs. Selecting by color
count is also unsupported because both components can use the same palette.

**Remaining uncertainty.** The masked query answers are intentionally withheld.
The implementation handles arbitrary rectangular crops and all four observed
command values; behavior outside this visible task family was not inferred.
