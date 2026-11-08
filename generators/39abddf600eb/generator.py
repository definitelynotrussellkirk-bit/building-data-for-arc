"""Input generator for Manhattan-bisector task 39abddf600eb.

A lawful input contains one inset rectangular frame and exactly two colored
seeds in its strict interior.  The unchanged canonical rule redraws those
objects on black and paints color 9 at every strict-interior cell whose
Manhattan distance to the two seeds is equal.

Opposite-parity seeds are intentionally lawful: their integer-grid bisector is
empty, producing the identity examples present in the canonical task.  The
default schedule rotates identity, aligned-axis, and diagonal geometries so any
three consecutive lesson demonstrations include a counterexample to the
plausible but wrong "only diagonal pairs transform" shortcut.
"""
from __future__ import annotations

from functools import lru_cache
from itertools import combinations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "39abddf600eb"
TASK_ID = GENERATOR_ID
RULE_HASH = "38c495fef5e9"
VERSION = "3.1.0"
ALLOW_IDENTITY_OUTPUT = True
EXAMPLES_NEEDED = 3

SUMMARY = (
    "An inset rectangular frame contains exactly two colored seeds. Paint color 9 "
    "on every strict-interior cell equidistant from the seeds in Manhattan distance; "
    "opposite-parity seeds lawfully yield an unchanged input."
)

INVARIANTS = [
    "exactly one complete inset rectangular frame in one color",
    "exactly two nonzero non-frame seeds strictly inside that frame",
    "no other nonzero cells occur in the input",
]

AXES = {
    "grid_h": {"type": "int", "default": "canonical-profile schedule plus broad cases", "valid": "8..16"},
    "grid_w": {"type": "int", "default": "canonical-profile schedule plus broad cases", "valid": "8..18"},
    "frame_color": {"type": "int", "default": "uniform 2..8", "valid": "2..8"},
    "seed_geometry": {
        "type": "str",
        "default": "cyclic identity|axis|diagonal",
        "valid": "identity|axis|diagonal",
    },
    "seed_color_relation": {
        "type": "str",
        "default": "mostly different, periodically same",
        "valid": "same|different",
    },
}
# Every combination is constructible even on the minimum 8x8 canvas.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

_GEOMETRIES = ("axis", "diagonal", "identity")
# At least two aligned examples occur in every four consecutive draws.  Thus a
# four-pair lesson remains identifying even when any one pair is rotated into
# the query slot and the other three are used as demonstrations.
_GEOMETRY_SCHEDULE = ("axis", "diagonal", "axis", "identity", "axis", "diagonal")
_COLOR_RELATIONS = ("same", "different")
_CANONICAL_SHAPES = {
    None: ((10, 12), (11, 11), (11, 13), (12, 13), (12, 14)),
    "easy": ((10, 12), (11, 11)),
    "medium": ((10, 12), (11, 13), (12, 13)),
    "hard": ((11, 13), (12, 14)),
}


def _draw_frame(grid, r1, c1, r2, c2, color):
    for c in range(c1, c2 + 1):
        grid[r1][c] = color
        grid[r2][c] = color
    for r in range(r1, r2 + 1):
        grid[r][c1] = color
        grid[r][c2] = color


