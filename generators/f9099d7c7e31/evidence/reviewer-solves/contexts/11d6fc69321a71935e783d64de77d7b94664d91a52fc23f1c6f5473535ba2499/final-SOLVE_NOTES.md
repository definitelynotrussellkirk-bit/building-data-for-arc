# Visible-example solve log

## Exposure and protocol
I inspected and revised this task's generator and read its canonical rule before this solve. Earlier exposure is **yes**: this is not a blind inference result. Since `prepare`, I have used only `challenge.json`, this independently written Python, and the public checker. I have not opened the generator, rule, earlier solution explanations, private labels, or private scores during the solve.

## Revision 1: explicit negative-control experiment
Hypothesis under test: crop the original grid to the object having greatest bounding-rectangle area, breaking ties by number of cells. This is an intentional ablation of a plausible visual shortcut, not a claim that I forgot the previous review.

Visible evidence: examples 0 and 1 have wide three-row objects. Example 1 includes foreign-colored cells inside the shown crop, so output should be a slice of the original input, not only the chosen object's color. Example 2 contains a sparse taller object, a dense narrower object, and the shown three-by-five output. These permit a direct selection-rule comparison without query labels.

Implementation: independently extract same-color four-neighbor components by breadth-first traversal and return a tight input slice. Submit the bbox-area selection to the public checker; retain the result even when it fails.

Remaining uncertainty: the visible examples do not establish a tie policy when both width and cell count are equal. The implementation uses stable row-major discovery for such ties; no generality beyond the visible family is claimed.

## Revision 2: width, then occupied cells
Revision 1 executed successfully but matched only **2/3** visible demonstrations. The failed third example selects the taller width-five component under bbox-area, instead of the shown width-five component with more occupied cells. Change only the selection key to `(width, cell_count)`; retain the same component extraction and literal input crop. A largest-cell-count rule would instead select the narrower 12-cell rectangle in that example, and would also contradict the shown output.

The second submission tests all three visible demonstrations and executes on both masked inputs. Masked correctness remains withheld. No query-dependent exceptions, task identifier checks, or stored output arrays are used.

## Stopping record
Revision 2 matched **3/3 visible examples** with completed execution. I stop after this evidence rather than inspect withheld labels. Both submitted versions and their notes are retained by the checker. Earlier exposure: yes. Reference consultation during this solve: no. Hidden-query correctness: unknown pending independent maintainer scoring. This result is not a model-training evaluation or a blind human-solve benchmark.
