# Area parity / anchor threshold parametric family

This task-local native family keeps the source puzzle’s connected-component and
area-counting work while adding one episode-fixed rule choice.

| `rule_mode` | Behavior |
| --- | --- |
| `area_parity` (default) | Exact canonical program: odd-area components become 3 and even-area components become 4. |
| `anchor_threshold` | Find the unique red component, bind its area `k`, then recolor every component 3 when its area is below `k` and 4 otherwise. |

The alternative has a real causal dependency. **A** finds the unique red
four-connected component and counts it. The input-dependent intermediate is its
area `k`. **B** cannot choose any component’s comparison color until `k` is
known. A wrong `k+1` moves every equality-size component from 4 to 3; the retained
protected-Racket witness records that changed final output.

The adapter supports exact integer seeds in `0..2**63-1`, 2–6 demonstrations,
and 1–4 queries independently. Inputs are matched across settings. Separate
per-index RNG streams make demonstration and query prefixes stable when counts
change. Every scene has one red anchor and components below, equal to, and above
its size. The first two demonstrations use different anchor thresholds and
reject the declared parity, fixed-threshold, non-strict-boundary, bbox-area,
smallest/largest, and constant-color shortcuts.

The four queries cover ordinary transfer, a different threshold and geometry,
boundary-touching components, and a substantive 30×30 scene spread across the
canvas. Query labels, settings, and programs remain private. A controller exposes
only demonstrations and one current query input; the first visible turn is byte-
identical whether one or four queries were generated.

From the packet root, focused tests and native qualification are run through
`review.py`; owner acceptance and training admission remain separate downstream
gates.
