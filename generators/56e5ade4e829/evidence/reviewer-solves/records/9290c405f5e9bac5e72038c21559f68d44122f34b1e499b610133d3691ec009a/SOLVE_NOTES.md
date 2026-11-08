# Solve work log

## Prior exposure declaration

This is an exposed post-repair solve. Before preparation I had read and repaired this task's generator and authority material, so I already knew the intended family of operations. During this solve I did not reopen the generator, Racket rule, reference solution, private labels, or earlier solution explanations. I used only the visible prepared challenge and my own Python implementation.

## Visible-example analysis

Each input contains two spatially separated objects, colored 1 and 2, plus one isolated marker whose color is neither 0, 1, nor 2. The output ignores the objects' absolute positions: crop each object to its own bounding box and align the two normalized masks at their top-left corners.

The marker chooses a Boolean combination of those normalized masks:

- marker 3: intersection. In examples 0 and 3, only the cells occupied by both normalized objects survive.
- marker 4: union. Examples 1 and 4 retain every cell occupied by either object.
- any other shown marker: symmetric difference. Example 2 uses marker 7 and retains cells occupied by exactly one object.

The selected mask is cropped again to its occupied bounding box and painted color 8, with zeros inside that rectangle. I retain `[[0]]` as the natural representation if a selected mask is empty, although no visible example requires it.

## Revision 1

Implemented exactly that hypothesis in `solution.py`: normalize colors 1 and 2 independently; detect the singleton non-operand marker; apply intersection/union/XOR; crop and render with 8. The implementation deliberately uses shape masks rather than global coordinates, because the visible examples place operands at unrelated locations.

Remaining uncertainty is limited to unseen malformed inputs (missing/multiple markers or missing operands). The prepared inputs consistently have one marker and both operands, so the solution follows that visible domain.