def _validate_overrides(overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name in ("grid_h", "grid_w", "frame_color"):
        value = overrides.get(name)
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
    for name in ("seed_geometry", "seed_color_relation"):
        value = overrides.get(name)
        if value is not None and type(value) is not str:
            raise ValueError(f"{name} must be a string, not {type(value).__name__}")
    ranges = {"grid_h": (8, 16), "grid_w": (8, 18), "frame_color": (2, 8)}
    for name, (lo, hi) in ranges.items():
        value = overrides.get(name)
        if value is not None and not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside [{lo}, {hi}]")
    if overrides.get("seed_geometry") not in (None, *_GEOMETRIES):
        raise ValueError(f"seed_geometry must be one of {_GEOMETRIES}")
    if overrides.get("seed_color_relation") not in (None, *_COLOR_RELATIONS):
        raise ValueError(f"seed_color_relation must be one of {_COLOR_RELATIONS}")


def _scheduled_shape(ctx, sample_index, difficulty):
    # Four of every five defaults anchor the exact canonical (h,w,palette)
    # manifold. The fifth deliberately explores the complete advertised canvas.
    if sample_index % 5 != 4:
        shapes = _CANONICAL_SHAPES.get(difficulty, _CANONICAL_SHAPES[None])
        return ctx.draw_rng("canonical_shape").choice(shapes)
    rng = ctx.draw_rng("broad_shape")
    return rng.randint(8, 16), rng.randint(8, 18)


def _draw_axis(ctx, name, full_domain, scheduled):
    options = full_domain if ctx.overrides.get(name) is not None else (scheduled,)
    return ctx.draw_choice(name, options)


@lru_cache(maxsize=256)
def _frame_boxes(h, w):
    boxes = []
    for top_margin in (1, 2):
        for bottom_margin in (1, 2):
            r1, r2 = top_margin, h - 1 - bottom_margin
            if r2 - r1 < 4:
                continue
            for left_margin in (1, 2):
                for right_margin in (1, 2):
                    c1, c2 = left_margin, w - 1 - right_margin
                    if c2 - c1 >= 4:
                        boxes.append((r1, c1, r2, c2))
    return tuple(boxes)


@lru_cache(maxsize=512)
def _relative_pairs(interior_h, interior_w, geometry):
    points = tuple((r, c) for r in range(interior_h) for c in range(interior_w))
    pairs = []
    for a, b in combinations(points, 2):
        same_parity = (a[0] + a[1]) % 2 == (b[0] + b[1]) % 2
        aligned = a[0] == b[0] or a[1] == b[1]
        if geometry == "identity" and not same_parity:
            pairs.append((a, b))
        elif geometry == "axis" and same_parity and aligned:
            pairs.append((a, b))
        elif geometry == "diagonal" and same_parity and not aligned:
            pairs.append((a, b))
    return tuple(pairs)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    scheduled_h, scheduled_w = _scheduled_shape(ctx, sample_index, difficulty)
    h = _draw_axis(ctx, "grid_h", tuple(range(8, 17)), scheduled_h)
    w = _draw_axis(ctx, "grid_w", tuple(range(8, 19)), scheduled_w)
    frame_color = ctx.draw_int("frame_color", 2, 8)

    scheduled_geometry = _GEOMETRY_SCHEDULE[sample_index % len(_GEOMETRY_SCHEDULE)]
    geometry = _draw_axis(ctx, "seed_geometry", _GEOMETRIES, scheduled_geometry)
    scheduled_relation = "same" if sample_index % 7 == 6 else "different"
    relation = _draw_axis(ctx, "seed_color_relation", _COLOR_RELATIONS, scheduled_relation)

    boxes = _frame_boxes(h, w)
    if not boxes:
        raise RuntimeError(f"no lawful frame box for {h}x{w}")
    r1, c1, r2, c2 = ctx.draw_rng("frame_box").choice(boxes)
    grid = full_grid(h, w, 0)
    _draw_frame(grid, r1, c1, r2, c2, frame_color)

    pairs = _relative_pairs(r2 - r1 - 1, c2 - c1 - 1, geometry)
    if not pairs:
        raise RuntimeError(f"no {geometry} seed pair fits frame {(r1, c1, r2, c2)}")
    (ar, ac), (br, bc) = ctx.draw_rng("seed_positions").choice(pairs)
    a = (r1 + 1 + ar, c1 + 1 + ac)
    b = (r1 + 1 + br, c1 + 1 + bc)

    colors = tuple(color for color in range(1, 9) if color != frame_color)
    color_rng = ctx.draw_rng("seed_colors")
    if relation == "same":
        first = second = color_rng.choice(colors)
    else:
        first, second = color_rng.sample(colors, 2)
    grid[a[0]][a[1]] = first
    grid[b[0]][b[1]] = second
    return grid


def _parse_scene(grid):
    if not isinstance(grid, list) or not grid:
        raise ValueError("grid must be a nonempty list")
    if not isinstance(grid[0], list) or not grid[0]:
        raise ValueError("grid rows must be nonempty lists")
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("grid cells must be integer colors 0..9")
    h, w = len(grid), width
    if not 8 <= h <= 16 or not 8 <= w <= 18:
        raise ValueError(f"grid dimensions {h}x{w} outside 8..16 by 8..18")

    nonzero = [(r, c, value) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
    candidates = []
    for color in sorted({value for _, _, value in nonzero} - {9}):
        points = {(r, c) for r, c, value in nonzero if value == color}
        rs = [r for r, _ in points]
        cs = [c for _, c in points]
        r1, r2, c1, c2 = min(rs), max(rs), min(cs), max(cs)
        if r2 - r1 < 4 or c2 - c1 < 4:
            continue
        border = (
            {(r1, c) for c in range(c1, c2 + 1)}
            | {(r2, c) for c in range(c1, c2 + 1)}
            | {(r, c1) for r in range(r1, r2 + 1)}
            | {(r, c2) for r in range(r1, r2 + 1)}
        )
        if points == border:
            candidates.append((r1, c1, r2, c2, color, border))
    if len(candidates) != 1:
        raise ValueError(f"expected exactly one complete rectangular frame, found {len(candidates)}")

    r1, c1, r2, c2, frame_color, border = candidates[0]
    if frame_color not in range(2, 9):
        raise ValueError(f"frame color {frame_color} outside 2..8")
    if not (0 < r1 < r2 < h - 1 and 0 < c1 < c2 < w - 1):
        raise ValueError("frame must be strictly inset from the grid boundary")

    extras = [(r, c, value) for r, c, value in nonzero if (r, c) not in border]
    if len(extras) != 2:
        raise ValueError(f"expected exactly two seeds and no other marks, found {len(extras)}")
    seeds = sorted(extras)
    for r, c, color in seeds:
        if not (r1 < r < r2 and c1 < c < c2):
            raise ValueError("every seed must lie strictly inside the frame")
        if color in (0, 9, frame_color):
            raise ValueError("seed colors must be 1..8 and distinct from the frame")
    return {
        "height": h,
        "width": w,
        "r1": r1,
        "c1": c1,
        "r2": r2,
        "c2": c2,
        "frame_color": frame_color,
        "border": border,
        "seeds": seeds,
    }


def _geometry(scene):
    (ar, ac, _), (br, bc, _) = scene["seeds"]
    if (ar + ac - br - bc) % 2:
        return "identity"
    return "axis" if ar == br or ac == bc else "diagonal"


def observe_overrides(grid):
    """Recover every advertised exact axis from returned pixels."""
    scene = _parse_scene(grid)
    a, b = scene["seeds"]
    return {
        "grid_h": scene["height"],
        "grid_w": scene["width"],
        "frame_color": scene["frame_color"],
        "seed_geometry": _geometry(scene),
        "seed_color_relation": "same" if a[2] == b[2] else "different",
    }


def self_check(grid, *, difficulty=None, meta=None):
    """Return diagnostics for inputs outside the declared framed-seed grammar."""
    try:
        _parse_scene(grid)
    except (TypeError, ValueError) as exc:
        return [str(exc)]
    return []


def strict_canonical_like(grid):
    """For this task, every lawful declared input is on the rule's manifold."""
    return self_check(grid)


def _manhattan_output(grid):
    scene = _parse_scene(grid)
    out = full_grid(scene["height"], scene["width"], 0)
    for r, c in scene["border"]:
        out[r][c] = scene["frame_color"]
    for r, c, color in scene["seeds"]:
        out[r][c] = color
    (ar, ac, _), (br, bc, _) = scene["seeds"]
    for r in range(scene["r1"] + 1, scene["r2"]):
        for c in range(scene["c1"] + 1, scene["c2"]):
            if abs(r - ar) + abs(c - ac) == abs(r - br) + abs(c - bc):
                out[r][c] = 9
    return out


def _diagonal_only(grid):
    """RIVAL only: incorrectly leaves every aligned seed pair unchanged."""
    scene = _parse_scene(grid)
    (ar, ac, _), (br, bc, _) = scene["seeds"]
    if ar == br or ac == bc:
        return [list(row) for row in grid]
    return _manhattan_output(grid)


def _has_aligned_seed_pair(grid):
    return observe_overrides(grid)["seed_geometry"] == "axis"


def lesson_identifiable(demos, query):
    """Require a demonstration that falsifies the diagonal-only shortcut."""
    try:
        if any(_diagonal_only(demo["input"]) != demo["output"] for demo in demos):
            return []
    except (KeyError, TypeError, ValueError) as exc:
        return [f"malformed lesson while checking diagonal-only rival: {exc}"]
    return ["no aligned-seed demonstration refutes the diagonal-only rival"]


SEMANTIC_WITNESSES = {"aligned_seed_pair": _has_aligned_seed_pair}
SEMANTIC_RIVALS = {"diagonal_only": _diagonal_only}
WITNESS_RIVALS = {"aligned_seed_pair": ["diagonal_only"]}
CANONICAL_SHORTCUTS = {"diagonal_only": _diagonal_only}
LESSON_COMPETITORS = {"diagonal_only": _diagonal_only}
