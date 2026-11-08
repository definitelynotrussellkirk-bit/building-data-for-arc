from collections import Counter


def _transform(grid, kind):
    """Apply one of the eight symmetries of a square grid."""
    n = len(grid)
    out = [[0 for _ in range(n)] for _ in range(n)]

    for r in range(n):
        for c in range(n):
            if kind == "identity":
                rr, cc = r, c
            elif kind == "rot90":
                rr, cc = c, n - 1 - r
            elif kind == "rot180":
                rr, cc = n - 1 - r, n - 1 - c
            elif kind == "rot270":
                rr, cc = n - 1 - c, r
            elif kind == "reflect_lr":
                rr, cc = r, n - 1 - c
            elif kind == "reflect_tb":
                rr, cc = n - 1 - r, c
            elif kind == "transpose":
                rr, cc = c, r
            elif kind == "reflect_anti_diagonal":
                rr, cc = n - 1 - c, n - 1 - r
            else:  # pragma: no cover - internal invariant
                raise ValueError(f"unknown transform: {kind}")
            out[rr][cc] = grid[r][c]
    return out


def _split_panels(grid):
    if not grid or not grid[0]:
        raise ValueError("grid must be non-empty")
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if (width - 2) % 3 != 0:
        raise ValueError("expected three equal panels separated by two columns")

    panel_width = (width - 2) // 3
    sep1 = panel_width
    sep2 = 2 * panel_width + 1
    if panel_width != len(grid):
        raise ValueError("expected square panels")

    first_separator = {row[sep1] for row in grid}
    second_separator = {row[sep2] for row in grid}
    if len(first_separator) != 1 or first_separator != second_separator:
        raise ValueError("separator columns are not uniform and matching")

    panels = []
    for start in (0, sep1 + 1, sep2 + 1):
        panels.append([row[start : start + panel_width] for row in grid])
    return panels


def solve(grid):
    """Infer the panel-1-to-panel-2 symmetry and apply it to panel 3."""
    first, second, target = _split_panels(grid)
    kinds = (
        "identity",
        "rot90",
        "rot180",
        "rot270",
        "reflect_lr",
        "reflect_tb",
        "transpose",
        "reflect_anti_diagonal",
    )
    matches = [kind for kind in kinds if _transform(first, kind) == second]
    if not matches:
        raise ValueError("no square-grid symmetry maps the first panel to the second")

    candidates = [_transform(target, kind) for kind in matches]
    if any(candidate != candidates[0] for candidate in candidates[1:]):
        raise ValueError("the examples leave the target transformation ambiguous")
    return candidates[0]
