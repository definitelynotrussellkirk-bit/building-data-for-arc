# Solve work log

## Exposure before solving

I read only the packet-level instructions, the assignment text, and the visible
examples produced by `solve_episode.py blind prepare`. I did not open this task's
generator, canonical rule, reference solutions, private labels, audits, or prior
solution explanations. I do not recall earlier exposure to task `ead22faa41ef`.

## Revision 1 — orthogonal 2/3 pairing

**Hypothesis.** Colors 2 and 3 act as complementary adjacent markers. For every
orthogonally adjacent 2/3 pair, erase the 2 and recolor the 3 to 8. Preserve 5s
and any unpaired 2s or 3s. Pair membership should be determined simultaneously
from the input rather than changed during a scan.

**Evidence from the demonstrations.** In example 0, all four horizontal `2,3`
pairs become `0,8`, while the isolated 2 at `(3,5)` and isolated 3 at `(5,8)`
remain. Example 1 shows that order is irrelevant: horizontal `3,2` pairs also
become `8,0`. Example 2 supplies the vertical case, where each vertically
adjacent 2/3 pair changes the same way and the isolated 2 at `(8,6)` remains.
No diagonal pair is demonstrated, so I restrict adjacency to the four cardinal
directions.

**Implementation.** Scan original color-3 cells, collect all orthogonally
adjacent color-2 cells and their matching 3s, then apply the changes to a copy.
Using sets makes the behavior deterministic if one cell participates in more
than one adjacency, although such an overlap is not visible in the examples.

**Remaining uncertainty.** The visible examples do not show branching overlaps
(one 3 touching multiple 2s or vice versa). The simultaneous all-incidences
interpretation is the simplest extension of the demonstrated local rule.
