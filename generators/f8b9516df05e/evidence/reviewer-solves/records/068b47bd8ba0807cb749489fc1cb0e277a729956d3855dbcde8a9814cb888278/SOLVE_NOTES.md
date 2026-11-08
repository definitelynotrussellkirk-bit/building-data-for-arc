# Solve work log

## Prior exposure

Before this blind episode I had read only the packet-level instructions and the
assignment text. I did not open the generator, canonical rule, task notes,
reference solution, private labels, or any earlier explanation for task
`f8b9516df05e`.

## Revision 1 — rightward colored-seed rays

### Observations

Every changed training row contains a nonzero, non-gray colored cell to the left
of a gray `8`, with only background `0` cells between them. The output preserves
the endpoints and recolors the intervening zeros with the left endpoint's color.
Examples include a length-two red extension in train 0 row 6 and a length-four
red extension in train 1 row 8. Rows without such a pair remain unchanged.

Train 1 row 3 also contains a second gray cell farther right. The colored `1`
stops at the first non-background cell, so the nearer gray endpoint appears to
bound the ray. Test query 0 row 5 contains `3,0,8,0,8,4,9`; treating the *next
non-background* cell as the endpoint gives a short `3` segment while avoiding a
line that crosses the adjacent `4,9` cells.

### Hypothesis

For each colored cell other than `8`, scan right across zeros. If the next
nonzero cell is gray `8`, fill the zeros in between with the seed color. Do not
cross another colored or gray cell, and do not extend leftward.

### Program

`solution.py` copies the grid, applies that row-local scan independently to every
non-gray seed, and preserves shape and all original nonzero cells.

### Remaining uncertainty

The visible training examples only demonstrate gray endpoints to the right.
A bidirectional "connect through clear background to an adjacent gray endpoint"
rule would agree on those examples and likely on the provided queries, because
the only colored cells right of a gray endpoint in query 0 are adjacent or
blocked by another color. I selected the directional rule because every taught
change has a colored left endpoint and gray right endpoint.
