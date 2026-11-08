# Exhaustive induced-path rival census

This is a diagnostic census of the complete induced-simple-path domain on a
fixed 5×6 board, at every occupied length from 7 through 20. It does not sample
or import `generator.py`, and it is not evidence about the distribution emitted
by the revised generator. No solve directory or candidate solve was read.
The baseline generator hash supplied as review context was
`a9ad5c0c5a3c1b4eb1dc2db8fdc120f16342fcdc3cb261bbce1aedc4bb4a8efb`;
the census is not bound to that implementation or to any later implementation.

## Result

Even length does not prevent one example from refuting all five
canonical-fitting rivals. Such examples exist at every even length 8–20.
Examples refuting all nine declared rivals exist at every even length 10–20.
There are no all-nine examples of length 8 within this fixed 5×6 domain.

| Occupied length | Distinct induced supports | Refute all five | Refute all nine |
|---:|---:|---:|---:|
| 7 | 1,180 | 236 | 68 |
| 8 | 1,776 | 12 | 0 |
| 9 | 2,542 | 1,008 | 564 |
| 10 | 3,328 | 36 | 8 |
| 11 | 4,380 | 1,744 | 1,212 |
| 12 | 5,440 | 232 | 132 |
| 13 | 7,048 | 3,256 | 2,780 |
| 14 | 7,624 | 592 | 544 |
| 15 | 8,940 | 5,020 | 4,224 |
| 16 | 7,138 | 856 | 728 |
| 17 | 6,860 | 4,248 | 4,120 |
| 18 | 2,274 | 348 | 328 |
| 19 | 928 | 644 | 632 |
| 20 | 222 | 68 | 68 |

Each support is counted once modulo path reversal. Board symmetries and
translations remain separate. Seed 2 is always placed at the raster-later
endpoint and seed 3 at the earlier endpoint, which makes `raster_seed_order`
disagree. All other occupied cells are blue 1 and the background is black 0.
Thus the counts are also exact counts of qualifying inputs under this fixed
seed-orientation convention. No RNG or seed range applies: enumeration is
exhaustive over the stated domain.

The five rivals are `bfs8`, `diagonal_euclidean`, `raster_seed_order`,
`turn_penalty_half`, and `turn_discount_half`. The other four are `manhattan`,
`euclidean_squared`, `chebyshev`, and `turn_penalty_one`.

## Reproduction and verification

Run from the extracted packet root:

```sh
python repo/generators/547c45a21db1/workspace/semantic_review/even_length/enumerate_paths.py --max-length 20 --verify-probe --out checks/semantic-review/even-length/census.json > checks/semantic-review/even-length/census.log
```

The verified run completed successfully in about 10.46 seconds. Every support's
fast all-five classification was cross-checked against the existing `probe.py`
functions. All-five examples were also checked against the other four actual
probe functions to count all-nine refutations. The retained witness grids and
all individual rival differences were computed directly through `probe.py`.

The depth-first search starts at each of the 30 board cells and extends a path
only when a proposed unvisited neighbor touches exactly the current endpoint
among visited cells. This enumerates every simple induced 4-connected path up to
the depth bound. A support is recorded only when its initial endpoint is
raster-later than its final endpoint, eliminating exactly the reverse traversal.

All expected outputs in this census are explicitly Python BFS diagnostics.
This subtask did not execute the retained Racket authority and makes no new
authority-validation claim. `commands.json` records the command, working
directory, exit status, and hashes. `census.json` retains the exact counts and
per-length example grids; a missing counter in that sparse JSON means zero.

## Why both turn rivals can fail on even paths

Index a path of length n from seed 2 at index 0. For an interior cell i, define
T(i) as the number of turns strictly before i minus the number strictly after i.
The ordinary red-minus-green distance is `D(i) = 2i - n + 1`. The two rival
distance differences are `D(i) + T(i)/2` and `D(i) - T(i)/2`.
Both are strictly increasing along the path: moving one cell increases D by 2,
while T increases by at most 2. Consequently their midpoint decisions determine
whether either coloring differs from BFS.

For even length `n = 2m`, define `A = T(m-1)` and `B = T(m)`. Ordinary BFS gives
distance differences −1 and +1 at these two central cells. Both turn rivals
disagree with BFS exactly when `A >= 2` or `B <= -2`. This is possible when
turns are concentrated toward one endpoint. For odd `n = 2m+1`, both disagree
exactly when `T(m) != 0`, because the BFS midpoint is tied. This weaker condition
helps explain the much greater abundance of odd all-rival witnesses.

## A short even witness

Use this length-8 path, with seed 3 at the first coordinate and seed 2 at the
last coordinate:

```python
[(0,0), (1,0), (1,1), (2,1), (2,2), (2,3), (2,4), (2,5)]
```

The `bfs8` and `diagonal_euclidean` rivals assign 3 at (2,2), where BFS assigns
2. `turn_penalty_half` assigns 4 at (2,1), where BFS assigns 3.
`turn_discount_half` also changes (2,2) from 2 to 3. The raster rival exchanges
all six recolored cells. The Manhattan rival agrees, so this witness refutes
eight of the nine rivals. Its complete input, diagnostic output, and differences
are retained in `checks/semantic-review/even-length/hand_witness.json`.
