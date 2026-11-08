# Fresh visible-example solve notes

I used only `solve/challenge.json` during this solve. I had already reviewed this task's generator and rule before the solve episode, so the finish record must mark earlier exposure as **yes**; I did not reopen or consult those references while solving.

## Hypothesis

The color-8 full columns split each input into three equal-width panels. The first and second panels show a foreground support before and after a growth operation. The output is the third/query support plus the cells that were added from the first support to the second, recolored with the query color and clipped at the query panel boundary.

Foreground placement is irrelevant, so I normalize supports by bounding-box top-left before comparing them. Three demonstrations directly fit `delta = AFTER - BEFORE` after normalization. In the fourth, two translations of BEFORE overlap AFTER equally well. The translation that makes the largest number of distinct, in-bounds changes to QUERY yields exactly the visible output. I therefore use maximum support overlap, then maximum observable novelty on the query, as the tie-break.

## Visible checks made before execution

- Demo 1: inferred additions `(1,1)` and `(2,0)` complete the color-5 query.
- Demo 2: additions `(0,1)` and `(1,2)` produce the sparse color-5 result rather than simply copying the second panel.
- Demo 3: one of two additions falls below the grid and is clipped; the visible result is the remaining 2x2 block.
- Demo 4: the overlap/novelty tie-break selects additions `(0,1)` and `(1,2)`, matching both newly painted cells.

Predicted tests:

1. Complete the color-7 L into the same five-cell pattern shown in panel two.
2. Preserve the horizontal color-2 triple and add one cell below its middle plus one two rows below its left end.

No failed solution revisions were invented; the first executable version implements this hypothesis.
