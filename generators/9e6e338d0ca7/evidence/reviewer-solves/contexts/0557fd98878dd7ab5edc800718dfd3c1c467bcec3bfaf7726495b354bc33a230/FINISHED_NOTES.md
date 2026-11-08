# Solve work log

Earlier task-rule exposure: none. Before this solve I opened only packet-level instructions and the assignment draw; I did not inspect this task's generator, rule, notes, solutions, labels, or audit records.

## Revision 1

Hypothesis: color `5` forms walls that partition the grid into rooms. Count the nonzero colored marker cells in each nonempty room, ignore empty rooms, find the smallest positive count, and fill every room tied at that minimum with its marker color. The demonstrations support this: lesson 1 fills the two one-marker rooms rather than the two-marker room; lesson 2 fills the sole one-marker room rather than the two two-marker rooms; lesson 3 fills the sole one-marker room while leaving rooms with two or three markers unchanged.

Implementation probe: identify 4-connected non-`5` components, collect their nonzero markers, and fill minimum-count rooms when their fill color is unambiguous. This predicts three filled singleton rooms in test 1 and only the top-left singleton room in test 2. Remaining uncertainty: the examples do not show a minimum room with multiple markers of mixed colors; the implementation conservatively leaves such an ambiguous room unchanged.
