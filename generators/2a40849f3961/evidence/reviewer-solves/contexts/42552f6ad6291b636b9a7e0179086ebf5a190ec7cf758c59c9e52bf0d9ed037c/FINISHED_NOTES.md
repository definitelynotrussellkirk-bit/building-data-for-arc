# Solve work log

This is a human work log, not a captured model trace. Before this solve I had already reviewed the assigned generator and Racket authority, so earlier rule exposure is **yes**. During this solve I did not reopen the generator, authority, reference solutions, private query labels, or earlier solution explanations; I used only the visible examples printed by `solve_episode.py prepare` and the visible-only checker.

## Revision 1

**Visible observation.** Each input has gray (`5`) barriers, one checkpoint of each color `1,2,3,4`, and open background `0`. The output preserves barriers and checkpoints and paints cyan (`8`) paths connecting consecutive checkpoint colors. Example 2 shows a route detouring around barriers rather than a bounding-box or straight-line fill. The three visible examples are consistent with independent shortest 4-neighbor paths `1→2`, `2→3`, `3→4`, painting only interior zeros.

**Tie hypothesis.** The visible tie-shaped example is consistent with breadth-first neighbor priority up, down, left, right. I implemented that explicit order rather than relying on dictionary/set iteration. Each leg searches the original input, so paths do not block one another; overlapping route cells are merged before painting.

**Edge behavior.** If a leg is unreachable, it contributes no cells. Walls and colored checkpoints are never overwritten. Output shape is unchanged and the input is not mutated.

**Alternatives rejected.** Manhattan L-shapes fail around barriers. A single global route search could couple legs incorrectly. Treating newly painted `8` cells as blockers would make output depend on processing order. Right-before-left tie breaking remains the main uncertainty to be tested against the visible examples.

## Revision 2

The first check did not reach semantic comparison: Python raised `RuntimeError: deque mutated during iteration` because I iterated directly over a deque while appending neighbors. This was an implementation error, not evidence against the path hypothesis. I replaced that loop with the standard `while queue: popleft()` BFS and changed nothing else.
