# Post-repair solve notes

## Scope and exposure disclosure

This is a factual, agent-authored summary of the solving work, not a model
transcript or token trace. The coordinating agent had already inspected the
rule while repairing the packet. I performed this solve as an isolated worker
with only the visible `solve/challenge.json`, my own solve files, and the
supported check/finish outputs. The coordinator supplied no rule details or
solution hints. I did not inspect a generator, canonical rule, reference
solution or explanation, private labels, taskprobe material, repository/source
files, or other agents' findings. The overall episode must therefore declare
earlier exposure **yes**, and reference consulted **no**. This is not claimed
to be a blind solve.

## Visible observations and experiments

The visible challenge contains three input/output training pairs and two test
inputs without outputs. Color 1 forms walls, color 7 occurs at doors, and the
remaining connected interior regions are rooms. Red 2 and green 3 indicate
endpoint rooms. Shown outputs fill complete selected rooms with 8, retain all
wall and door pixels, and replace an unselected color-4 mark with 0.

I enumerated rooms by row-major first cell and constructed their adjacency
through color-7 doors using only the visible inputs. The observations were:

| Example | Minimum-door room paths | Shown filled rooms |
| --- | --- | --- |
| Train 1 | `6,7,10` or `6,9,10` | `6,7,10` |
| Train 2 | `3,2,1,0` | `0,1,2,3` |
| Train 3 | `0` | `0` |
| Test 1 | `0,1,6` or `0,5,6` | Not provided |
| Test 2 | `5,3,1` | Not provided |

The hypothesis that every reachable room should fill is contradicted by
training pair 3, where both endpoint markers occupy one room and only that
room is filled even though it connects to others.

I also tested the alternative of minimizing traversed pixel steps on training
pair 1. A breadth-first distance calculation on all non-wall pixels gives 11
steps; restricting traversal to the shown filled rooms and doors gives 13.
Thus selecting rooms from a shortest pixel path does not explain that output.
This was a visible-data experiment, not a failed submitted code revision.

## Revision 1 hypothesis

Treat doors as unit-cost edges between rooms and choose a shortest room route
from the red room to the green room. Resolve ties by ascending row-major room
IDs during breadth-first search. Fill every interior cell in the selected
rooms with 8; replace all other interior cells, including extra marks, with 0.
Keep walls and doors unchanged.

This matches the shown choice in training pair 1 and predicts the upper
intermediate room for test pair 1. The visible examples do not uniquely prove
this tie rule: other rules could choose the same training route. The role of
extra colored marks is likewise underdetermined beyond the shown removal of
an unselected mark. I treat them as removable interior marks, not endpoints.

## Validation and stopping record

Revision 1 has been written to `solve/solution.py`. Its supported check and
finish results will be recorded below after they execute. No failed solution
revision has occurred or been manufactured.
