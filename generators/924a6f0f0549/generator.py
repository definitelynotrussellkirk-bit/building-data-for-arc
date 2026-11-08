"""Native generator for ARC task ``924a6f0f0549``.

The first row contains ``k`` color-1 markers.  In the body, exactly one
4-connected monochrome object has area ``k``.  The canonical rule selects that
object, keeps its outline cells, and crops the result to the selected object's
bounding box.

The public axes below are deliberately small and honest: every accepted value
is consumed, observable from the produced grid, and legal in every difficulty
band.  Difficulty only changes the default distribution; it never narrows the
public override contract.
"""
from __future__ import annotations

from collections.abc import Iterable
from math import ceil, sqrt

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "924a6f0f0549"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "23fd1d61a026"
SUMMARY = (
    "Row 0 has k color-1 markers. Below it are distinctly sized, distinctly "
    "colored body objects; exactly one has area k. Select that object, keep "
    "its 4-neighbor outline, and crop to its bounding box."
)

INVARIANTS = [
    "row 0 contains exactly target_size color-1 markers and otherwise background",
    "the body contains n_objects monochrome 4-connected components",
    "body component areas are pairwise distinct",
    "exactly one body component area equals target_size",
]

AXES = {
    "grid_h": {"type": "int", "default": "keyed draw", "valid": "10..30"},
    "grid_w": {"type": "int", "default": "keyed draw", "valid": "12..30"},
    "target_size": {"type": "int", "default": "keyed draw", "valid": "3..12"},
    "n_objects": {"type": "int", "default": "keyed draw", "valid": "3..5"},
}

_BODY_COLORS = (2, 3, 4, 5, 6, 7, 8, 9)
_DIRS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_DIFFICULTIES = (None, "easy", "medium", "hard")


def _validate_call(difficulty, overrides: dict) -> None:
    if difficulty not in _DIFFICULTIES:
        raise ValueError("difficulty must be one of None, easy, medium, hard")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")


def _paint(grid: list[list[int]], top: int, left: int,
           cells: Iterable[tuple[int, int]], color: int) -> None:
    for row, col in cells:
        grid[top + row][left + col] = color


def _compact_poly(rng, size: int) -> list[tuple[int, int]]:
    """Return a connected, compact polyomino of exactly ``size`` cells."""
    max_width = min(size, max(2, ceil(sqrt(size)) + 1))
    min_width = min(2, max_width)
    width = rng.randint(min_width, max_width)
    order: list[tuple[int, int]] = []
    for row in range(ceil(size / width)):
        columns = range(width) if row % 2 == 0 else range(width - 1, -1, -1)
        order.extend((row, col) for col in columns)
    cells = order[:size]

    # Dihedral transforms retain connectivity while adding deterministic variety.
    transform = rng.randrange(8)
    transformed: list[tuple[int, int]] = []
    for row, col in cells:
        if transform & 1:
            row, col = col, row
        if transform & 2:
            row = -row
        if transform & 4:
            col = -col
        transformed.append((row, col))
    min_row = min(row for row, _ in transformed)
    min_col = min(col for _, col in transformed)
    return sorted((row - min_row, col - min_col) for row, col in transformed)


def _shape_size(cells: list[tuple[int, int]]) -> tuple[int, int]:
    return (max(row for row, _ in cells) + 1,
            max(col for _, col in cells) + 1)


def _free(grid: list[list[int]], top: int, left: int,
          shape_h: int, shape_w: int) -> bool:
    """Reserve one background cell between body-object bounding boxes."""
    h, w = len(grid), len(grid[0])
    if top < 1 or left < 0 or top + shape_h > h or left + shape_w > w:
        return False
    for row in range(max(1, top - 1), min(h, top + shape_h + 1)):
        for col in range(max(0, left - 1), min(w, left + shape_w + 1)):
            if grid[row][col] != 0:
                return False
    return True


