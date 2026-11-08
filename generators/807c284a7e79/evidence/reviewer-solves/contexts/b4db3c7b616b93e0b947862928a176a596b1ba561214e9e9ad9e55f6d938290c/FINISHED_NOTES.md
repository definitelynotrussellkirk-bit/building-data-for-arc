# Post-repair visible-only solve notes

This is a human work log. I had earlier rule exposure during the assigned generator review, so this is **not blind**. During this solve phase I consulted only `solve/challenge.json` and my own Python; I did not reopen the generator, Racket source, reference solutions, private labels, or earlier solution explanations.

## Visible-example observations

- Every input has an outer wall of color 8, one seed of color 2, zeros, and an interior wall.
- In outputs, color-8 cells are unchanged.
- The seed itself becomes color 3.
- Reached open cells alternate 3/4 across each cardinal step. This is consistent with shortest-path distance parity from the seed: even distance becomes 3 and odd distance becomes 4.
- The second visible training example has a complete wall that disconnects the upper chamber from the seed. Its upper zeros stay zero. This rules out the tempting shortcut “checkerboard every non-wall cell.”
- The third example likewise fills only the seed-containing side of a complete vertical wall, confirming reachability is part of the rule.

## Hypothesis

Run four-neighbor BFS from the unique 2 through cells whose value is not 8. Copy the input, then recolor only visited cells: even BFS distance to 3, odd distance to 4. Leave walls and all unreachable cells unchanged.

## Probe before checker

I implemented the hypothesis directly and compared it against every visible training output. The intended invariants are:

1. exactly one seed is required;
2. input is not mutated;
3. only reachable non-wall cells change;
4. seed is distance zero and therefore becomes 3.

No failed natural revision occurred; the first hypothesis was already uniquely supported by the visible disconnected-chamber examples.
