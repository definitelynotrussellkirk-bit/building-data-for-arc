# Solve work log

## Prior exposure

I had not seen task `a2d296c74658`, its generator, its rule, reference solutions,
private labels, or prior solution explanations before this blind episode. I read
only `solve-blind/challenge.json` and the solve instructions.

## Revision 1 — vertical one-cell bridges

Across all three visible training pairs, every newly painted cell is a zero that
lies exactly between two orange (`7`) cells in the same column: a `7, 0, 7`
vertical triple becomes `7, 4, 7`. Nonzero middle cells remain unchanged (the
`9` between two 7s in training example 1), and an analogous `8, 0, 8` triple is
not painted, so the endpoint color is specifically 7 and the fill color is 4.

Implemented a non-mutating scan of the original grid. For each interior zero,
paint 4 iff its immediate vertical neighbors are both 7. Horizontal pairs and
larger vertical gaps are intentionally ignored because the visible examples
support only the exact one-cell vertical bridge.

Expected query changes:
- Query 1: `(2,0)`, `(2,2)`, and `(4,0)` become 4; `(2,8)` stays 8.
- Query 2: `(1,0)`, `(1,2)`, `(3,0)`, and `(5,0)` become 4; `(1,8)` stays 6.

Remaining uncertainty: the examples do not test whether longer vertical gaps
should be filled, but their repeated exact spacing and selective nonzero
preservation make the local `7,0,7` rule the simplest supported transformation.
