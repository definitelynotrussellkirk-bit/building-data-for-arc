# Visible-only solve notes

The gray cells (5) are fixed walls. Every other nonzero color is a seed. Within each 4-connected non-gray region, each zero cell takes the color of the reachable seed with the shortest path that does not cross gray. If distances tie, the smaller numeric seed color wins. A region with no seed remains zero.

Evidence from the five visible demonstrations:

- The open chamber examples look like nearest-seed Voronoi fills.
- The partial vertical wall in demonstration 5 changes the boundary relative to raw Manhattan distance, so distance must be shortest path around walls.
- The horizontally split and multi-room examples leave seedless chambers at zero, ruling out a global nearest seed through walls.
- The two-seed examples include equidistant cells where the lower color wins, supporting numeric tie-breaking rather than first-seed order.

Revision 1 implements an independent BFS from every seed, preserves color 5, chooses the lexicographic minimum `(distance, color)`, and leaves cells with no reachable seed at zero.
