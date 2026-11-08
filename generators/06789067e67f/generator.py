"""Generator for H70: sort component crops by holes, area, then color.

Each nonzero 4-connected component is cropped to its bounding box.  Components
are sorted by ``(hole_count descending, area descending, color ascending)`` and
packed left-to-right, top-aligned, with one blank column between crops.

The declared axes are strict and total over their advertised ranges.  Earlier
versions exposed a ``single_component`` texture even though ``self_check``
rejected it, silently accepted unknown textures, and made valid size endpoints
unreachable under difficulty-specific draw bounds.  Version 3 removes that
contradictory texture and validates every override before generation.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "06789067e67f"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "82b12cea1db8"

SUMMARY = (
    "2-4 isolated components sorted by (hole_count desc, area desc, color asc) "
    "and packed left-to-right, top-aligned, with one blank column between crops. "
    "Tie textures force the area and color tie-breaks to matter."
)

EXAMPLES_NEEDED = 4
INVARIANTS = [
    "background is 0",
    "2-4 isolated monochrome 4-connected components",
    "the (holes, area, color) sort keys are pairwise distinct",
]

TEXTURES = ("plain", "tie_holes", "tie_area", "all_solid")
AXES = {
    "grid_h": {"type": "int", "default": "difficulty-skewed 10..18", "valid": "10..18"},
    "grid_w": {"type": "int", "default": "difficulty-skewed 12..22", "valid": "12..22"},
    "n_comps": {"type": "int", "default": "difficulty-skewed 2..4", "valid": "2..4"},
    "texture": {
        "type": "str",
        "default": "rng over plain|tie_holes|tie_area|all_solid",
        "valid": "plain|tie_holes|tie_area|all_solid",
        "doc": "tie_holes makes area decide; tie_area makes color decide",
    },
}
_VALID_DIFFICULTIES = (None, "easy", "medium", "hard")


class Shape:
    __slots__ = ("cells", "height", "width")

    def __init__(self, cells: tuple[tuple[int, int], ...], height: int, width: int):
        self.cells = cells
        self.height = height
        self.width = width


def _shape_from_rows(*rows: str) -> Shape:
    width = len(rows[0])
    if not rows or any(len(row) != width for row in rows):
        raise ValueError("shape rows must be nonempty and rectangular")
    cells = tuple((r, c) for r, row in enumerate(rows) for c, value in enumerate(row) if value == "1")
    return Shape(cells, len(rows), width)


SOLID_2X2 = _shape_from_rows("11", "11")
SOLID_2X3 = _shape_from_rows("111", "111")
SOLID_3X2 = _shape_from_rows("11", "11", "11")
SOLID_3X3 = _shape_from_rows("111", "111", "111")
RING_3X3 = _shape_from_rows("111", "101", "111")
RING_3X4 = _shape_from_rows("1111", "1001", "1111")
DOUBLE_RING_3X5 = _shape_from_rows("11111", "10101", "11111")
C_3X3 = _shape_from_rows("111", "100", "111")
C_4X3 = _shape_from_rows("111", "100", "100", "111")


def _strict_int(overrides: dict, name: str, lo: int, hi: int) -> None:
    if name not in overrides or overrides[name] is None:
        return
    value = overrides[name]
    if type(value) is not int:
        raise TypeError(f"{name} must be an exact integer (not bool)")
    if not lo <= value <= hi:
        raise ValueError(f"{name} must be in {lo}..{hi}")


def _validate_request(difficulty, overrides: dict) -> None:
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be one of None, easy, medium, hard")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    _strict_int(overrides, "grid_h", 10, 18)
    _strict_int(overrides, "grid_w", 12, 22)
    _strict_int(overrides, "n_comps", 2, 4)
    if "texture" in overrides and overrides["texture"] is not None:
        value = overrides["texture"]
        if type(value) is not str:
            raise TypeError("texture must be a string")
        if value not in TEXTURES:
            raise ValueError(f"texture must be one of {TEXTURES}")


def _hole_count(shape: Shape) -> int:
    body = set(shape.cells)
    seen: set[tuple[int, int]] = set()
    holes = 0
    for r in range(shape.height):
        for c in range(shape.width):
            if (r, c) in body or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            touches = False
            while stack:
                rr, cc = stack.pop()
                if rr in (0, shape.height - 1) or cc in (0, shape.width - 1):
                    touches = True
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < shape.height and 0 <= nc < shape.width
                            and (nr, nc) not in body and (nr, nc) not in seen):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            if not touches:
                holes += 1
    return holes


def _shape_plan(texture: str, n: int, rng) -> list[Shape]:
    if texture == "plain":
        pool = [DOUBLE_RING_3X5, RING_3X3, C_3X3, SOLID_2X3]
        # Rotate the zero-hole alternatives without changing the essential
        # 2-hole > 1-hole > 0-hole teaching structure.
        if rng.randrange(2):
            pool[2], pool[3] = C_4X3, SOLID_2X2
        return pool[:n]
    if texture == "tie_holes":
        # Equal one-hole counts, unequal areas: area descending must decide.
        return [RING_3X3, RING_3X4, DOUBLE_RING_3X5, C_3X3][:n]
    if texture == "tie_area":
        # Identical geometry with distinct colors: color ascending must decide.
        return [RING_3X3, RING_3X3, DOUBLE_RING_3X5, C_3X3][:n]
    if texture == "all_solid":
        # All primary keys tie; area and then color remain observable.
        return [SOLID_2X2, SOLID_2X3, SOLID_3X2, SOLID_3X3][:n]
    raise AssertionError(texture)


def _rects_separated(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> bool:
    ar0, ac0, ar1, ac1 = a
    br0, bc0, br1, bc1 = b
    return ar1 + 1 < br0 or br1 + 1 < ar0 or ac1 + 1 < bc0 or bc1 + 1 < ac0


def _place_shapes(h: int, w: int, shapes: list[Shape], colors: list[int], rng) -> list[list[int]]:
    # Place largest boxes first and use complete bounded backtracking.  This makes
    # every advertised corner (including 10x12 with four components) reliable.
    order = sorted(range(len(shapes)), key=lambda i: shapes[i].height * shapes[i].width, reverse=True)
    placed: dict[int, tuple[int, int]] = {}
    rects: list[tuple[int, int, int, int]] = []

    def search(depth: int) -> bool:
        if depth == len(order):
            return True
        index = order[depth]
        shape = shapes[index]
        candidates = [
            (r, c)
            for r in range(h - shape.height + 1)
            for c in range(w - shape.width + 1)
        ]
        rng.shuffle(candidates)
        for r, c in candidates:
            rect = (r, c, r + shape.height - 1, c + shape.width - 1)
            if any(not _rects_separated(rect, other) for other in rects):
                continue
            placed[index] = (r, c)
            rects.append(rect)
            if search(depth + 1):
                return True
            rects.pop()
            del placed[index]
        return False

    if not search(0):
        raise ValueError(f"could not place {len(shapes)} components in {h}x{w}")
    grid = full_grid(h, w, 0)
    for index, shape in enumerate(shapes):
        r0, c0 = placed[index]
        color = colors[index]
        for dr, dc in shape.cells:
            grid[r0 + dr][c0 + dc] = color
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_request(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h = ctx.draw_int_diff("grid_h", 10, 18)
    w = ctx.draw_int_diff("grid_w", 12, 22)
    n = ctx.draw_int_diff("n_comps", 2, 4)
    texture = ctx.draw_choice("texture", TEXTURES)
    rng = ctx.draw_rng("layout")
    colors = list(ctx.draw_distinct_colors("component_colors", n=n, exclude={0}))
    shapes = _shape_plan(texture, n, rng)
    # Ensure full sort triples are unique.  Distinct colors make a full tie
    # impossible even for identical shapes, but keep the invariant explicit.
    keys = [(_hole_count(shape), len(shape.cells), color) for shape, color in zip(shapes, colors, strict=True)]
    if len(set(keys)) != len(keys):
        raise AssertionError(f"duplicate sort keys: {keys}")
    return _place_shapes(h, w, shapes, colors, rng)


def _grid_error(grid) -> str | None:
    if type(grid) is not list or not grid:
        return "grid must be a nonempty list"
    if type(grid[0]) is not list or not grid[0]:
        return "grid rows must be nonempty lists"
    width = len(grid[0])
    if not 1 <= len(grid) <= 30 or not 1 <= width <= 30:
        return "grid dimensions must be in 1..30"
    for row in grid:
        if type(row) is not list or len(row) != width:
            return "grid must be rectangular"
        for value in row:
            if type(value) is not int or not 0 <= value <= 9:
                return "grid cells must be exact integer ARC colors 0..9"
    return None


def _components(grid: list[list[int]]) -> list[tuple[int, list[tuple[int, int]]]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components = []
    for r0 in range(h):
        for c0 in range(w):
            if grid[r0][c0] == 0 or (r0, c0) in seen:
                continue
            color = grid[r0][c0]
            stack = [(r0, c0)]
            seen.add((r0, c0))
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            components.append((color, cells))
    return components


def _component_key(component: tuple[int, list[tuple[int, int]]]) -> tuple[int, int, int]:
    color, cells = component
    r0 = min(r for r, _ in cells)
    r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    c1 = max(c for _, c in cells)
    local = {(r - r0, c - c0) for r, c in cells}
    shape = Shape(tuple(sorted(local)), r1 - r0 + 1, c1 - c0 + 1)
    return _hole_count(shape), len(cells), color


def self_check(grid, *, difficulty=None, meta=None):
    error = _grid_error(grid)
    if error:
        return [error]
    components = _components(grid)
    if not 2 <= len(components) <= 4:
        return [f"expected 2-4 components, got {len(components)}"]
    keys = [_component_key(component) for component in components]
    if len(set(keys)) != len(keys):
        return [f"(holes, area, color) keys not pairwise distinct: {keys}"]
    return []
