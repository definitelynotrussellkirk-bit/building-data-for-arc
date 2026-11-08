# Solve work log

## Exposure declaration before solving

I had not opened task `2c7b1545edf9`'s generator, rule, notes, reference solution,
private labels, or audit records. I had read only the packet-level instructions and
then `solve-blind/challenge.json` (plus the supplied blank solve-workspace templates).

## Revision 1 — largest connected object, reading-order tie break

The examples contain several separated monochrome objects on a zero background, and
the output is an exact zero-padded crop of one object. Counting 4-connected pixels:

- training 1 selects a 7-pixel object; another 7-pixel object starts farther right;
- training 2 selects a 7-pixel object; another 7-pixel object starts lower;
- training 3 selects the unique 8-pixel object.

Hypothesis: select the largest 4-connected nonzero monochrome component, resolving
area ties by topmost row and then leftmost column, and return its tight bounding-box
crop. This predicts the first query's 6-pixel red component and the second query's
topmost of two 7-pixel components. The second query is the main uncertainty because
the two largest components also share bounding-box area, density, perimeter, and
several basic graph statistics, leaving reading order as the simplest demonstrated
tie rule.

Probe: a local visible-example assertion was run before implementation and failed
with the supplied `NotImplementedError`, confirming the harness exercised the blank
solver. After implementation, I will check all visible pairs through the official
solve tracker. No reference material was consulted.
