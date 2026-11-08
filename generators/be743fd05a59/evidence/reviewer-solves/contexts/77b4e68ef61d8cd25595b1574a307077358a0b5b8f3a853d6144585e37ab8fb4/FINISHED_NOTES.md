# Visible-only solve work log

This is an authored work log, not a token-level model trace.

## Exposure declaration

Before the assignment draw, I opened packet instructions and generic repository
guidance. An initial overbroad archive inventory also requested README files;
its output was heavily truncated. I did not knowingly view this task's generator,
rule, answer labels, or an earlier solution, but cannot certify the entire
earlier README exposure. Earlier exposure is therefore recorded as **unknown**.
After preparation I used only this directory's public challenge and my Python
experiments. No reference was consulted during the solve.

## Attempt 1

Visible examples preserve every original cell. They add color 5 one row below
and one column left of color 9, only when the destination is inside the grid
and was background 0. An occupied destination remains unchanged.

The visible shapes are respectively 8 by 10, 9 by 11, and 8 by 10 for both
input and output. Query inputs are 8 by 12 and 10 by 11; their output shapes
and labels were not supplied.

I enumerated all 24 nonzero offsets in a 5 by 5 neighborhood using only the
three visible pairs. Only offset (+1, -1) matched all three. The complete
probe result is `visible_probe.json`. This supports the implemented local rule;
it does not prove uniqueness among arbitrary hypotheses.

No earlier solution attempt failed. I will retain the actual checker result
and finish when all visible examples and query executions pass. Query
correctness remains withheld from the reviewer.
