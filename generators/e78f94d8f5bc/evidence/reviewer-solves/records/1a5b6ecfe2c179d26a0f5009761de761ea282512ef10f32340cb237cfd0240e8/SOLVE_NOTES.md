# Solve notes

This final solve is bound to generator SHA-256 `92d7322e92d454be7e44ee31cdf557008e8faa7e55e3d70a7173dedf4e165bae`. I had already seen the task semantics during generator review, so earlier exposure is `yes`. During this solve episode I used only the newly prepared visible examples and did not reopen the generator, Racket authority, reference solution, private labels, or the earlier solve archive.

Across all three examples, colors 1 and 2 stay fixed. A subset of color-0 cells becomes 4, and those cells form the walkable four-neighbor route joining the two color-2 endpoints; unused walkable branches remain 0. I implemented breadth-first search through colors 0 and 2, reconstruct the shortest route, paint it 4, and restore both endpoint cells to 2.

The visible inputs are maze-like and appear to have a unique route. The neighbor order only supplies deterministic behavior if a future malformed input has a tie.
