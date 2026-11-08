# Solve work log

## Exposure

Before this solve I had read only the packet-level instructions and repository-level documentation. I did not open this task's generator, canonical rule, private labels, reference solution, notes, or audit evidence.

## Revision 1 — block-diagonal duplication plus active blank-row lines

The output dimensions are exactly twice the input height and width. In every visible example, the input appears unchanged in the upper-left block and again in the lower-right block; the other two blocks are zero.

Rows that are all zero sometimes become full-width color-3 lines in both copies. The distinguishing visible case is training example 2: source row 1 becomes green, while the all-zero final source row 5 stays zero. I therefore treat all-zero rows at or before the final non-zero row as in-content separators, and all-zero rows after the final non-zero row as trailing padding. This also explains the leading zero row in training example 1, which becomes green because content follows it.

The two consecutive leading zero rows in query 1 leave one uncertainty not directly resolved by the demonstrations: color both active blank rows, or only the one immediately adjacent to content. I chose to color both because the visible evidence is most simply described as replacing every blank row inside the vertical content extent; the alternative needs an additional adjacency exception unsupported by the examples.

Implementation: allocate a 2H × 2W zero canvas, copy the input at offsets (0, 0) and (H, W), find the last non-zero source row, and paint every all-zero source row through that index across both output rows with color 3.
