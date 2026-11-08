# Solve work log

## Exposure declaration

Before this fresh learner-side solve I had already reviewed the assigned generator and the authoritative behavior as part of the repair, so earlier rule exposure is **yes**. During this solve I kept the generator, Racket source, reference solutions, private query labels, and prior solution notes closed. I used only `solve/README.md`, its visible examples, and the visible-example checker.

## Revision 1

**Observed pattern.** Each input has one red cell (`2`), gray walls (`5`), and empty cells (`0`). In every training output, the red cell and all orthogonally reachable non-wall cells in its chamber become azure (`8`). Gray cells are unchanged, and non-wall cells in chambers separated by gray walls remain unchanged.

**Hypothesis.** Treat `5` as an impassable wall, start at the unique `2`, perform a four-neighbor flood fill through every cell whose input color is not `5`, and recolor the reached component to `8`. This explains the large filled chamber in example 0, the small upper-right chamber in example 1, and the small lower-left chamber in example 2. The diagonal wall contacts in the examples also argue against eight-neighbor connectivity.

**Implementation.** `solve/solution.py` copies the grid, validates rectangularity and the unique seed, then uses a queue for four-neighbor breadth-first traversal. It never crosses color `5`; reached cells are painted `8`.

**Alternatives considered.** Filling the largest chamber fails examples 1 and 2. Filling the top-left chamber fails all examples whose seed is elsewhere. Filling an axis-aligned rectangle around the seed is too weak for the irregular open region in example 0. Eight-neighbor flood fill would cross diagonal-only contacts that the visible wall geometry appears designed to distinguish.

**Remaining uncertainty.** The visible examples use only colors `0`, `2`, and `5`. The implementation follows the more general visible rule “traverse any non-5 cell,” but there is no visible evidence for additional traversable colors. The requested task domain appears consistent with this choice.
