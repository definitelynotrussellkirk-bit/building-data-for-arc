"""
Solvers — modular, composable strategy generators for ARC-AGI tasks.

Architecture:
  base.py           — Solver base class, registry, runner
  registry.py       — Auto-discovery and registration of all solvers
  runner.py         — Try all solvers on a task, rank by confidence
  scorer.py         — Test solvers against training pairs

  color/            — Color mapping strategies
  frame/            — Rectangular frame strategies
  gravity/          — Movement/gravity strategies
  structural/       — Line drawing, connecting, extending
  pattern/          — Tiling, key-template, lattice strategies
  filter/           — Neighbor-based filtering strategies
  object/           — Object-level manipulation strategies

Each solver:
  1. Has a `can_solve(task) -> float` (0-1 confidence it can handle this)
  2. Has a `solve(task) -> rule_fn` (returns a grid→grid function)
  3. Inherits from Solver base class
  4. Is auto-registered by the registry
"""
