# Visible-example solve log

## Exposure and protocol
I inspected and revised this task's generator and read its canonical rule before this solve. Earlier exposure is **yes**: this is not a blind inference result. Since `prepare`, I have used only `challenge.json`, this independently written Python, and the public checker. I have not opened the generator, rule, earlier solution explanations, private labels, or private scores during the solve.

## Revision 1: explicit negative-control experiment
Hypothesis under test: crop the original grid to the object having greatest bounding-rectangle area, breaking ties by number of cells. This is an intentional ablation of a plausible visual shortcut, not a claim that I forgot the previous review.

Visible evidence: examples 0 and 1 have wide three-row objects. Example 1 includes foreign-colored cells inside the shown crop, so output should be a slice of the original input, not only the chosen object's color. Example 2 contains a sparse taller object, a dense narrower object, and the shown three-by-five output. These permit a direct selection-rule comparison without query labels.

Implementation: independently extract same-color four-neighbor components by breadth-first traversal and return a tight input slice. Submit the bbox-area selection to the public checker; retain the result even when it fails.

Remaining uncertainty: the visible examples do not establish a tie policy when both width and cell count are equal. The implementation uses stable row-major discovery for such ties; no generality beyond the visible family is claimed.
