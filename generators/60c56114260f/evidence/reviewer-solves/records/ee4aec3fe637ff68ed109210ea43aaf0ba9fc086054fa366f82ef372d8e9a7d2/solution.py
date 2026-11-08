from __future__ import annotations


def _normalise(cells: set[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    """Translate a finite cell set so its top-left occupied cell is at (0, 0)."""
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return tuple(sorted((r - min_r, c - min_c) for r, c in cells))


def _rotation_signature(cells: set[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    """Canonicalise a shape up to quarter-turn rotations (not reflections)."""
    variants: list[tuple[tuple[int, int], ...]] = []
    current = set(cells)
    for _ in range(4):
        variants.append(_normalise(current))
        current = {(c, -r) for r, c in current}
    return min(variants)


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Return the reading-order shape-equivalence matrix.

    Each non-zero colour denotes one object. Objects are ordered by the top-left
    occupied cell of their bounding box. Cells are marked 8 when the corresponding
    two objects have the same shape after translation and rotation; otherwise 0.
    """
    by_colour: dict[int, set[tuple[int, int]]] = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                by_colour.setdefault(value, set()).add((r, c))

    objects = sorted(
        by_colour.values(),
        key=lambda cells: (
            min(r for r, _ in cells),
            min(c for _, c in cells),
        ),
    )
    signatures = [_rotation_signature(cells) for cells in objects]
    return [
        [8 if signatures[i] == signatures[j] else 0 for j in range(len(objects))]
        for i in range(len(objects))
    ]
