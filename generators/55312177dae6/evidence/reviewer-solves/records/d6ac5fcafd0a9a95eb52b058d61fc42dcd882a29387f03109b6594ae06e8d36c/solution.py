"""Visible-example solution for blind task 55312177dae6."""


def _rotate_clockwise(shape):
    """Rotate a rectangular tuple-of-tuples 90 degrees clockwise."""
    return tuple(tuple(row[c] for row in reversed(shape)) for c in range(len(shape[0])))


def _reflect(shape):
    """Mirror a shape left-to-right."""
    return tuple(tuple(reversed(row)) for row in shape)


def _canonical_dihedral(shape):
    variants = []
    current = shape
    for _ in range(4):
        variants.append(current)
        variants.append(_reflect(current))
        current = _rotate_clockwise(current)
    return min(variants)


def _components(grid):
    height = len(grid)
    width = len(grid[0])
    seen = set()
    result = []

    for r in range(height):
        for c in range(width):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for nr, nc in ((rr - 1, cc), (rr + 1, cc), (rr, cc - 1), (rr, cc + 1)):
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] != 0
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))

            min_r = min(rr for rr, _ in cells)
            max_r = max(rr for rr, _ in cells)
            min_c = min(cc for _, cc in cells)
            max_c = max(cc for _, cc in cells)
            cell_set = set(cells)
            shape = tuple(
                tuple(1 if (rr, cc) in cell_set else 0 for cc in range(min_c, max_c + 1))
                for rr in range(min_r, max_r + 1)
            )
            result.append(
                {
                    "shape": shape,
                    "signature": _canonical_dihedral(shape),
                    "min_r": min_r,
                    "max_r": max_r,
                    "min_c": min_c,
                    "max_c": max_c,
                }
            )
    return result


def solve(grid):
    """Rotate the rightmost member of the repeated shape family clockwise."""
    components = _components(grid)
    by_signature = {}
    for component in components:
        by_signature.setdefault(component["signature"], []).append(component)

    repeated = [group for group in by_signature.values() if len(group) >= 2]
    if not repeated:
        raise ValueError("no repeated shape family found")

    # The visible examples contain one repeated family. Prefer the most frequent
    # family, then the one with more occupied cells for deterministic behavior.
    family = max(
        repeated,
        key=lambda group: (
            len(group),
            sum(sum(row) for row in group[0]["shape"]),
        ),
    )
    chosen = max(
        family,
        key=lambda component: (
            component["max_c"],
            component["min_c"],
            component["max_r"],
        ),
    )
    rotated = _rotate_clockwise(chosen["shape"])
    return [[8 if value else 0 for value in row] for row in rotated]
