# Solve notes

Human-readable work log based only on the prepared visible examples during this solve phase.

Hypothesis: color 5 cells are impermeable walls. Treat every maximal 4-connected region of non-5 cells as a chamber. Count seed cells colored 1, 2, or 3 in each chamber. A chamber with exactly one seed is filled completely with that seed color; chambers with zero or multiple seeds are cleared to 0. Walls remain 5 and shape is unchanged.

Checks against the three demonstrations:
- Example 0: the isolated color-2 chamber fills; the chamber containing three color-1 seeds clears.
- Example 1: only the bottom-left single-1 chamber fills; the three-seed chamber clears.
- Example 2: the local vertical wall segment must count as a real separator, allowing the one-seed chamber to fill while adjacent multi-seed chambers clear.

Implementation uses an explicit 4-neighbor flood traversal and constructs a fresh output grid.
