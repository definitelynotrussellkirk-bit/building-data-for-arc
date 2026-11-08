# Solve work log

Earlier rule exposure: **yes**. I repaired this generator before the required fresh solve, so I already knew the intended task family. During this solve I kept the generator, Racket rule, reference solutions, prior solve notes, and private labels closed and used only `challenge.json` plus local Python checks.

## Revision 1

The three visible examples support one rule: find each 4-connected region of zeroes, collect colors 1–4 on its cardinal boundary, and fill the entire region only when one color has a unique plurality. A marker contributes once for every zero-to-marker cardinal adjacency; this explains the small nonrectangular chamber with a marker embedded inside it. Tied regions remain zero, and all nonzero cells are preserved.

I implemented that component flood-fill directly in `solution.py`. A local replay against all three visible train pairs matched every output cell. No alternate revision was needed; the principal rival considered was counting distinct marker cells only, which the visible full-contrast example refutes.
