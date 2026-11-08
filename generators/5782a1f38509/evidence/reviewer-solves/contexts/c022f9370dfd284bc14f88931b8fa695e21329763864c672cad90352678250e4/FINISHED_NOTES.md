# Solve work log

## Prior exposure declaration

Before this solve episode I had already inspected the task's canonical rule while
reviewing the generator.  I did **not** reopen the rule, generator source,
reference solution, private labels, or earlier explanation during this solve.
This episode therefore must be recorded as `earlier-exposure: yes` and
`reference-consulted: no`.

## Revision 1

### Evidence read

I used only `challenge.json`.  Across all five visible pairs, each nonzero
same-colour 4-connected component becomes its own tightly cropped object.  The
objects are placed left-to-right with exactly one all-zero separator column.
Their original colours and internal holes/background are preserved, and every
crop begins on output row zero.

The ordering signal is occupied-cell count, ascending.  The fifth example is
particularly useful because two disconnected components share colour 9; they
remain separate, ruling out global colour grouping.  Other examples separate
cell count from bounding-box height/width, so sorting by crop dimensions is not
sufficient.

### Implementation

I wrote a general solver that:

1. validates a rectangular grid;
2. finds nonzero same-colour 4-connected components by breadth-first search;
3. tightly crops each component;
4. sorts crops by ascending occupied-cell count;
5. top-aligns them left-to-right with one zero column between neighbours.

The visible examples use distinct component sizes.  I added deterministic
geometric/colour tie-breakers only for otherwise unspecified equal-size inputs;
they do not alter any observed case.  Empty input content returns `[[0]]`.

### Predicted test outputs

For the first hidden input shown in the challenge, the singleton 9 precedes the
vertical three-cell 7 and the four-cell 1 shape.  For the second, singleton 7
precedes the vertical two-cell 8 and the four-cell 4 square.  Both predictions
preserve top alignment and one-column gaps.

### Remaining uncertainty

The examples do not define equal-area ordering.  The implementation's tie-break
is deterministic but is an extrapolation.  Apart from that edge case, all major
operations are independently supported by multiple visible pairs.
