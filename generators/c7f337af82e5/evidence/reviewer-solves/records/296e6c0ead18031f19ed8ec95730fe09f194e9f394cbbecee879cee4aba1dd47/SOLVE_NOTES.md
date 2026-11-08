# Visible-example Python solve work log

## Evidence and provenance

This solver received the prepared puzzle in `solve/challenge.json` and used only
that file as puzzle evidence. I did not open a generator, a Racket rule,
canonical/reference data, private labels, another agent's report, or any prior
solution explanation. I did not browse. I used the public `solve_episode.py` CLI
through its help and execution interface without reading its source.

The parent reviewer had already seen the rule during repair. This is a separate
solver context without that rule text, but the overall post-repair workflow is
**not blind**. The required finish declaration is therefore
`--earlier-exposure yes --reference-consulted no`; the latter describes the
reference consultation for this visible-example solve, not the parent's earlier
exposure.

The paths `solve/solution.py` and `solve/SOLVE_NOTES.md` existed when this solve
began. Their contents were not opened. They were renamed into `solve/revisions/`
with the prefix `untouched_preexisting_` so that writing this solution and log
would not discard them or expose their contents to this solver.

## Observations before implementation

There are four visible training pairs and two query inputs whose correct outputs
are withheld. Every visible output preserves the grid dimensions, clears the
top-left marker to zero, and changes selected orange cells (`7`) to cyan (`8`).
All visible orange objects are separate rectangles, rectangular frames, or a
thin filled segment.

| Training pair | Corner marker | Filled objects | Hollow frames | Observed changes |
| --- | --- | --- | --- | --- |
| 1 | 2 | 3 by 2 and 3 by 5 rectangles | Two 3 by 3 frames | Both filled rectangles become 8; frames remain 7 |
| 2 | 2 | 3 by 6 rectangle | 4 by 3 and 3 by 5 frames | Filled rectangle becomes 8; frames remain 7 |
| 3 | 1 | 3 by 5 rectangle | 3 by 3 frame | Frame becomes 8; filled rectangle remains 7 |
| 4 | 2 | 2 by 1 segment and 3 by 5 rectangle | 3 by 4 and 3 by 3 frames | Segment and filled rectangle become 8; frames remain 7 |

Dimensions above are height by width. The fourth pair is useful evidence that
thin objects belong with filled rectangles. The top-left marker is separate
from the orange-component search even when an object is adjacent to it.

## Hypothesis and revision 001

The corner marker selects object type: `1` selects hollow frames and `2` selects
filled objects. Clear the marker and recolor every cell of each selected orange
object from `7` to `8`; preserve the remaining cells.

Implementation: collect four-neighbor connected components of color `7`.
An object is filled when its cell count equals the area of its bounding box.
Otherwise classify it as hollow within the observed domain, where every such
object is a rectangular frame. This criterion naturally handles the observed
two-cell segment and the singleton in the second query. I did not add special
cases for particular positions, dimensions, or individual examples.

This is one genuine solve hypothesis, not a sequence of deliberately incorrect
attempts. Its first implementation is preserved as
`solve/revisions/solution_v001.py` before the checker is run. The public checker
will test exact agreement on the four visible training outputs and produce
query predictions with withheld correctness.

## Query predictions and limits

For query 1, the hypothesis predicts that the 3 by 3 frame becomes cyan and the
3 by 5 filled rectangle remains orange. For query 2, the isolated orange cell
and the 5 by 3 filled rectangle become cyan, while the 3 by 3 frame stays orange.
Both top-left markers are cleared.

The examples do not establish behavior for arbitrary irregular, open, nested,
diagonally touching, or multicolored objects. The bounding-box criterion is an
inference appropriate to the visible object family; it is not an independently
verified definition for all possible shapes. Query correctness is **unknown**
unless the public interface actually provides it; hidden answers must not be
consulted to strengthen the claim.

## Check and finish results

Pending the first genuine checker run. Exact command arguments, exit status,
visible scores, attempt count, and the reported generator hash will be recorded
here after the public CLI returns them.
