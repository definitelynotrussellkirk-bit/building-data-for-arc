# Solve notes — 302ddfbe2baa

## Exposure declaration

This is the required post-repair solve. I had already inspected and repaired the generator and canonical rule before this episode, so this is **not blind**. During the solve episode itself I read only `solve/challenge.json`; I did not consult the generator, Racket source, private labels, reference solutions, or earlier solution explanations.

## Visible-example hypothesis

All three demonstrations support one row-local transformation:

1. Every yellow `4` is a source.
2. Scan strictly to its right.
3. Replace only background `0` cells with cyan `8`.
4. Stop before the first maroon `9`, or at the right boundary.
5. Preserve the source, blockers, and any other nonzero color.

The second demonstration is the key pass-through probe: a `2` lies on the live ray and is preserved while zeros after it still become `8`. The third demonstration disambiguates direction and blocker choice: the nearer `9` is left of the source, while the intended ray still travels right and stops at the first of two right-side `9`s.

## Implementation

`solve/solution.py` copies the grid, scans every input `4`, and paints input-zero cells to the right until an input `9` is encountered. It deliberately reads blockers and paint eligibility from the original input so overlapping effects cannot change stopping behavior.

## Stopping reason

One general program explains every visible pair, includes the two explicit shortcut-counterexamples, and requires no special casing. I stopped after its first visible check.
