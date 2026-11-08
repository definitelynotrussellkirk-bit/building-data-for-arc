# Solve work log

## Exposure declaration before solving

I had not opened task `348efda982ab`'s generator, Racket rule, reference
solutions, private labels, notes, or audit records. I used only
`solve-blind/challenge.json` and my own local analysis of its visible examples.

## Revision 1 — room marker count equals door count

**Hypothesis.** Colors 1 and 9 form walls, while 7 marks doors in those walls.
Treating all three as boundaries partitions the non-wall cells into rooms. The
output first erases every green marker (3). It fills a room with 8 exactly when
that room contains as many green markers as it has distinct adjacent doors;
otherwise the room becomes 0. Doors and walls are unchanged.

**Probe.** I enumerated 4-connected room components while treating 1, 7, and 9
as blocked, then counted green cells and distinct orthogonally adjacent 7 cells.
Across the three visible examples, every filled room had equal counts, including
the zero-marker/zero-door room in training example 2. Every unfilled room had
unequal counts. Representative contrasts: training example 1 has a 2-marker,
2-door room that fills beside a 2-marker, 3-door room that does not; training
example 3 has 2-marker rooms with 2 versus 3 doors and only the former fill.

**Implementation.** `solve` performs one BFS per room, collects adjacent door
coordinates to avoid double-counting a long/shared contact, and writes either 8
or 0 to the room. It leaves 1, 7, and 9 untouched.

**Alternatives rejected.** Marker count alone fails because rooms with the same
count receive different outputs. Reachability through doors also fails because
connected rooms can receive different outputs. Degree equality explains every
visible room, including the otherwise easy-to-miss 0 = 0 case.

**Remaining uncertainty.** The examples show only orthogonal doors and regular
wall partitions. The implementation follows the visible four-neighbor geometry
and counts a door once even if it touches more than one cell of the same room.
