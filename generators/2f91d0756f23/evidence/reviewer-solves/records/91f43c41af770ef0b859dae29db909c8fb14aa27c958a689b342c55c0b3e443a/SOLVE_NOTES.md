# Blind solve notes — 2f91d0756f23

## Attempt 1

Hypothesis: the color-9 cell is a rotation center.  The count of color-1 cells
in the top row is an instruction telling how many successive orientations of
the colored motif to keep, including the original.  Each added orientation is a
90-degree clockwise rotation around 9; the color-1 instruction cells disappear.

Evidence from the visible pairs:

- One marker: no motif copy is added.
- Two markers: the cell at offset `(-2,-1)` from 9 gains a copy at `(-1,+2)`,
  exactly one clockwise quarter-turn.
- Three markers: each seed has its original, +90°, and +180° positions; the
  +270° member is absent.
- Four markers: every non-9 seed completes its full four-cell rotational orbit.

The implementation snapshots the original nonzero motif cells so newly written
copies are not recursively copied.  It removes every color-1 marker, preserves
the pivot, and clips only as a defensive guard (all demonstrated rotations fit).
