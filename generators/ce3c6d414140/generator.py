"""Canonical-profile sampler for ``ce3c6d414140``.

Each monochrome 8-connected object is a hollow right-slanting parallelogram.
The selected Racket authority keeps cells on that object's bounding-box bottom
row or rightmost column and shifts every other object cell one column right.
Outputs remain Racket-authoritative; :func:`rule_mirror` is an independent,
task-local audit oracle used by focused tests and semantic competitors.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "ce3c6d414140"
TASK_ID = GENERATOR_ID
RULE_HASH = "e5b989176419"
VERSION = "3.0.0"
EXAMPLES_NEEDED = 3
SUMMARY = (
    "A canonical-size zero-background grid contains one or two isolated, "
    "monochrome, hollow right-slanting parallelograms. For each object, keep "
    "the cells on its bounding-box bottom row or rightmost column fixed; shift "
    "every other object cell one column right."
)

INVARIANTS = [
    "profile is one of the three labeled canonical (shape, object-count) profiles",
    "each object is a monochrome hollow right-slanting parallelogram",
    "two-object lessons use distinct colors and at least one blank row of separation",
    "every ordinary input changes under the selected rule",
]

# These are the three labeled canonical canvas/object-count profiles.  Object
# geometry, position, and colors still vary independently inside each profile.
PROFILE_SPECS = {
    "small_one": (8, 9, 1),
    "square_one": (10, 10, 1),
    "tall_two": (14, 9, 2),
}
PROFILE_ORDER = tuple(PROFILE_SPECS)
AXES = {
    "profile": {
        "type": "str",
        "default": "deterministic three-profile rotation",
        "valid": "small_one|square_one|tall_two",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

_DIRS8 = tuple(
    (dr, dc)
    for dr in (-1, 0, 1)
    for dc in (-1, 0, 1)
    if (dr, dc) != (0, 0)
)
_BAND_OFFSET = {None: 0, "easy": 0, "medium": 1, "hard": 2}


def _validate_request(seed, sample_index, difficulty, overrides):
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int or sample_index < 0:
        raise TypeError("sample_index must be a non-negative integer (not bool)")
    if difficulty not in _BAND_OFFSET:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    profile = overrides.get("profile")
    if profile is not None and type(profile) is not str:
        raise TypeError("profile override must be a string")


def _parallelogram(height: int, top_width: int) -> set[tuple[int, int]]:
    """Normalized outline used by the canonical examples and generator."""
    if type(height) is not int or type(top_width) is not int:
        raise TypeError("parallelogram dimensions must be integers")
    if height < 3 or top_width < 3:
        raise ValueError("parallelogram dimensions must both be at least 3")
    cells = {(0, c) for c in range(top_width)}
    cells.update((height - 1, c) for c in range(height - 2, height - 2 + top_width))
    cells.update((r, r - 1) for r in range(1, height - 1))
    cells.update((r, top_width + r - 1) for r in range(1, height - 1))
    return cells


def _shape_options(max_height: int, canvas_width: int):
    options = []
    for height in range(3, min(6, max_height) + 1):
        max_top_width = min(6, canvas_width - height + 2)
        for top_width in range(3, max_top_width + 1):
            options.append((height, top_width))
    if not options:
        raise ValueError("canvas cannot fit a lawful parallelogram")
    return options


def _place(grid, cells, top, left, color):
    for r, c in cells:
        rr, cc = top + r, left + c
        if grid[rr][cc] != 0:
            raise RuntimeError("constructive placement collision")
        grid[rr][cc] = color


def _draw_one(ctx, grid, color):
    height, width = len(grid), len(grid[0])
    rng = ctx.draw_rng("object_0_geometry")
    oh, ow = rng.choice(_shape_options(height, width))
    bbox_width = oh + ow - 2
    top = rng.randint(0, height - oh)
    left = rng.randint(0, width - bbox_width)
    _place(grid, _parallelogram(oh, ow), top, left, color)


def _draw_two(ctx, grid, colors):
    """Construct two shapes with a full blank row between their bboxes."""
    height, width = len(grid), len(grid[0])
    rng = ctx.draw_rng("two_object_geometry")
    choices = []
    for first in _shape_options(height - 4, width):
        for second in _shape_options(height - first[0] - 1, width):
            if first[0] + second[0] + 1 <= height:
                choices.append((first, second))
    if not choices:
        raise ValueError("profile cannot construct two separated parallelograms")
    (h1, w1), (h2, w2) = rng.choice(choices)

    slack = height - (h1 + h2 + 1)
    top_pad = rng.randint(0, slack)
    remaining = slack - top_pad
    gap_extra = rng.randint(0, remaining)
    r1 = top_pad
    r2 = r1 + h1 + 1 + gap_extra
    bw1, bw2 = h1 + w1 - 2, h2 + w2 - 2
    c1 = rng.randint(0, width - bw1)
    c2 = rng.randint(0, width - bw2)
    _place(grid, _parallelogram(h1, w1), r1, c1, colors[0])
    _place(grid, _parallelogram(h2, w2), r2, c2, colors[1])


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_request(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    if overrides.get("profile") is None:
        scheduled = PROFILE_ORDER[(sample_index + _BAND_OFFSET[difficulty]) % len(PROFILE_ORDER)]
        profile = ctx.draw_choice("profile", (scheduled,))
    else:
        profile = ctx.draw_choice("profile", PROFILE_ORDER)

    height, width, n_objects = PROFILE_SPECS[profile]
    colors = ctx.draw_distinct_colors("object_colors", n=n_objects, exclude=(0,))
    grid = full_grid(height, width, 0)
    if n_objects == 1:
        _draw_one(ctx, grid, colors[0])
    else:
        _draw_two(ctx, grid, colors)
    return grid


def _components(grid):
    """Return row-major same-color 8-connected components."""
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[tuple[int, set[tuple[int, int]]]] = []
    for r in range(height):
        for c in range(width):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            seen.add((r, c))
            stack = [(r, c)]
            cells: set[tuple[int, int]] = set()
            while stack:
                rr, cc = stack.pop()
                cells.add((rr, cc))
                for dr, dc in _DIRS8:
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            components.append((color, cells))
    return components


def _shape_error(cells):
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    top, left = min(rows), min(cols)
    object_height = max(rows) - top + 1
    bbox_width = max(cols) - left + 1
    top_width = bbox_width - object_height + 2
    if object_height < 3 or top_width < 3:
        return "object bbox is too small for a hollow slanted parallelogram"
    normalized = {(r - top, c - left) for r, c in cells}
    if normalized != _parallelogram(object_height, top_width):
        return "object is not exactly a hollow right-slanting parallelogram"
    return None


def _profile_name(grid, components=None):
    components = _components(grid) if components is None else components
    signature = (len(grid), len(grid[0]), len(components))
    for name, spec in PROFILE_SPECS.items():
        if signature == spec:
            return name
    return None


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the complete ordinary lesson domain without mutating input."""
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["ragged grid"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer colors 0..9 (not bool)"]

    components = _components(grid)
    errors: list[str] = []
    if not components:
        errors.append("expected at least one nonzero parallelogram")
        return errors
    if _profile_name(grid, components) is None:
        errors.append(
            "grid shape and object count do not match a labeled canonical profile"
        )
    colors = [color for color, _ in components]
    if len(colors) != len(set(colors)):
        errors.append("separate objects must use distinct colors")
    for index, (_, cells) in enumerate(components):
        problem = _shape_error(cells)
        if problem:
            errors.append(f"object {index}: {problem}")
    for index, (_, left) in enumerate(components):
        for _, right in components[index + 1 :]:
            if any(
                max(abs(r1 - r2), abs(c1 - c2)) <= 1
                for r1, c1 in left
                for r2, c2 in right
            ):
                errors.append("objects must be separated under 8-connectivity")
    return errors


def strict_canonical_like(grid):
    return self_check(grid)


def observe_overrides(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe controls on invalid grid: " + "; ".join(errors))
    return {"profile": _profile_name(grid)}


def _stay_cells(grid, *, bottom=True, right=True):
    stays: set[tuple[int, int]] = set()
    for _, cells in _components(grid):
        max_row = max(r for r, _ in cells)
        max_col = max(c for _, c in cells)
        stays.update(
            (r, c)
            for r, c in cells
            if (bottom and r == max_row) or (right and c == max_col)
        )
    return stays


def _apply_with_stays(grid, stays):
    if not isinstance(grid, (list, tuple)) or not grid or not isinstance(grid[0], (list, tuple)) or not grid[0]:
        raise ValueError("expected a nonempty rectangular grid")
    height, width = len(grid), len(grid[0])
    output = full_grid(height, width, 0)
    for r in range(height):
        for c in range(width):
            if (r, c) in stays:
                output[r][c] = grid[r][c]
            elif (
                c > 0
                and grid[r][c - 1] != 0
                and (r, c - 1) not in stays
            ):
                output[r][c] = grid[r][c - 1]
    return output


def rule_mirror(grid):
    """Independent Python mirror of the pinned selected Racket rule."""
    return _apply_with_stays(grid, _stay_cells(grid, bottom=True, right=True))


def _bottom_only(grid):
    return _apply_with_stays(grid, _stay_cells(grid, bottom=True, right=False))


def _right_only(grid):
    return _apply_with_stays(grid, _stay_cells(grid, bottom=False, right=True))


def _shift_everything(grid):
    return _apply_with_stays(grid, set())


def _has_right_edge_stay(grid):
    try:
        return any(
            any(c == max(cc for _, cc in cells) and r < max(rr for rr, _ in cells)
                for r, c in cells)
            for _, cells in _components(grid)
        )
    except Exception:
        return False


def _has_bottom_edge_stay(grid):
    try:
        return any(
            any(r == max(rr for rr, _ in cells) and c < max(cc for _, cc in cells)
                for r, c in cells)
            for _, cells in _components(grid)
        )
    except Exception:
        return False


SEMANTIC_WITNESSES = {
    "right_edge_stays": _has_right_edge_stay,
    "bottom_edge_stays": _has_bottom_edge_stay,
}
SEMANTIC_RIVALS = {
    "bottom_only": _bottom_only,
    "right_only": _right_only,
}
WITNESS_RIVALS = {
    "right_edge_stays": ["bottom_only"],
    "bottom_edge_stays": ["right_only"],
}
LESSON_COMPETITORS = {
    "bottom_only": _bottom_only,
    "right_only": _right_only,
    "shift_everything": _shift_everything,
}


def lesson_identifiable(demos, query):
    """Report any declared competitor that fits all demos but changes query."""
    if not isinstance(demos, list) or not isinstance(query, dict):
        return ["expected labeled demonstrations and query"]
    if "input" not in query or "output" not in query:
        return ["query must be labeled for identifiability checking"]
    reasons = []
    for name, competitor in LESSON_COMPETITORS.items():
        try:
            fits = all(
                isinstance(pair, dict)
                and "input" in pair
                and "output" in pair
                and competitor(pair["input"]) == pair["output"]
                for pair in demos
            )
            changes_query = competitor(query["input"]) != query["output"]
        except Exception as exc:
            reasons.append(f"competitor {name} raised {type(exc).__name__}: {exc}")
            continue
        if fits and changes_query:
            reasons.append(
                f"competitor {name} fits every demonstration but changes the query"
            )
    return reasons
