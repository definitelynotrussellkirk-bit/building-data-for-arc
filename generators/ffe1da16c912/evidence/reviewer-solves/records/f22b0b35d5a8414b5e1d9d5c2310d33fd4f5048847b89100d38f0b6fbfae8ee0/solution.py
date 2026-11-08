from __future__ import annotations


def _crop(mask: list[list[int]]) -> list[list[int]]:
    points = [
        (r, c)
        for r, row in enumerate(mask)
        for c, value in enumerate(row)
        if value
    ]
    if not points:
        return []
    r0 = min(r for r, _ in points)
    r1 = max(r for r, _ in points)
    c0 = min(c for _, c in points)
    c1 = max(c for _, c in points)
    return [row[c0 : c1 + 1] for row in mask[r0 : r1 + 1]]


def _rotate(mask: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*mask[::-1])]


def _reflect(mask: list[list[int]]) -> list[list[int]]:
    return [row[::-1] for row in mask]


def _signature(mask: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    """Translation/rotation/reflection-invariant object signature."""
    current = _crop(mask)
    variants: list[tuple[tuple[int, ...], ...]] = []
    for _ in range(4):
        for candidate in (current, _reflect(current)):
            cropped = _crop(candidate)
            variants.append(tuple(tuple(row) for row in cropped))
        current = _rotate(current)
    return min(variants)


def solve(grid):
    # The input contains four monochrome objects separated by vertical 5-bars.
    separator_columns = [
        c for c in range(len(grid[0])) if all(row[c] == 5 for row in grid)
    ]
    cuts = [-1, *separator_columns, len(grid[0])]
    blocks = [
        [row[cuts[i] + 1 : cuts[i + 1]] for row in grid]
        for i in range(len(cuts) - 1)
        if cuts[i + 1] - cuts[i] > 1
    ]

    objects = []
    for block in blocks:
        colors = [value for row in block for value in row if value != 0]
        color = colors[0]
        mask = [[int(value != 0) for value in row] for row in block]
        objects.append((mask, color, _signature(mask)))

    # Exactly one pair is the same free polyomino. Preserve the left member's
    # orientation, crop it to its object bounds, and recolor it as the right one.
    for left in range(len(objects)):
        for right in range(left + 1, len(objects)):
            left_mask, _, left_signature = objects[left]
            _, right_color, right_signature = objects[right]
            if left_signature == right_signature:
                return [
                    [right_color if value else 0 for value in row]
                    for row in _crop(left_mask)
                ]

    raise ValueError("expected one congruent object pair")
