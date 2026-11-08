# Solve work log

I had not opened the generator, Racket rule, canonical row, prior solutions, or
private labels before this blind solve. I had only read packet-level operating
instructions and the visible `challenge.json`.

## Revision 1 — pairwise maze paths with a nested-route guard

The non-8 cells form a single acyclic maze in every visible example. Colors 2,
3, 4, and 5 are terminals. In each of the first four examples, the output's 7s
are exactly the zero-valued cells on the union of the unique paths 2↔3 and 4↔5.
I checked all three possible pairings; examples 2 and 4 (zero-indexed 1 and 3)
distinguish the intended pairing because 4 and 5 are adjacent while an extra
connector cell would appear under the other pairings.

The fifth example is unchanged. There the complete 4↔5 path is contained in the
2↔3 path (both 4 and 5 lie along the latter). My working interpretation is that
wholly nested requested routes are invalid/blocked, so the grid is left alone.
In the other positive examples the paths are disjoint or share only a short tail
at one terminal; neither path contains the other.

I implemented breadth-first path recovery (the maze is a tree, so the path is
unique), the nested-path no-op, and otherwise recolored only zero cells in the
union to 7. Remaining uncertainty: the visible data establishes the nested case
but not a precise alternative threshold for long partial overlaps. Both query
mazes are non-nested, so the observed positive rule gives unambiguous outputs.
