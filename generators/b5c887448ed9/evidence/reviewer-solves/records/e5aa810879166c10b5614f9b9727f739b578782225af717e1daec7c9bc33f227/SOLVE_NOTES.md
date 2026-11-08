# Solve work log

## Exposure declaration before solving

I had not opened the Racket rule, generator implementation, reference solutions,
private query labels, notes, or audit records for task `b5c887448ed9`. I used only
the visible examples printed by `python3 review.py blind prepare`, the generated
`challenge.json`, and local Python checks against its training examples.

## Revision 1 hypothesis

Each nonzero color occurs exactly twice. Treat the two cells as endpoints of an
axis-aligned L path. Let the endpoint with the smaller row be the upper endpoint.
From it, draw horizontally to the column of the lower endpoint, then draw
vertically down to the lower endpoint. This exactly explains every added cell in
all four demonstrations.

Two demonstrations contain a crossing between a horizontal segment and a
vertical segment of another color. In both cases the horizontal color is visible
at the crossing: color 6 over color 7 in train 1, and color 1 over color 3 in
train 3. I therefore render all vertical legs first and all horizontal legs
second. I restore the original endpoint markers last so an endpoint remains its
observed color if a generated path happens to cross it.

The remaining uncertainty is same-orientation overlap or coincident endpoints;
none occurs in the visible examples. The implementation handles same-row and
same-column pairs naturally, and otherwise makes no unsupported geometric
extension.

## Test-first probe

Before implementing, I ran a local visible-example harness that imported the
provided stub and asserted equality on all four training examples. It failed at
`NotImplementedError`, confirming that the harness exercised `solve` rather than
passing vacuously.
