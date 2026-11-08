"""Generator for normalized intersection of the largest red and green shapes.

The selected Racket rule chooses the largest 4-connected color-2 component and
the largest 4-connected color-3 component, normalizes both to their bounding-box
origins, intersects the normalized cell sets, and paints the result color 8.

Normal examples therefore contain one unique largest component of each source
color plus smaller disconnected distractors.  This prevents the shortcut
"normalize every cell of the color" from fitting the generated domain.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "729429f8ea2c"
VERSION = "4.1.0"
TASK_ID = "729429f8ea2c"

SUMMARY = (
    "A 0-background grid contains a unique largest color-2 shape and a unique "
    "largest color-3 shape, plus 1-3 smaller disconnected distractors of each "
    "color. Normalize only the two largest components to their bounding-box "
    "origins, intersect their occupied cells, and paint the cropped result "
    "color 8. Grid size, shape density, distractor count, shapes, and placements "
    "vary while preserving a nonempty normalized intersection."
)

INVARIANTS = [
    "colors are limited to background 0 and source colors 2 and 3",
    "each source color has one unique largest 4-connected component",
    "all same-color distractors are strictly smaller and disconnected",
    "the normalized largest components have a nonempty intersection",
    "ordinary examples refute the normalize-all-cells shortcut",
]

SHAPE_TEXTURES = ("sparse", "balanced", "dense")
DEGENERATE_TEXTURES = ("no_shapes", "no_intersection", "full_grid")
HELPFUL_TEXTURES = SHAPE_TEXTURES

AXES = {
    "grid_h": {"type": "int", "default": "difficulty-dependent", "valid": "8..20"},
    "grid_w": {"type": "int", "default": "difficulty-dependent", "valid": "10..20"},
    "distractor_count": {"type": "int", "default": "rng 1..3", "valid": "1..3"},
    "texture": {
        "type": "str",
        "default": "rng sparse|balanced|dense",
        "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES),
    },
}

_DIRS4 = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _exact_int(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _validate_overrides(overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override axis/axes: " + ", ".join(unknown))
    if "grid_h" in overrides:
        _exact_int(overrides["grid_h"], 8, 20, "grid_h")
    if "grid_w" in overrides:
        _exact_int(overrides["grid_w"], 10, 20, "grid_w")
    if "distractor_count" in overrides:
        _exact_int(overrides["distractor_count"], 1, 3, "distractor_count")
    if "texture" in overrides:
        value = overrides["texture"]
        if type(value) is not str or value not in HELPFUL_TEXTURES + DEGENERATE_TEXTURES:
            raise ValueError("texture must be a declared helpful or degenerate texture")
        if value in DEGENERATE_TEXTURES and "distractor_count" in overrides:
            raise ValueError("distractor_count cannot be combined with a degenerate texture")


def _norm(cells):
    top = min(r for r, _ in cells)
    left = min(c for _, c in cells)
    return [(r - top, c - left) for r, c in cells]


def _norm_set(cells):
    return set(map(tuple, _norm(cells)))


def _connected_polyomino(rng, size, max_h, max_w):
    """Return a normalized connected polyomino with exactly ``size`` cells."""
    for _ in range(160):
        cells = {(0, 0)}
        for _step in range(size * 80):
            if len(cells) == size:
                break
            row, col = rng.choice(tuple(cells))
            dr, dc = rng.choice(_DIRS4)
            cells.add((row + dr, col + dc))
        normalized = set(_norm(cells))
        if (len(normalized) == size
                and max(r for r, _ in normalized) < max_h
                and max(c for _, c in normalized) < max_w):
            return sorted(normalized)
    raise ValueError("could not construct a bounded connected polyomino")


def _components(grid, color):
    height, width = len(grid), len(grid[0])
    seen = set()
    result = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] != color or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            component = []
            while stack:
                rr, cc = stack.pop()
                component.append((rr, cc))
                for dr, dc in _DIRS4:
                    nxt = (rr + dr, cc + dc)
                    if (0 <= nxt[0] < height and 0 <= nxt[1] < width
                            and nxt not in seen and grid[nxt[0]][nxt[1]] == color):
                        seen.add(nxt)
                        stack.append(nxt)
            result.append(component)
    return result


def _placement_is_free(occupied, cells, top, left, height, width):
    """Require a one-cell moat around every separately placed component."""
    for row, col in cells:
        rr, cc = top + row, left + col
        if not (0 <= rr < height and 0 <= cc < width):
            return False
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                nr, nc = rr + dr, cc + dc
                if 0 <= nr < height and 0 <= nc < width and occupied[nr][nc]:
                    return False
    return True


def _place_component(grid, occupied, cells, color, rng):
    height, width = len(grid), len(grid[0])
    box_h = max(r for r, _ in cells) + 1
    box_w = max(c for _, c in cells) + 1
    candidates = [(top, left)
                  for top in range(height - box_h + 1)
                  for left in range(width - box_w + 1)]
    rng.shuffle(candidates)
    for top, left in candidates:
        if not _placement_is_free(occupied, cells, top, left, height, width):
            continue
        for row, col in cells:
            rr, cc = top + row, left + col
            grid[rr][cc] = color
            occupied[rr][cc] = True
        return True
    return False


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the ordinary domain and its largest-component teaching signal."""
    if not grid or not grid[0]:
        return ["empty grid"]
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        return ["ragged grid"]
    if any(type(cell) is not int or not 0 <= cell <= 9 for row in grid for cell in row):
        return ["grid cells must be exact integer colors 0..9"]
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []

    errors = []
    largest = {}
    for color in (2, 3):
        components = _components(grid, color)
        if len(components) < 2:
            errors.append(f"expected a largest color-{color} component plus distractors")
            continue
        ordered = sorted(components, key=len, reverse=True)
        if len(ordered[0]) == len(ordered[1]):
            errors.append(f"expected a unique largest color-{color} component")
            continue
        largest[color] = ordered[0]
    if 2 in largest and 3 in largest:
        intended = _norm_set(largest[2]) & _norm_set(largest[3])
        if not intended:
            errors.append("normalized largest color-2 and color-3 shapes do not intersect")
        else:
            all_twos = [(row, col) for row, values in enumerate(grid)
                        for col, value in enumerate(values) if value == 2]
            all_threes = [(row, col) for row, values in enumerate(grid)
                          for col, value in enumerate(values) if value == 3]
            shortcut = _norm_set(all_twos) & _norm_set(all_threes)
            if shortcut == intended:
                errors.append("normalize-all-cells shortcut matches the largest-component result")
    extras = sorted({value for row in grid for value in row if value not in (0, 2, 3)})
    if extras:
        errors.append(f"unexpected colors in normal example: {extras}")
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    texture_override = overrides.get("texture")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    rng = ctx.draw_rng("layout")

    if difficulty == "easy":
        h_range, w_range = (8, 11), (10, 13)
    elif difficulty == "hard":
        h_range, w_range = (15, 20), (15, 20)
    else:
        h_range, w_range = (11, 16), (12, 18)
    height = ctx.draw_int("grid_h", *(8, 20) if "grid_h" in overrides else h_range)
    width = ctx.draw_int("grid_w", *(10, 20) if "grid_w" in overrides else w_range)
    if texture_override in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture_override, height, width)
    distractors = ctx.draw_int("distractor_count", 1, 3)
    texture = texture_override or rng.choice(HELPFUL_TEXTURES)

    size_ranges = {
        "sparse": (4, 6),
        "balanced": (6, 9),
        "dense": (8, 12),
    }
    low, high = size_ranges[texture]
    max_box_h = max(3, min(6, height - 2))
    max_box_w = max(3, min(6, width - 2))
    capacity = max_box_h * max_box_w
    high = min(high, capacity)
    low = min(low, high)

    for _attempt in range(240):
        shape2 = _connected_polyomino(rng, rng.randint(low, high), max_box_h, max_box_w)
        shape3 = _connected_polyomino(rng, rng.randint(low, high), max_box_h, max_box_w)
        if not (_norm_set(shape2) & _norm_set(shape3)):
            continue

        grid = full_grid(height, width, 0)
        occupied = [[False] * width for _ in range(height)]
        if not _place_component(grid, occupied, shape2, 2, rng):
            continue
        if not _place_component(grid, occupied, shape3, 3, rng):
            continue
        placed = True
        for color in (2, 3):
            for _ in range(distractors):
                if not _place_component(grid, occupied, [(0, 0)], color, rng):
                    placed = False
                    break
            if not placed:
                break
        if placed and not self_check(grid, difficulty=difficulty):
            return grid

    raise ValueError("could not place largest shapes and disconnected distractors")


def _draw_from_degenerate(name, height, width):
    grid = full_grid(height, width, 0)
    if name == "no_shapes":
        return grid
    if name == "no_intersection":
        paint_at(grid, 1, 1, [(0, 0)], 2)
        paint_at(grid, 5, 7, [(0, 1), (1, 0), (1, 1)], 3)
        return grid
    if name == "full_grid":
        for row in range(height):
            for col in range(width):
                grid[row][col] = 2
        return grid
    return grid
