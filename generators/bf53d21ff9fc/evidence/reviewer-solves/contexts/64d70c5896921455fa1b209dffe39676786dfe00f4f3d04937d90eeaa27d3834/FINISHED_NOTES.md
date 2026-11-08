# Solve work log

## Exposure declaration before solving

I had not opened the generator, Racket rule, prior solutions, private labels, or notes for blind task `bf53d21ff9fc`. I used only `solve-blind/challenge.json` and my own reasoning/code.

## Revision 1 — graph path from a 5 to a 0-3-0 terminal

**Observed transformation.** The dominant color is background. A movable object is a `5` connected by a four-neighbor chain of `3` cells to the center `3` of a straight `0,3,0` terminal. The chain approaches the terminal perpendicular to the terminal's zero pair. The output erases the source and traversed `3` path, retains the `0,3,0` terminal, and places the `5` on the path cell immediately adjacent to the terminal center.

**Evidence from visible pairs.** In train pair 1, the lower-left `5` traverses the horizontal-then-vertical 3-chain and lands immediately below the top horizontal `0,3,0`; the unrelated lower `5` remains. In pair 3, the upper-left `5` similarly lands immediately above the lower horizontal terminal. Pair 2 contains two complete routes that move and incomplete/disconnected structures that remain, which rules out globally deleting all lines or moving every `5`.

**Implementation.** Detect terminal centers, search outward from only their perpendicular arrival sides through `3` cells until a `5` is reached, reconstruct that path, erase only its source/interior, and place `5` on the penultimate cell. Preserve incomplete structures and unrelated `5`s.

**Remaining uncertainty.** The visible examples do not specify ambiguous components with several reachable `5`s or multiple joined terminals. The implementation uses deterministic breadth-first search and prevents overlapping routes from being processed twice.

## Revision 2 — fix source-reachability bug

Revision 1 received `visible_passed: 0/3`. A direct comparison against the first visible pair showed the output was unchanged. Tracing the breadth-first search found the root cause: expansion admitted only value `3`, while the stopping condition looked for value `5`; therefore a source `5` more than one cell from the terminal could never enter the queue. A focused regression test, `solve-blind/tests/test_solution.py::test_reaches_source_five_at_far_end_of_three_path`, reproduced the failure before the change. The minimal correction admits both `3` and `5` when expanding, while the search still stops immediately when it reaches a `5`.
