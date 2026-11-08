# Blind solve notes — ee6ef749efca

I used only `challenge.json` and local Python reasoning; I did not inspect this task's generator, rule, notes, prior solutions, labels, or audit records.

## Observations

- Every training input contains red (`2`) single-cell markers and one or more magenta (`6`) connected components.
- The output removes all source objects and stamps one normalized magenta component at every red marker.
- The marker is the copied component's bounding-box top-left coordinate.
- Training example 3 is decisive: it contains a 3-cell magenta distractor and a 5-cell component. Only the largest component is copied, so the template-selection rule is "largest 4-connected 6-component", not nearest component or first component.

## Hypothesis and implementation

1. Find all 4-connected components of color 6.
2. Choose the component with the greatest cell count.
3. Normalize its cells relative to its bounding-box top-left.
4. Start with an all-zero grid of the same dimensions.
5. For every color-2 cell, stamp the normalized offsets in color 6, using the marker as top-left.

The two visible test inputs keep all copies in bounds. The implementation clips defensively at grid edges, though no visible example distinguishes clipping from rejecting an out-of-bounds copy.

## Manual test predictions

- Test 1 uses the four-cell zig-zag `[[6,6,0],[0,6,6]]` and stamps it at both red cells in row 3.
- Test 2 ignores the two-cell horizontal distractor, uses the four-cell T shape `[[0,6,0],[6,6,6]]`, and stamps it at the two red cells in column 7.
