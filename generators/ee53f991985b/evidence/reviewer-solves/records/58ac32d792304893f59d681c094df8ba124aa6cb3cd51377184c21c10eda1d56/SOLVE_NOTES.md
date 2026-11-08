# Solve work log

Earlier exposure before this episode: none known. I did not inspect this task's generator, canonical rule, private labels, prior solutions, or audit evidence.

## Revision 1 — complete rectangular frames are filled

Visible examples contain monochrome outline-like components. A component changes only when it is the complete perimeter of its own axis-aligned bounding box: those components have their zero-valued interiors filled with the frame color. Three-sided or otherwise incomplete frames remain unchanged. This explains all visible changes and refutes the broader alternative “fill every component bounding box.”

Implementation plan: find 4-connected components separately by color, compare each component exactly with the perimeter cells of its bounding box, and fill only background cells strictly inside exact rectangular frames. Preserve shape, existing non-background cells, incomplete frames, and unrelated components.

Test-first probe: `WORK/checks/blind-visible/test_visible_examples.py` loaded the initial stub and failed on all three examples with `NotImplementedError` (`red.txt`). After implementing the rule, rerun the same visible-example test and the packet's visible-only checker. Remaining uncertainty is limited to unseen arrangements such as nested or touching objects; filling only background cells avoids destroying unrelated interior colors.
