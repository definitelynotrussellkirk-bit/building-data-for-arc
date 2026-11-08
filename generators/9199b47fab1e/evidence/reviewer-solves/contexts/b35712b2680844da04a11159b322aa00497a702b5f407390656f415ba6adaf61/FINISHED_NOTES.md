# Solve work log

## Exposure declaration before solving

I had already inspected and repaired this task's generator and selected rule, so
this is an exposed reviewer solve, not a blind inference record. During this
solve phase I did not reopen the generator, Racket source, reference solutions,
or private labels; I used only the visible examples printed by `prepare`.

## Revision 1 — multi-source barrier-aware distance bands

All three demonstrations preserve the nonzero frame/partition color (8, 6, or
7) and preserve zero regions that are cut off from every color-2 cell. Within a
seeded open region, every source changes from 2 to 3, cardinal neighbors become
4, cells at distance two become 5, and the 3/4/5 cycle repeats. With several
sources, the visible pattern follows the minimum cardinal path from any source.

Hypothesis: treat every cell other than 0 or 2 as an impassable wall. Run one
multi-source four-neighbor BFS from all 2 cells through 0/2 cells. Recolor each
reached cell by shortest distance modulo three using 0→3, 1→4, 2→5; leave walls
and unreachable cells unchanged.

The two queries include closed and nested/partitioned chambers, so a plain
Manhattan-distance fill would incorrectly cross walls and color the outside.
The implementation therefore computes true path distance within traversable
components rather than using coordinate distance.
