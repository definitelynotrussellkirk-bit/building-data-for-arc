"""Semantic generator for ARC task ac4b61e7b230.

The input contains one 4-connected red (2) object and one 4-connected cyan
(8) object on black.  Move the red object toward cyan independently on each
axis until their bounding boxes abut; preserve both shapes and erase all other
cells.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "ac4b61e7b230"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "736dca1f0b72"
SUMMARY = "Move the red object along each separated axis until its bounding box abuts cyan."
INVARIANTS = [
    "background is color 0",
    "exactly one 4-connected color-2 object and one color-8 object",
    "the two object bounding boxes are separated on at least one axis",
    "the output preserves both shapes and makes their bounding boxes abut",
]

PUBLIC_PROFILES = (
    "public_train_1",
    "public_train_2",
    "public_train_3",
    "public_test_1",
)
GENERAL_PROFILES = (
    "red_upper_left",
    "red_above",
    "red_upper_right",
    "red_left",
    "red_right",
    "red_lower_left",
    "red_below",
    "red_lower_right",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "weighted exact-public and all eight spatial relations",
        "valid": "|".join(SCENE_PROFILES),
    }
}

_PUBLIC_ROWS = {
    "public_train_1": "0000000000/0220000000/0220000000/2220000000/0220008800/0000008800/0000000000/0000000000/0000000000",
    "public_train_2": "000000000/000000000/022200000/220200000/000000000/000000000/000000000/000000000/000000000/000000000/000880000/000880000/000000000/000000000",
    "public_train_3": "0000000000/0008800000/0008800000/0000000000/0000000000/0000000000/0002220000/0222220000/0022000000/0000000000/0000000000",
    "public_test_1": "0000000000/0000000000/0000000000/0000000000/0000020000/0000022000/0880022000/0880002000/0000000000/0000000000/0000000000",
}


def _decode(rows):
    return [[int(value) for value in row] for row in rows.split("/")]


_PUBLIC_INPUTS = {name: _decode(rows) for name, rows in _PUBLIC_ROWS.items()}
_PUBLIC_SIGNATURES = {tuple(map(tuple, grid)): name for name, grid in _PUBLIC_INPUTS.items()}
_RELATION_PROFILES = {
    (-1, -1): "red_upper_left",
    (-1, 0): "red_above",
    (-1, 1): "red_upper_right",
    (0, -1): "red_left",
    (0, 1): "red_right",
    (1, -1): "red_lower_left",
    (1, 0): "red_below",
    (1, 1): "red_lower_right",
}
_PROFILE_RELATION = {profile: relation for relation, profile in _RELATION_PROFILES.items()}

_SHAPES = {
    "single": ((0, 0),),
    "domino_h": ((0, 0), (0, 1)),
    "domino_v": ((0, 0), (1, 0)),
    "line_h3": ((0, 0), (0, 1), (0, 2)),
    "line_v3": ((0, 0), (1, 0), (2, 0)),
    "square2": ((0, 0), (0, 1), (1, 0), (1, 1)),
    "ell3": ((0, 0), (1, 0), (1, 1)),
    "ell5": ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2)),
    "tee5": ((0, 0), (0, 1), (0, 2), (1, 1), (2, 1)),
    "plus5": ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
    "zig5": ((0, 0), (1, 0), (1, 1), (2, 1), (2, 2)),
    "u7": ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2), (1, 2), (0, 2)),
    "stair7": ((0, 0), (1, 0), (1, 1), (2, 1), (2, 2), (3, 2), (3, 3)),
}


def _valid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be non-empty"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["rows must be non-empty"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["cells must be ARC colors"]
    return []


def _components(grid, color):
    height, width = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(height) for c in range(width) if grid[r][c] == color}
    components = []
    while unseen:
        todo = [next(iter(unseen))]
        cells = set()
        while todo:
            cell = todo.pop()
            if cell not in unseen:
                continue
            unseen.remove(cell)
            cells.add(cell)
            row, col = cell
            todo.extend(
                neighbor
                for neighbor in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1))
                if neighbor in unseen
            )
        components.append(cells)
    return components


def _bbox(cells):
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _axis_relation(first_low, first_high, second_low, second_high):
    if first_high < second_low:
        return -1
    if first_low > second_high:
        return 1
    return 0


def _translation(red_bbox, cyan_bbox):
    r1a, c1a, r2a, c2a = red_bbox
    r1b, c1b, r2b, c2b = cyan_bbox
    dr = r1b - r2a - 1 if r2a < r1b else r2b + 1 - r1a if r1a > r2b else 0
    dc = c1b - c2a - 1 if c2a < c1b else c2b + 1 - c1a if c1a > c2b else 0
    return dr, dc


def _analysis(grid):
    errors = _valid(grid)
    result = {"errors": errors, "scene_profile": None}
    if errors:
        return result
    height, width = len(grid), len(grid[0])
    unexpected = sorted({value for row in grid for value in row} - {0, 2, 8})
    if unexpected:
        errors.append(f"unexpected non-background colors: {unexpected}")
    red_parts = _components(grid, 2)
    cyan_parts = _components(grid, 8)
    if len(red_parts) != 1:
        errors.append(f"expected exactly one color-2 object, found {len(red_parts)}")
    if len(cyan_parts) != 1:
        errors.append(f"expected exactly one color-8 object, found {len(cyan_parts)}")
    if len(red_parts) != 1 or len(cyan_parts) != 1:
        return result
    red, cyan = red_parts[0], cyan_parts[0]
    red_bbox, cyan_bbox = _bbox(red), _bbox(cyan)
    relation = (
        _axis_relation(red_bbox[0], red_bbox[2], cyan_bbox[0], cyan_bbox[2]),
        _axis_relation(red_bbox[1], red_bbox[3], cyan_bbox[1], cyan_bbox[3]),
    )
    if relation == (0, 0):
        errors.append("object bounding boxes must be separated on at least one axis")
    dr, dc = _translation(red_bbox, cyan_bbox)
    shifted_red = {(row + dr, col + dc) for row, col in red}
    if any(not 0 <= row < height or not 0 <= col < width for row, col in shifted_red):
        errors.append("translated red object leaves the grid")
    if shifted_red & cyan:
        errors.append("translated red object overlaps cyan")
    output = [[0] * width for _ in range(height)]
    for row, col in cyan:
        output[row][col] = 8
    for row, col in shifted_red:
        output[row][col] = 2
    profile = _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid))) or _RELATION_PROFILES.get(relation)
    if profile not in SCENE_PROFILES:
        errors.append("object relation does not match a declared scene profile")
    result.update(
        {
            "red": red,
            "cyan": cyan,
            "red_bbox": red_bbox,
            "cyan_bbox": cyan_bbox,
            "relation": relation,
            "translation": (dr, dc),
            "shifted_red": shifted_red,
            "output": output,
            "scene_profile": profile,
            "errors": errors,
        }
    )
    return result


def rule_mirror(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return [row[:] for row in analysis["output"]]


def canonical_profile_signature(grid):
    analysis = _analysis(grid)
    profile = analysis.get("scene_profile")
    return profile if not analysis["errors"] and profile in PUBLIC_PROFILES else None


def observe_overrides(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {"scene_profile": analysis["scene_profile"]}


def _shape_size(shape):
    return max(row for row, _ in shape) + 1, max(col for _, col in shape) + 1


def _axis_layout(first_size, second_size, relation, gap, rng):
    if relation < 0:
        return 0, first_size + gap, first_size + gap + second_size
    if relation > 0:
        return second_size + gap, 0, second_size + gap + first_size
    span = max(first_size, second_size)
    if first_size <= second_size:
        return rng.randint(0, second_size - first_size), 0, span
    return 0, rng.randint(0, first_size - second_size), span


def _band(difficulty):
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return difficulty
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def _general(rng, profile, band):
    relation = _PROFILE_RELATION[profile]
    shape_names = list(_SHAPES)
    red_shape = _SHAPES[rng.choice(shape_names)]
    cyan_shape = _SHAPES[rng.choice(shape_names)]
    red_h, red_w = _shape_size(red_shape)
    cyan_h, cyan_w = _shape_size(cyan_shape)
    gaps = {"easy": (1, 3), "medium": (2, 6), "hard": (4, 8)}
    gap_low, gap_high = gaps[band]
    row_gap = rng.randint(gap_low, gap_high) if relation[0] else 0
    col_gap = rng.randint(gap_low, gap_high) if relation[1] else 0
    red_row, cyan_row, used_h = _axis_layout(red_h, cyan_h, relation[0], row_gap, rng)
    red_col, cyan_col, used_w = _axis_layout(red_w, cyan_w, relation[1], col_gap, rng)
    margins = {"easy": (1, 3), "medium": (1, 5), "hard": (2, 5)}
    margin_low, margin_high = margins[band]
    top, bottom = rng.randint(margin_low, margin_high), rng.randint(margin_low, margin_high)
    left, right = rng.randint(margin_low, margin_high), rng.randint(margin_low, margin_high)
    height, width = top + used_h + bottom, left + used_w + right
    grid = [[0] * width for _ in range(height)]
    for row, col in red_shape:
        grid[top + red_row + row][left + red_col + col] = 2
    for row, col in cyan_shape:
        grid[top + cyan_row + row][left + cyan_col + col] = 8
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - {"scene_profile"}
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")
    requested = overrides.get("scene_profile")
    if requested is not None and requested not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {requested!r}")
    band = _band(difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    profile = requested or ctx.draw_choice(
        "scene_profile",
        list(PUBLIC_PROFILES) + [name for name in GENERAL_PROFILES for _ in range(4)],
    )
    if profile in PUBLIC_PROFILES:
        return [row[:] for row in _PUBLIC_INPUTS[profile]]
    return _general(ctx.draw_rng("layout"), profile, band)


def self_check(grid, *, difficulty=None, meta=None):
    return list(_analysis(grid)["errors"])
