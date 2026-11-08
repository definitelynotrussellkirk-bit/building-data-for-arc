# Visible-example solve: reviewer-authored work log

This is a concise human-readable record of observations and experiments, not a captured token-level model trace. Earlier exposure: **yes**. I reviewed the task's generator and Racket authority before this phase. From `solve_episode.py prepare` through `finish`, I opened only the visible challenge and my own Python candidate/test files; I did not consult the generator, Racket source, previous solutions or private labels. This is **not a blind solve**.

## Observations from the three visible demonstrations

The background and occupied positions are preserved. Output colours are 2, 3 and, when there are three objects, 4. In example 0 the disconnected objects have 12, 13 and 15 occupied cells, receiving 2, 3 and 4. Example 1 has areas 4, 5 and 8 with the same ascending assignment. Example 2 has areas 6 and 8, assigned 2 and 3. Example 0 is multicoloured; examples 1 and 2 demonstrate that objects of the same input colour receive different output colours.

The sparse L in example 0 occupies a 7-by-7 box but has 13 cells and receives 3, whereas the compact 15-cell object receives 4. In example 2 the smaller L has a larger bounding box than the 8-cell compact object. Thus box area is not the measured quantity. Top-left scan order also fails: the first object receives 3 in all three examples. Input-colour remapping cannot explain examples 1 and 2. A fixed L-to-colour rule also fails across these examples.

## Candidate and checks

The candidate performs a four-neighbour flood fill on nonzero cells, sorts objects by occupied cell count, and repaints them with successive colours beginning at 2. It does not look up examples. Input validation deliberately rejects tied sizes and object counts outside the demonstrated two/three-object domain instead of inventing those behaviours. Runtime is linear in grid size plus the small object sort.

`test_solution.py` was created first. Its initial failure (`preimplementation_test.log`) says only that no candidate existed; it is **not a failed solve attempt**. The first and only actual candidate is `solution.py`. Visible-example and transpose/purity checks pass. No deliberately wrong candidate was submitted as an ordinary solve, and no failed solve was fabricated.

The official check records one ordinary `solve` attempt. Masked queries are executed by that tool, but correctness feedback is withheld. Neither successful execution nor agreement with the three visible examples proves query accuracy. The final stopping reason is visible agreement and successful execution, pending independent intake scoring.
