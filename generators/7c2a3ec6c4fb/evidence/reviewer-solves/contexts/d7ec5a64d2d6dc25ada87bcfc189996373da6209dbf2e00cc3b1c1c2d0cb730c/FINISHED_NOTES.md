# Solve work log

## Exposure record

Before solving task `7c2a3ec6c4fb`, I had not opened its generator, rule,
reference solution, private labels, audit records, or earlier explanations.

## Revision 1 — baseline diagnostic

The supplied `NotImplementedError` template was checked once and failed all
three visible examples, as expected.

## Revision 2 — unmatched 8-connected object

The nonzero cells form several small 8-connected objects. After cropping each
object to its bounding box while preserving colors and orientation, every object
has an exact duplicate except one. The output is that sole unmatched crop:

- Example 0 uniquely contains `[[5,5,5],[7,5,7]]`.
- Example 1 uniquely contains `[[5,0,5],[0,5,0],[0,0,6]]`.
- Example 2 uniquely contains `[[7,7],[7,0],[7,0]]`.

Four-connectivity incorrectly fragments diagonal objects, so the implementation
uses 8-connectivity. It compares exact colored crops without allowing rotations
or reflections, because the visible pairs match in their presented orientation.
