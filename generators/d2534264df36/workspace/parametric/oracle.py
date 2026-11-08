"""Independent Python semantics for the nested-ring cross-stop family."""
from __future__ import annotations

from copy import deepcopy

MODES = ("complete_only", "nearest_hit", "farthest_hit")


def _grid(value) -> list[list[int]]:
    if type(value) is not list or not value or type(value[0]) is not list or not value[0]:
        raise ValueError("expected a nonempty rectangular grid")
    width = len(value[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in value
    ):
        raise ValueError("expected exact integer colors in a rectangular grid")
    return deepcopy(value)


def complete_rings(grid) -> list[list[int]]:
    """Mirror the exact canonical row-major completion rule."""
    source = _grid(grid)
    height, width = len(source), len(source[0])
    out = deepcopy(source)
    cells = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if source[row][col] > 0
    ]
    for row, col in cells:
        color = source[row][col]
        ring = min(row, col, height - 1 - row, width - 1 - col)
        far = height - 1 - ring
        is_corner = row in (ring, far) and col in (ring, far)
        if is_corner:
            targets = ((ring, ring), (ring, far), (far, ring), (far, far))
        else:
            offsets = range(ring + 2, far - 1, 2)
            targets = (
                [(ring, offset) for offset in offsets]
                + [(far, offset) for offset in offsets]
                + [(offset, ring) for offset in offsets]
                + [(offset, far) for offset in offsets]
            )
        for target_row, target_col in targets:
            out[target_row][target_col] = color
    return out


def ray_intermediate(completed, mode: str) -> dict[str, int]:
    """Read the selected completed side on the north hub ray."""
    if mode not in ("nearest_hit", "farthest_hit"):
        raise ValueError("ray mode must be nearest_hit or farthest_hit")
    base = _grid(completed)
    height, width = len(base), len(base[0])
    if height != width:
        raise ValueError("cross composition requires a square grid")
    hub = height // 2
    hits = [row for row in range(hub) if base[row][hub] > 0]
    if not hits:
        raise ValueError("completed grid has no north-ray side hit")
    hit_row = max(hits) if mode == "nearest_hit" else min(hits)
    return {
        "hub": hub,
        "hit_row": hit_row,
        "hit_color": base[hit_row][hub],
        "far_row": height - 1 - hit_row,
        "hit_count": len(hits),
    }


def _fill_cross(base, mode: str) -> list[list[int]]:
    out = _grid(base)
    if mode == "complete_only":
        return out
    try:
        intermediate = ray_intermediate(out, mode)
    except ValueError as error:
        if str(error) == "completed grid has no north-ray side hit":
            return out
        raise
    hit = intermediate["hit_row"]
    far = intermediate["far_row"]
    hub = intermediate["hub"]
    color = intermediate["hit_color"]
    cells = (
        [(row, hub) for row in range(hit + 1, far)]
        + [(hub, col) for col in range(hit + 1, far)]
    )
    for row, col in cells:
        if out[row][col] == 0:
            out[row][col] = color
    return out


def solve(grid, mode: str) -> list[list[int]]:
    if mode not in MODES:
        raise ValueError(f"mode must be one of {MODES}")
    completed = complete_rings(grid)
    return _fill_cross(completed, mode)


def skip_a_solve(grid, mode: str) -> list[list[int]]:
    """Counterfactual B on the raw source, intentionally skipping completion A."""
    if mode not in ("nearest_hit", "farthest_hit"):
        raise ValueError("skip-A applies only to composed settings")
    return _fill_cross(grid, mode)
