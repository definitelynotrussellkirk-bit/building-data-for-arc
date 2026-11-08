"""Random-walk blob placement — useful for generators that need
multiple non-touching connected components."""
from __future__ import annotations

import random


Cell = tuple[int, int]


def has_neighbor(p: Cell, used: set[Cell],
                 ignore: frozenset[Cell] = frozenset()) -> bool:
    """True if p has an orthogonal neighbor in `used` (excluding `ignore`)."""
    r, c = p
    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nb = (r + dr, c + dc)
        if nb in ignore:
            continue
        if nb in used:
            return True
    return False


def grow_blob(rng: random.Random, h: int, w: int,
              used: set[Cell], target_size: int,
              *, max_attempts: int = 50) -> set[Cell] | None:
    """Random-walk grow a connected blob of `target_size` cells, where
    no cell of the blob is orthogonally adjacent to any cell in `used`
    (so the blob is isolated from existing content).

    Returns the blob as a set, or None if it couldn't fit after
    `max_attempts` tries. Does NOT mutate `used` (caller should
    `used |= blob` if accepting)."""
    for _ in range(max_attempts):
        seed = (rng.randint(0, h - 1), rng.randint(0, w - 1))
        if seed in used or has_neighbor(seed, used):
            continue
        cells = {seed}
        frontier = [seed]
        while frontier and len(cells) < target_size:
            r, c = frontier.pop(rng.randint(0, len(frontier) - 1))
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nr, nc = r + dr, c + dc
                if not (0 <= nr < h and 0 <= nc < w):
                    continue
                cand = (nr, nc)
                if cand in cells or cand in used:
                    continue
                # `cells` themselves don't count as "used" for adjacency,
                # since the blob can self-touch by definition.
                if has_neighbor(cand, used, ignore=cells):
                    continue
                cells.add(cand)
                frontier.append(cand)
                if len(cells) == target_size:
                    break
        if len(cells) == target_size:
            return cells
    return None


def bbox_of(cells: set[Cell]) -> tuple[int, int, int, int]:
    """Inclusive bbox (r1, c1, r2, c2) of a cell set.

    Delegates to `puzzle_generators.helpers.indices.bbox` so there is
    one canonical Python bbox-of-cells implementation. See
    docs/OWNERSHIP.md."""
    from .indices import bbox  # local: blobs ↔ indices avoid cycle
    return bbox(cells)


def bbox_overlaps(bb1, bb2) -> bool:
    """Inclusive bbox overlap test."""
    r1a, c1a, r2a, c2a = bb1
    r1b, c1b, r2b, c2b = bb2
    return not (r2a < r1b or r2b < r1a or c2a < c1b or c2b < c1a)
