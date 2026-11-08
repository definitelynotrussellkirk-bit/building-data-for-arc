"""puzzle_generators — per-puzzle ARC instance generators.

Phase 2 of docs/PUZZLE_GENERATOR_ROADMAP.md.

Public surface:
    from puzzle_generators import gen_ctx, GenCtx
    from puzzle_generators.helpers.grid import full_grid, draw_rect
    from puzzle_generators.helpers.palette import random_palette
"""
from .base import GenCtx, gen_ctx, stable_rng  # noqa: F401
