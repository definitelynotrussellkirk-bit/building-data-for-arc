# Blind solve e971e0773705

Exposure: no earlier knowledge of this task; no generator, reference rule,
canonical records, prior explanations or private labels were opened. Files used:
`challenge.json`, displayed preparation output, and our own solution/test files.

## Revision 1 — genuine solve attempt
Observed input shapes are 10×16, 11×8, 15×10; all visible outputs are 3×6.
Red four-connected components are 4-cell T tetrominoes in two orientations.
An input-only component probe counted (top-bar, bottom-bar) as (3,3), (2,2),
(4,3) in the demonstrations. Output blue counts are 3,2,4; green counts 3,2,3.
This distinguishes the orientation-to-color assignment in the third example.
Each color occupies corners of its own 3×3 block, filling down the first column
then down the last column. The middle row and each block's middle column stay 0.

Alternative considered: preserving spatial arrangement of objects. Rejected
because objects move substantially between inputs while the outputs remain
count encodings. No failed semantic solution was manufactured. A local visible
unit test first failed only on the supplied NotImplementedError placeholder;
that is setup evidence, not a solver revision or a teaching negative.

Implemented connected-component classification, two counts, and corner encoding.
Query inputs contain 4 bottom-bar/0 top-bar and 4/4; their labels and dimensions
remain withheld. Shapes/counts beyond observed tetrominoes and four per type are
not supported by this hypothesis; the code fails clearly rather than inventing
an unseen encoding.
