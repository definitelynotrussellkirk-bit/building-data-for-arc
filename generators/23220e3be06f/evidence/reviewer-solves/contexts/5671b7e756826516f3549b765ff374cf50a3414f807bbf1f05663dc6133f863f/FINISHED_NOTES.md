# Solve work log

I had no earlier exposure to task `23220e3be06f`, its generator, rule, reference
solutions, private labels, or prior solve notes. I used only the prepared visible
examples.

## Revision 1 — crop payload and flip from the corner marker

Observation: every input has a single nonzero instruction cell at `(0, 0)` and a
separate multicolor payload object lower in the grid. The output is exactly the
payload's tight nonzero bounding box, retaining zeros inside that box.

The marker value determines a reflection:

- Marker `5`: reflect the cropped payload left-to-right. Train 0 and train 2
  exactly match this operation.
- Marker `6`: reflect the cropped payload top-to-bottom. Train 1 exactly matches
  this operation.

I rejected rotations because train 1 keeps its `4 × 2` dimensions and only
reverses row order, while train 0 keeps `2 × 4` dimensions and only reverses
column order.

Implementation: exclude `(0, 0)`, crop the bounding box of every remaining
nonzero cell, then apply the marker-selected reflection. This also handles query
0 where color `6` occurs both as the marker and inside the payload; exclusion is
by position rather than by color.

Predicted query outputs before checking:

Query 0 (`6`, vertical reflection):

```text
9 9 0 0
9 0 0 6
```

Query 1 (`5`, horizontal reflection):

```text
7 7 7 0
0 3 3 3
0 0 3 0
0 0 0 3
```

Remaining uncertainty: the visible lesson shows only markers `5` and `6`, always
at `(0, 0)`. The solution deliberately does not invent behavior for unseen
markers or marker locations.
