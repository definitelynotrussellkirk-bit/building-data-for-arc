from __future__ import annotations


def _rot90(tile: list[list[int]]) -> list[list[int]]:
    """Rotate a square tile 90 degrees clockwise."""
    return [list(row) for row in zip(*tile[::-1])]


def _identity(tile: list[list[int]]) -> list[list[int]]:
    return [row[:] for row in tile]


def _rot180(tile: list[list[int]]) -> list[list[int]]:
    return _rot90(_rot90(tile))


def _rot270(tile: list[list[int]]) -> list[list[int]]:
    return _rot90(_rot180(tile))


def _flip_lr(tile: list[list[int]]) -> list[list[int]]:
    return [row[::-1] for row in tile]


def _flip_ud(tile: list[list[int]]) -> list[list[int]]:
    return tile[::-1]


def _transpose(tile: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*tile)]


def _anti_diagonal(tile: list[list[int]]) -> list[list[int]]:
    # Reflection across the top-right to bottom-left diagonal.
    return [list(row) for row in zip(*tile[::-1])][::-1]


_TRANSFORMS = {
    "identity": _identity,
    "rot90": _rot90,
    "rot180": _rot180,
    "rot270": _rot270,
    "flip_lr": _flip_lr,
    "flip_ud": _flip_ud,
    "transpose": _transpose,
    "anti_diagonal": _anti_diagonal,
}

_INVERSE = {
    "identity": "identity",
    "rot90": "rot270",
    "rot180": "rot180",
    "rot270": "rot90",
    "flip_lr": "flip_lr",
    "flip_ud": "flip_ud",
    "transpose": "transpose",
    "anti_diagonal": "anti_diagonal",
}


def _separator(grid: list[list[int]]) -> tuple[int, int]:
    height = len(grid)
    width = len(grid[0])
    for row_index, row in enumerate(grid):
        if len(set(row)) != 1:
            continue
        color = row[0]
        for col_index in range(width):
            if all(grid[r][col_index] == color for r in range(height)):
                return row_index, col_index
    raise ValueError("no crossing separator row and column found")


def _matching_transforms(
    source: list[list[int]], target: list[list[int]]
) -> list[str]:
    return [name for name, transform in _TRANSFORMS.items() if transform(source) == target]


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Complete the missing quadrant by extending the row-wise symmetry analogy."""
    sep_row, sep_col = _separator(grid)
    quadrants = [
        [row[:sep_col] for row in grid[:sep_row]],
        [row[sep_col + 1 :] for row in grid[:sep_row]],
        [row[:sep_col] for row in grid[sep_row + 1 :]],
        [row[sep_col + 1 :] for row in grid[sep_row + 1 :]],
    ]

    blank_indices = [
        index
        for index, tile in enumerate(quadrants)
        if tile and all(cell == 0 for row in tile for cell in row)
    ]
    if len(blank_indices) != 1:
        raise ValueError(f"expected one blank quadrant, found {len(blank_indices)}")
    missing = blank_indices[0]

    # Infer the left-to-right dihedral transform from whichever row is complete,
    # then apply that same analogy to the incomplete row.
    if missing in (2, 3):
        matches = _matching_transforms(quadrants[0], quadrants[1])
        source = quadrants[2] if missing == 3 else quadrants[3]
        use_inverse = missing == 2
    else:
        matches = _matching_transforms(quadrants[2], quadrants[3])
        source = quadrants[0] if missing == 1 else quadrants[1]
        use_inverse = missing == 0

    if not matches:
        raise ValueError("the complete quadrant pair is not related by a square symmetry")

    candidates = []
    for name in matches:
        chosen = _INVERSE[name] if use_inverse else name
        candidate = _TRANSFORMS[chosen](source)
        if candidate not in candidates:
            candidates.append(candidate)
    if len(candidates) != 1:
        raise ValueError("visible pair leaves multiple different completions")
    return candidates[0]
