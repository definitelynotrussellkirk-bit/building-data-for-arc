# Blind solve record: 80a3c4f25880

This is an assistant-authored work summary, not a token-level conversation trace.
Earlier rule exposure: no. No generator, reference rule, private labels, audit
record, or previous solution was consulted. Only the public README/challenge
and a Python probe of its three visible pairs were used.

## Visible evidence and revision 1

The upper-left cell is an isolated marker. The remaining nonzero cells form
one object. Cropping that object's bounding box preserves its color and holes.
The probe compared all four clockwise quarter-turns against each visible output:
example 0 (input 8 by 8, output 2 by 3) matched turn 1 and marker 1;
example 1 (input 8 by 8, output 3 by 3) matched turn 2 and marker 2;
example 2 (input 7 by 7, output 2 by 3) matched turn 3 and marker 3.
The submitted rule crops the object and uses the marker as the clockwise turn
count. No failed solution revision or deliberate negative was manufactured.

The two query outputs remain unknown. Query execution is not evidence of
correctness; independent scoring is deferred to the maintainer. This rule is
supported by the three visible examples, with no claim beyond that evidence.
