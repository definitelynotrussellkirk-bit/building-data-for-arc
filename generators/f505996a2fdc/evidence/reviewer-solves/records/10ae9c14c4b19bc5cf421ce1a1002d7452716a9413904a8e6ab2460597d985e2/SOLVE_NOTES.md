# Visible-example solve notes

## Revision 1

The nonzero cell at `(0,0)` is a command rather than part of the object. After
clearing it, tightly crop all remaining nonzero cells.

The five demonstrations directly identify:

- `1`: identity
- `2`: rotate 90 degrees clockwise
- `3`: rotate 180 degrees
- `5`: reflect left/right
- `6`: reflect up/down

Command `4` appears only in the first query. The natural completion of this
six-operation codebook is transpose across the main diagonal. That also keeps
`4` distinct from the already observed quarter-turn and axial reflections.

Implementation therefore clears the command, crops, and dispatches the six
matrix transforms. The only visible-example uncertainty is the unseen command
`4`; no rule source or hidden label was consulted during this solve episode.
