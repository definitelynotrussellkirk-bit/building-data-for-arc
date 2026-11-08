# Post-repair solve work log

This is a human-readable work log based only on `solve/challenge.json` during the solve phase. I had already seen the assigned task's rule while reviewing its generator, so this is an **exposed** solve; I did not reopen the generator, Racket source, canonical data, private labels, or earlier solution text while solving.

## Visible-example hypothesis

The top row is an instruction row. Its number of blue `1` cells is `k`; their positions do not matter. The maroon `9` below the header is a rotation anchor. Every other nonzero cell below the header is a colored seed.

The answer is a fresh zero grid. Keep the `9`, clear the header, and for every colored seed paint `k` positions: its original offset from the anchor followed by repeated quarter turns using row/column offset update `(dr, dc) -> (dc, -dr)`.

Evidence from the visible examples:

- With one marker, the two seeds are simply retained and the header disappears.
- With two markers, the seed at offset `(1,-1)` also appears at `(-1,-1)`, fixing the turn direction.
- With three markers, each of two seed colors occupies exactly the first three positions of its four-position orbit.
- With four markers and four seed colors, each seed completes its full quarter-turn orbit.

## Implementation choice

Scan row 0 for `k`, find the unique `9`, collect nonzero/non-9 cells only from rows 1+, and paint turns in the same seed row-major order. Bounds are checked even though the visible examples keep the orbit in-frame.

No failed revision was manufactured; the first concrete implementation directly encodes the rule supported by all four demonstrations.
