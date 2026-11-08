from __future__ import annotations


def _rotate_clockwise(grid: list[list[int]]) -> list[list[int]]:
    """Rotate a square grid 90 degrees clockwise."""
    return [list(row) for row in zip(*grid[::-1])]


def _reflect_left_right(grid: list[list[int]]) -> list[list[int]]:
    """Reflect a grid across its vertical axis."""
    return [row[::-1] for row in grid]


def _symmetries(grid: list[list[int]]):
    """Yield the eight dihedral symmetries of a square grid."""
    rotated = [row[:] for row in grid]
    for _ in range(4):
        yield [row[:] for row in rotated]
        yield _reflect_left_right(rotated)
        rotated = _rotate_clockwise(rotated)


def _infer_color_map(
    transformed_source: list[list[int]], target: list[list[int]]
) -> dict[int, int] | None:
    """Return a consistent nonzero color renaming, or None if masks differ."""
    mapping: dict[int, int] = {}
    reverse: dict[int, int] = {}

    for source_row, target_row in zip(transformed_source, target):
        for source_color, target_color in zip(source_row, target_row):
            if (source_color == 0) != (target_color == 0):
                return None
            if source_color == 0:
                continue

            previous = mapping.get(source_color)
            if previous is not None and previous != target_color:
                return None

            previous_source = reverse.get(target_color)
            if previous_source is not None and previous_source != source_color:
                return None

            mapping[source_color] = target_color
            reverse[target_color] = source_color

    return mapping


def _split_panels(grid: list[list[int]]) -> tuple[list[list[int]], ...]:
    """Split three n×n panels separated by one column each."""
    size = len(grid)
    if size == 0 or any(len(row) != 3 * size + 2 for row in grid):
        raise ValueError("expected three square panels separated by two columns")

    first = [row[:size] for row in grid]
    second = [row[size + 1 : 2 * size + 1] for row in grid]
    third = [row[2 * size + 2 :] for row in grid]
    return first, second, third


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Apply the first-to-second panel analogy to the third panel."""
    first, second, third = _split_panels(grid)
    candidates: list[list[list[int]]] = []

    for transformed_first, transformed_third in zip(
        _symmetries(first), _symmetries(third)
    ):
        color_map = _infer_color_map(transformed_first, second)
        if color_map is None:
            continue

        candidate = [
            [color_map.get(color, color) for color in row]
            for row in transformed_third
        ]
        if candidate not in candidates:
            candidates.append(candidate)

    if not candidates:
        raise ValueError("no square symmetry and color renaming maps panel 1 to panel 2")
    if len(candidates) != 1:
        raise ValueError("visible analogy permits multiple different outputs")
    return candidates[0]
