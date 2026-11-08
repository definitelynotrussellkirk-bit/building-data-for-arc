# Solve work log

## Exposure declaration before solving

I had not opened the generator, canonical rule, private labels, prior solutions, or task-specific notes for blind task `21d822423cfc`. I only read the visible `challenge.json` and the provided solution template.

## Revision 1 — monochromatic-room flood

**Observation.** Color 5 forms walls that partition each grid into 4-connected rooms. In every training example, a room containing exactly one distinct nonzero/non-wall color is filled with that color. Empty rooms stay unchanged. Rooms containing two distinct marker colors (for example 2 and 3, or 1 and 2) stay unchanged.

**Important query discriminator.** The first query has a room containing two markers that are both color 3, and the second query has three color-3 markers in one room. This suggests multiplicity is not the veto; conflicting distinct colors are. Therefore I fill a room whenever its set of marker colors has cardinality one, regardless of how many marker cells it contains.

**Implementation.** Find every 4-connected component of cells whose value is not 5. For each component, collect values other than 0 and 5. If there is exactly one distinct value, replace the whole component with it; otherwise preserve the room.

**Remaining uncertainty.** The visible examples do not show a room containing multiple markers of the same color in training, so the query behavior depends on the natural generalization from “one distinct marker color” rather than “exactly one marker cell.” The repeated same-color query markers appear intentionally chosen to test that distinction.