def _fallback_row_layout(h: int, w: int, sizes: list[int],
                         colors: list[int]) -> list[list[int]]:
    """Guaranteed legal layout for the minimum 10x12 / five-object case."""
    grid = full_grid(h, w, 0)
    rows = [1 + 2 * index for index in range(len(sizes))]
    if rows[-1] >= h or max(sizes) > w:
        raise ValueError("requested axes cannot fit the guaranteed row layout")
    for index, (row, size, color) in enumerate(zip(rows, sizes, colors)):
        slack = w - size
        left = 0 if slack == 0 else (index * 3) % (slack + 1)
        for col in range(left, left + size):
            grid[row][col] = color
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Generate one deterministic, fresh puzzle input grid."""
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h = ctx.draw_int_strict("grid_h", 10, 30)
    w = ctx.draw_int_strict("grid_w", 12, 30)
    target_size = ctx.draw_int_strict("target_size", 3, 12)
    n_objects = ctx.draw_int_strict("n_objects", 3, 5)

    size_rng = ctx.draw_rng("object_sizes")
    alternatives = [size for size in range(3, 13) if size != target_size]
    sizes = [target_size, *size_rng.sample(alternatives, n_objects - 1)]
    size_rng.shuffle(sizes)

    palette_rng = ctx.draw_rng("body_palette")
    colors = palette_rng.sample(list(_BODY_COLORS), n_objects)
    layout_rng = ctx.draw_rng("layout")

    grid: list[list[int]] | None = None
    for _attempt in range(80):
        candidate = full_grid(h, w, 0)
        placed_all = True
        for size, color in zip(sizes, colors):
            shape = _compact_poly(layout_rng, size)
            shape_h, shape_w = _shape_size(shape)
            if shape_h > h - 1 or shape_w > w:
                placed_all = False
                break
            positions = [
                (row, col)
                for row in range(1, h - shape_h + 1)
                for col in range(0, w - shape_w + 1)
            ]
            layout_rng.shuffle(positions)
            position = next(
                ((row, col) for row, col in positions
                 if _free(candidate, row, col, shape_h, shape_w)),
                None,
            )
            if position is None:
                placed_all = False
                break
            _paint(candidate, position[0], position[1], shape, color)
        if placed_all:
            grid = candidate
            break

    if grid is None:
        grid = _fallback_row_layout(h, w, sizes, colors)

    marker_rng = ctx.draw_rng("markers")
    for col in marker_rng.sample(range(w), target_size):
        grid[0][col] = 1

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise AssertionError("generated invalid grid: " + "; ".join(errors))
    return [list(row) for row in grid]


def _components(grid: list[list[int]], *, start_row: int = 0):
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[tuple[int, list[tuple[int, int]]]] = []
    for row in range(start_row, h):
        for col in range(w):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while stack:
                current = stack.pop()
                cells.append(current)
                for drow, dcol in _DIRS4:
                    nxt = (current[0] + drow, current[1] + dcol)
                    if (start_row <= nxt[0] < h and 0 <= nxt[1] < w
                            and nxt not in seen and grid[nxt[0]][nxt[1]] == color):
                        seen.add(nxt)
                        stack.append(nxt)
            result.append((color, cells))
    return result


def _validate_grid(grid) -> list[str]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        return ["grid must be a non-empty 2D list"]
    h, w = len(grid), len(grid[0])
    if not 1 <= h <= 30 or not 1 <= w <= 30:
        return ["grid dimensions must be within 1..30"]
    if any(type(row) is not list or len(row) != w for row in grid):
        return ["grid must be rectangular"]
    if any(type(value) is not int or not 0 <= value <= 9
           for row in grid for value in row):
        return ["grid cells must be exact integer colors 0..9"]
    return []


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the marker-count selection contract."""
    errors = _validate_grid(grid)
    if errors:
        return errors
    if difficulty not in _DIFFICULTIES:
        return ["difficulty must be one of None, easy, medium, hard"]

    marker_count = sum(value == 1 for value in grid[0])
    if not 3 <= marker_count <= 12:
        errors.append("row 0 must contain 3..12 color-1 markers")
    if any(value not in (0, 1) for value in grid[0]):
        errors.append("row 0 must contain only marker color 1 and background")

    components = _components(grid, start_row=1)
    sizes = [len(cells) for _, cells in components]
    colors = [color for color, _ in components]
    if not 3 <= len(components) <= 5:
        errors.append(f"expected 3..5 body objects, got {len(components)}")
    if len(sizes) != len(set(sizes)):
        errors.append("body component sizes must be distinct")
    if sizes.count(marker_count) != 1:
        errors.append(
            f"exactly one body component size must equal marker count "
            f"{marker_count}; sizes={sizes}"
        )
    if any(color in (0, 1) for color in colors):
        errors.append("body object colors must exclude background and marker color")
    if len(colors) != len(set(colors)):
        errors.append("body object colors must be distinct")
    return errors


def observe_overrides(grid) -> dict[str, int]:
    """Recover every public axis from a valid generated grid."""
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe invalid grid: " + "; ".join(errors))
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "target_size": sum(value == 1 for value in grid[0]),
        "n_objects": len(_components(grid, start_row=1)),
    }


def rule_mirror(grid, *, render_mode: str = "outline") -> list[list[int]]:
    """Pure Python mirror of the canonical rule plus its reviewed variant."""
    errors = _validate_grid(grid)
    if errors:
        raise ValueError("invalid grid: " + "; ".join(errors))
    if render_mode not in ("outline", "silhouette"):
        raise ValueError("render_mode must be outline or silhouette")

    marker_count = sum(value == 1 for value in grid[0])
    matches = [item for item in _components(grid, start_row=1)
               if len(item[1]) == marker_count]
    if len(matches) != 1:
        raise ValueError("expected exactly one body object matching marker count")
    color, cells = matches[0]
    selected = set(cells)
    if render_mode == "outline":
        rendered = {
            cell for cell in selected
            if any((cell[0] + drow, cell[1] + dcol) not in selected
                   for drow, dcol in _DIRS4)
        }
    else:
        rendered = selected

    min_row = min(row for row, _ in rendered)
    max_row = max(row for row, _ in rendered)
    min_col = min(col for _, col in rendered)
    max_col = max(col for _, col in rendered)
    output = full_grid(max_row - min_row + 1, max_col - min_col + 1, 0)
    for row, col in rendered:
        output[row - min_row][col - min_col] = color
    return output
