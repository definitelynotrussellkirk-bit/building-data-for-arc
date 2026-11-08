# 2006f915df8b — Trace the shortest corridor path

Generator version 3.0.0; unchanged Racket rule hash `24791e9d8fc8`.

Trace a shortest four-neighbor route from red 2 to green 3 through cells other than gray wall 5. Paint only original-zero interior path cells cyan 8, preserving all other cells and the grid dimensions. Canonical inputs may contain tied shortest routes; generated inputs select a unique shortest route.

Production alternates stretched two-loop teaching witnesses and varied lattice mazes with trees, branches, and loops. The two dimension axes cover height 7–12 and width 8–14 in every difficulty. Three demonstrations and one query are checked against 27 named competitors, including a goal-greedy shortcut that fits all canonical pairs. Duplicate rejection is accounted for by witness endpoint parity and alternating vertical endpoint order. See notes.md, task-local tests, retained counterexample, and return reports for measured scope and limitations.
