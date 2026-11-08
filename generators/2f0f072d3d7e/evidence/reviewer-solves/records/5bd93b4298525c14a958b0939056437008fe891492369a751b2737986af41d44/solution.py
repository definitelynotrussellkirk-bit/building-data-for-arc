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
    r1 = max(r for r, _ in points) + 1
    c0 = min(c for _, c in points)
    c1 = max(c for _, c in points) + 1
    return [row[c0:c1] for row in mask[r0:r1]]


def _rotate_ccw(shape: list[list[int]]) -> list[list[int]]:
    if not shape:
        return []
    return [list(row) for row in zip(*shape)][::-1]


def _mirror_lr(shape: list[list[int]]) -> list[list[int]]:
    return [row[::-1] for row in shape]


def _transform(shape: list[list[int]], quarter_turns: int, mirror: bool) -> list[list[int]]:
    result = [row[:] for row in shape]
    for _ in range(quarter_turns % 4):
        result = _rotate_ccw(result)
    if mirror:
        result = _mirror_lr(result)
    return result


def _panel_mask(grid: list[list[int]], start_col: int) -> list[list[int]]:
    return [
        [1 if value != 0 else 0 for value in row[start_col : start_col + 4]]
        for row in grid
    ]


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Solve the visual analogy encoded by six 4x4 panels.

    Panel 0 -> panel 1 defines a rotation/reflection of a tightly cropped shape.
    Apply that same transform to panel 2, select the matching choice among panels
    3..5, and return that choice in its displayed position recolored azure (8).
    """
    starts = (0, 5, 10, 15, 20, 25)
    panels = [_panel_mask(grid, start) for start in starts]
    cropped = [_crop(panel) for panel in panels]

    valid_transforms: list[tuple[int, bool]] = []
    for quarter_turns in range(4):
        for mirror in (False, True):
            if _transform(cropped[0], quarter_turns, mirror) == cropped[1]:
                valid_transforms.append((quarter_turns, mirror))

    matching_choices: set[int] = set()
    for transform in valid_transforms:
        wanted = _transform(cropped[2], *transform)
        for choice in range(3, 6):
            if cropped[choice] == wanted:
                matching_choices.add(choice)

    if len(matching_choices) != 1:
        raise ValueError(
            f"expected one transformed choice, found {sorted(matching_choices)} "
            f"from transforms {valid_transforms}"
        )

    chosen = panels[matching_choices.pop()]
    return [[8 if value else 0 for value in row] for row in chosen]
