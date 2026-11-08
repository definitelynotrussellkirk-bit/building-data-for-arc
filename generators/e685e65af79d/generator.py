"""Generator for e685e65af79d: rotational closure of each colored object.

For each 4-connected nonzero object with a square bounding box, overlay the
object's 0, 90, 180 and 270 degree rotations inside that box.

Version 3 repairs the retained half-turn teaching shortcut and inert controls:
every ordinary input includes a shape whose quarter-turn closure adds cells
beyond its half-turn closure, and the advertised shape override is now exact.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "e685e65af79d"
VERSION = "3.0.0"
TASK_ID = GENERATOR_ID
SUMMARY = (
    "A zero-background grid contains 2-4 separated, distinctly colored objects "
    "with asymmetric square bounding boxes. For each object, overlay its three "
    "clockwise quarter-turns inside its own bounding box. Every ordinary input "
    "contains a diagnostic object that rules out a 180-degree-only shortcut."
)
EXAMPLES_NEEDED = 3
INVARIANTS = [
    "2-4 non-touching objects with distinct colors",
    "every object has a square bounding box and is quarter-turn asymmetric",
    "at least one object needs a 90-degree copy beyond its half-turn closure",
]

DEGENERATE_TEXTURES = ("no_blobs", "symmetric_blob", "non_square_bbox")
HELPFUL_TEXTURES = ("varied", "diagnostic")
AXES = {
    "grid_h": {"type": "int", "default": "by difficulty", "valid": "10..18"},
    "grid_w": {"type": "int", "default": "by difficulty", "valid": "10..18"},
    "n_blobs": {"type": "int", "default": "by difficulty", "valid": "2..4"},
    "blob_shape_idx": {"type": "int", "default": "rng", "valid": "0..9"},
    "texture": {"type": "str", "default": "rng helpful", "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

# All shapes are connected, asymmetric and span a square bounding box.
_SHAPE_BANK = [
    [(0, 0), (0, 1), (1, 0)],
    [(0, 0), (0, 1), (0, 2), (1, 2), (2, 1), (2, 2)],
    [(0, 0), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2)],
    [(0, 0), (1, 0), (1, 1), (1, 2), (2, 2)],
    [(0, 0), (0, 1), (0, 2), (1, 0), (2, 0)],
    [(0, 0), (0, 1), (1, 1), (2, 1), (2, 2)],
    [(0, 0), (0, 1), (1, 0), (2, 0), (3, 0), (3, 1), (3, 2), (3, 3)],
    [(0, 3), (1, 2), (1, 3), (2, 0), (2, 1), (2, 2), (3, 2)],
    [(0, 0), (0, 1), (1, 1)],
    [(0, 0), (1, 0), (1, 1)],
]


def _shape_bbox(cells):
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return max(rows) - min(rows) + 1, max(cols) - min(cols) + 1


def _norm(cells):
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return sorted((r - r0, c - c0) for r, c in cells)


def _rot90(cells):
    normalized = _norm(cells)
    side = max(max(r for r, _ in normalized), max(c for _, c in normalized)) + 1
    return _norm([(c, side - 1 - r) for r, c in normalized])


def _half_turn_closure(cells):
    base = _norm(cells)
    r180 = _rot90(_rot90(base))
    return sorted(set(base) | set(r180))


def _rotation_closure(cells):
    base = _norm(cells)
    result = set()
    current = base
    for _ in range(4):
        result.update(current)
        current = _rot90(current)
    return sorted(result)


def _is_diagnostic(cells):
    return len(_rotation_closure(cells)) > len(_half_turn_closure(cells))


if len(_SHAPE_BANK) != 10 or any(_shape_bbox(shape)[0] != _shape_bbox(shape)[1] for shape in _SHAPE_BANK):
    raise RuntimeError("shape bank contract changed")
_ROTATION_DIAGNOSTIC_INDICES = tuple(i for i, shape in enumerate(_SHAPE_BANK) if _is_diagnostic(shape))
if not _ROTATION_DIAGNOSTIC_INDICES:
    raise RuntimeError("shape bank needs a half-turn counterexample")


def _try_place(grid, shape, color, rng, *, max_tries=250):
    height, width = len(grid), len(grid[0])
    shape_h, shape_w = _shape_bbox(shape)
    for _ in range(max_tries):
        top = rng.randint(0, height - shape_h)
        left = rng.randint(0, width - shape_w)
        if any(
            0 <= top + dr < height
            and 0 <= left + dc < width
            and grid[top + dr][left + dc] != 0
            for dr in range(-1, shape_h + 1)
            for dc in range(-1, shape_w + 1)
        ):
            continue
        for dr, dc in shape:
            grid[top + dr][left + dc] = color
        return True
    return False


def _build_grid(height, width, shapes, colors, rng):
    for _ in range(80):
        grid = full_grid(height, width, 0)
        if all(_try_place(grid, shape, color, rng) for shape, color in zip(shapes, colors)):
            return grid
    raise RuntimeError("failed to place all requested objects")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    texture = ctx.draw_choice("texture", list(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)) if overrides.get("texture") is not None else "varied"
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, None)

    if difficulty == "easy":
        h_lo, h_hi, w_lo, w_hi, n_lo, n_hi = 10, 12, 10, 12, 2, 2
    elif difficulty == "hard":
        h_lo, h_hi, w_lo, w_hi, n_lo, n_hi = 14, 18, 14, 18, 3, 4
    elif difficulty == "medium":
        h_lo, h_hi, w_lo, w_hi, n_lo, n_hi = 12, 16, 12, 16, 2, 4
    else:
        h_lo, h_hi, w_lo, w_hi, n_lo, n_hi = 11, 14, 11, 14, 2, 3
    height = ctx.draw_int_strict("grid_h", h_lo, h_hi)
    width = ctx.draw_int_strict("grid_w", w_lo, w_hi)
    count = ctx.draw_int_strict("n_blobs", n_lo, n_hi)
    rng = ctx.draw_rng("layout")

    forced = overrides.get("blob_shape_idx")
    if forced is not None:
        shape_index = ctx.draw_int_strict("blob_shape_idx", 0, len(_SHAPE_BANK) - 1)
        shapes = [_SHAPE_BANK[shape_index] for _ in range(count)]
    elif texture == "diagnostic":
        shapes = [rng.choice([_SHAPE_BANK[i] for i in _ROTATION_DIAGNOSTIC_INDICES]) for _ in range(count)]
    else:
        shapes = [rng.choice([_SHAPE_BANK[i] for i in _ROTATION_DIAGNOSTIC_INDICES])]
        shapes.extend(rng.choice(_SHAPE_BANK) for _ in range(count - 1))
    colors = rng.sample(list(range(1, 10)), count)
    return _build_grid(height, width, shapes, colors, rng)


def _draw_from_degenerate(name, rng):
    height = width = 12
    grid = full_grid(height, width, 0)
    if name == "no_blobs":
        return grid
    if name == "symmetric_blob":
        shape = [(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)]
        paint_at(grid, 1, 1, shape, 3)
        paint_at(grid, 7, 4, shape, 6)
        return grid
    if name == "non_square_bbox":
        paint_at(grid, 1, 1, [(0, 0), (0, 1), (0, 2), (0, 3), (1, 3)], 3)
        paint_at(grid, 7, 4, [(0, 0), (1, 0), (2, 0), (2, 1), (2, 2)], 6)
        return grid
    raise ValueError(f"unknown degenerate texture: {name!r}")


def _components(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(height):
        for c in range(width):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            color = grid[r][c]
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < height and 0 <= nc < width and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            rows = [rr for rr, _ in cells]
            cols = [cc for _, cc in cells]
            result.append((color, cells, (min(rows), min(cols), max(rows), max(cols))))
    return result


def self_check(grid, *, difficulty=None, meta=None):
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    errors = []
    components = _components(grid)
    lo, hi = (3, 4) if difficulty == "hard" else ((2, 2) if difficulty == "easy" else (2, 4) if difficulty == "medium" else (2, 3))
    if not lo <= len(components) <= hi:
        errors.append(f"expected {lo}..{hi} objects, got {len(components)}")
    colors = [color for color, _, _ in components]
    if len(colors) != len(set(colors)):
        errors.append("object colors are not distinct")
    diagnostic = False
    for _color, cells, bbox in components:
        r1, c1, r2, c2 = bbox
        if r2 - r1 != c2 - c1:
            errors.append("object bounding box is not square")
            continue
        if _norm(cells) == _rot90(cells):
            errors.append("object is quarter-turn symmetric")
        diagnostic = diagnostic or _is_diagnostic(cells)
    if components and not diagnostic:
        errors.append("no object refutes the half-turn-only shortcut")
    return errors
