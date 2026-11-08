# Solve notes

This is a human work log based only on the visible prepared examples during this solve episode. I had already inspected the task rule while repairing the generator, so this is explicitly an exposed post-repair solve, not a blind solve; I did not reopen the generator, Racket rule, reference solutions, or private query labels after preparation.

## Observations

- Every output has the input shape and contains only 0 and 9.
- Color 8 acts as a wall. Color 2 is the start and color 3 the goal.
- Example 0's painted route detours through color 4 before color 6 and through color 5 before color 7.
- Examples 1 and 4 are all-zero despite geometric connectivity. In each, a needed key is placed behind its matching door, suggesting an unreachable-state signal rather than “paint all corridors.”
- Example 2 paints the direct start-to-goal route and ignores a side branch containing special colors, so the rule is shortest lawful route, not “collect every key.”
- The consistent pairings are key 4 → door 6 and key 5 → door 7.

## Hypothesis

Run breadth-first search in `(row, column, has-key-4, has-key-5)` state space. Walls 8 are blocked; door 6 is blocked until key 4 is held and door 7 until key 5 is held. Paint every coordinate on the first shortest lawful path with 9 on an otherwise zero grid. Return all zeros when no lawful state reaches the goal.

To preserve any visible tie behavior, I use neighbor order up, down, left, right. Key acquisition is represented as a same-cell state transition placed at the front of the queue, so the subsequent moves carry the newly acquired key without adding spatial distance.

## Expected query behavior

- Query 0 appears to be the bypass profile: start 2 at row 6 can reach goal 3 through the right corridor without needing either dead-end key/door branch. The BFS should paint only that shortest route.
- Query 1 appears to require key 4 before door 6, then key 5 before door 7 on the route toward goal 3. The stateful BFS should include the necessary detours and doors.
