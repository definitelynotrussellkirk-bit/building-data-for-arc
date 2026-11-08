# Post-repair visible-only solve notes

Earlier exposure: **yes**. I reviewed this task's generator and canonical rule before
this solve episode. During this solve phase I used only `solve/challenge.json` and
did not reopen the generator, Racket source, reference solution, or private labels.

## Hypothesis

The 9s form immutable outer frames and the 5s form immutable internal dividers.
Every other nonzero cell is a colored key. In each visible pair, the key's color
fills exactly the 4-connected zero component reachable from that key without
crossing a 5 or 9. Other disconnected chambers stay zero. When two keys occur,
each is processed against the original input, so one key color is not traversable
by another.

## Implementation

Copy the input, enumerate all non-{0,5,9} keys in row-major order, and run a
four-neighbor BFS from each key through cells whose original value is either 0
or that key's color. Paint reached cells in the output, preserving 5 and 9.

## Checks considered

- Train 1 has two keys in different left-frame regions; both regions fill while
  the right frame remains unchanged.
- Train 2 has one key; only its lower-left chamber fills.
- Train 3 has keys in different frames; each fill stops at the nearest 5/9 walls.
- Test inputs contain the same roles and no conflicting key inside one component.
