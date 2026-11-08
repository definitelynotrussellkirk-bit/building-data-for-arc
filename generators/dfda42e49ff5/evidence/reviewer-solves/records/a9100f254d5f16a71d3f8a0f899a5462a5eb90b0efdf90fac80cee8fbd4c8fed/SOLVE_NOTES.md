# Visible-only solve work log

## Exposure

I read only this lane's README.md, challenge.json, and the initial work-log
instructions before implementing the solution. I have no earlier rule exposure
and consulted no generator, Racket rule, reference solution, private label,
audit evidence, other task source, or prior solution explanation.

## Revision 1

Observation: The three visible training outputs preserve the input dimensions,
colors, and existing colored cells. They add color in horizontal gaps inside
individual connected objects. Separate objects on the same row stay separate;
their outer irregular edges remain unchanged.

Hypothesis: Find each orthogonally connected nonzero object of one color. In
each occupied row, fill zero cells between that object's leftmost and rightmost
cells with the object's color. Use the original grid for component membership.

Implementation: solution.py provides solve(grid), copies its input, and applies
that rule to each component. Existing nonzero cells are preserved.

Validation: The initial implementation will be checked on all three visible
training pairs and both query inputs with the official blind check command.
No earlier implementation or failed attempt was made.

Alternatives and uncertainty: Filling across an entire row would incorrectly
join separate objects in the visible examples. Filling each object's bounding
rectangle would alter the preserved irregular edges. The examples do not test
diagonal-only connections or overlapping fill spans of different colors; the
implementation uses orthogonal connectivity and preserves nonzero cells.
Private query outputs are unknown, so query correctness cannot be established.
