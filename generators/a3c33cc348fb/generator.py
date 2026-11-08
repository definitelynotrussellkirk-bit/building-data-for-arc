"""Semantic generator for ARC task a3c33cc348fb (source b548a754).

A two-color filled rectangle expands its bounding box just far enough to
contain the first cyan marker.  The expanded perimeter keeps the original
frame color, the expanded interior uses the original inner color, the marker
is consumed, and every cell outside the new rectangle becomes background.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "a3c33cc348fb"
TASK_ID = "a3c33cc348fb"
VERSION = "3.1.0"
RULE_HASH = "b3185fa9390c"
SUMMARY = "Expand a two-color framed rectangle to include the cyan marker while preserving frame and interior colors."
INVARIANTS = [
    "calibrated inputs contain one solid two-color framed rectangle and one cyan marker",
    "the marker lies outside and shares a row or column with the rectangle, including edge alignment",
    "the output bounding box is the coordinate union of the source rectangle and marker",
    "the expanded perimeter keeps the source frame color and its strict interior uses the source inner color",
    "the cyan marker is consumed and every cell outside the expanded rectangle becomes zero",
]

PUBLIC_PROFILES = ("public_1", "public_2", "public_3", "public_4")
GENERAL_PROFILES = ("near_reach", "left_reach", "corner_reach", "far_reach")
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "four complete official reach families plus four controlled distance/alignment contrasts",
        "valid": "|".join(SCENE_PROFILES),
    }
}

_PUBLIC_ROWS = {
    "public_1": (
        "00000000000", "03333300000", "03222300008", "03222300000",
        "03333300000", "00000000000", "00000000000", "00000000000",
        "00000000000", "00000000000", "00000000000",
    ),
    "public_2": (
        "00000000000", "02222000000", "02112000000", "02112000000",
        "02222000000", "00000000000", "00000000000", "00000000000",
        "00080000000", "00000000000", "00000000000",
    ),
    "public_3": (
        "000000000000", "001110000000", "001610000000", "001610000000",
        "001610000000", "001110000080", "000000000000", "000000000000",
        "000000000000", "000000000000", "000000000000", "000000000000",
        "000000000000",
    ),
    "public_4": (
        "0000000000000", "0000800000000", "0000000000000", "0000000000000",
        "0000000000000", "0000000000000", "0000000000000", "0000000000000",
        "0000000000000", "0006666600000", "0006444600000", "0006444600000",
        "0006666600000",
    ),
}
_PUBLIC_INPUTS = {
    profile: [[int(value) for value in row] for row in rows]
    for profile, rows in _PUBLIC_ROWS.items()
}
_PUBLIC_EXACT = {
    tuple(map(tuple, grid)): profile for profile, grid in _PUBLIC_INPUTS.items()
}
_PUBLIC_KEYS = {
    (5, 4, 5, 1): "public_1",
    (4, 4, 4, 1): "public_2",
    (3, 5, 6, 0): "public_3",
    (4, 5, 8, 1): "public_4",
}
_PUBLIC_SPECS = {
    "public_1": {"height": 4, "width": 5, "side": "right", "distance": 5, "offset": 1},
    "public_2": {"height": 4, "width": 4, "side": "bottom", "distance": 4, "offset": 2},
    "public_3": {"height": 5, "width": 3, "side": "right", "distance": 6, "offset": 4},
    "public_4": {"height": 4, "width": 5, "side": "top", "distance": 8, "offset": 1},
}
_CANONICAL_SHAPES = ((11, 11), (13, 12), (13, 13))



def _valid_grid(grid):
    if not isinstance(grid, (list, tuple)) or not 1 <= len(grid) <= 30:
        return ["input must contain one through thirty rows"]
    if not isinstance(grid[0], (list, tuple)) or not 1 <= len(grid[0]) <= 30:
        return ["input must contain one through thirty columns"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["input must be rectangular"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid for value in row
    ):
        return ["input cells must be literal ARC color integers from zero through nine"]
    return []


def _first_cyan(grid):
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value == 8:
                return row, col
    raise ValueError("rule requires at least one cyan marker")


def _non_background(grid):
    return [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value not in (0, 8)
    ]


def rule_mirror(grid):
    """Broad, input-pure mirror of the canonical Racket program."""
    errors = _valid_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    height, width = len(grid), len(grid[0])
    marker_row, marker_col = _first_cyan(grid)
    cells = _non_background(grid)
    if not cells:
        raise ValueError("rule requires at least one non-background non-cyan cell")
    rows = [row for row, _, _ in cells]
    cols = [col for _, col, _ in cells]
    row0, row1, col0, col1 = min(rows), max(rows), min(cols), max(cols)
    frame_color = grid[row0][col0]
    inner_color = next((value for _, _, value in cells if value != frame_color), frame_color)
    new_row0, new_row1 = min(row0, marker_row), max(row1, marker_row)
    new_col0, new_col1 = min(col0, marker_col), max(col1, marker_col)
    output = [[0] * width for _ in range(height)]
    for row in range(new_row0, new_row1 + 1):
        for col in range(new_col0, new_col1 + 1):
            if row in (new_row0, new_row1) or col in (new_col0, new_col1):
                output[row][col] = frame_color
            else:
                output[row][col] = inner_color
    return output


def _relationship(frame_height, frame_width, side, distance, offset):
    if side in ("left", "right"):
        depth, edge_length = frame_width, frame_height
    else:
        depth, edge_length = frame_height, frame_width
    corner_distance = min(offset, edge_length - 1 - offset)
    return depth, edge_length, distance, corner_distance


def _analysis(grid):
    errors = _valid_grid(grid)
    if errors:
        return {"errors": errors, "scene_profile": None, "facts": None, "output": None}
    height, width = len(grid), len(grid[0])
    if not 10 <= height <= 30 or not 10 <= width <= 30:
        errors.append("calibrated canvas dimensions must be ten through thirty")
    markers = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 8
    ]
    if len(markers) != 1:
        errors.append(f"expected exactly one cyan marker, got {len(markers)}")
    cells = _non_background(grid)
    if not cells:
        errors.append("calibrated input requires a framed rectangle")
        return {"errors": errors, "scene_profile": None, "facts": None, "output": None}
    colors = {value for _, _, value in cells}
    if len(colors) != 2 or any(color in (0, 8) for color in colors):
        errors.append("framed rectangle must use exactly two distinct nonzero non-cyan colors")
    rows = [row for row, _, _ in cells]
    cols = [col for _, col, _ in cells]
    row0, row1, col0, col1 = min(rows), max(rows), min(cols), max(cols)
    frame_height, frame_width = row1 - row0 + 1, col1 - col0 + 1
    if not 3 <= frame_height <= 9 or not 3 <= frame_width <= 9:
        errors.append("source rectangle sides must be three through nine")
    frame_color = grid[row0][col0]
    inner_color = next((value for _, _, value in cells if value != frame_color), frame_color)
    expected_cells = {
        (row, col)
        for row in range(row0, row1 + 1)
        for col in range(col0, col1 + 1)
    }
    actual_cells = {(row, col) for row, col, _ in cells}
    if actual_cells != expected_cells:
        errors.append("all non-background non-cyan cells must form one solid rectangle")
    for row, col in expected_cells:
        expected = frame_color if row in (row0, row1) or col in (col0, col1) else inner_color
        if grid[row][col] != expected:
            errors.append("source rectangle must have one exact perimeter color and one exact interior color")
            break
    side = None
    distance = None
    offset = None
    if len(markers) == 1:
        marker_row, marker_col = markers[0]
        if marker_col < col0 and row0 <= marker_row <= row1:
            side, distance, offset = "left", col0 - marker_col, marker_row - row0
        elif marker_col > col1 and row0 <= marker_row <= row1:
            side, distance, offset = "right", marker_col - col1, marker_row - row0
        elif marker_row < row0 and col0 <= marker_col <= col1:
            side, distance, offset = "top", row0 - marker_row, marker_col - col0
        elif marker_row > row1 and col0 <= marker_col <= col1:
            side, distance, offset = "bottom", marker_row - row1, marker_col - col0
        else:
            errors.append("cyan marker must lie outside and share an inclusive frame row or column")
    if distance is not None and not 1 <= distance <= 12:
        errors.append("marker distance must be one through twelve")
    key = (
        _relationship(frame_height, frame_width, side, distance, offset)
        if side is not None else None
    )
    profile = _PUBLIC_KEYS.get(key)
    if profile is None and side is not None:
        corner_aligned = offset in (0, (frame_height if side in ("left", "right") else frame_width) - 1)
        if 1 <= distance <= 3:
            profile = "near_reach"
        elif 9 <= distance <= 12:
            profile = "far_reach"
        elif 4 <= distance <= 8 and corner_aligned:
            profile = "corner_reach"
        elif 4 <= distance <= 8 and side == "left":
            profile = "left_reach"
    if profile is None and not errors:
        errors.append(f"unsupported calibrated reach signature {key!r} on side {side!r}")
    output = rule_mirror(grid) if markers and cells else None
    if not errors and output == [list(row) for row in grid]:
        errors.append("calibrated expansion must visibly consume the marker and change the rectangle")
    return {
        "errors": errors,
        "scene_profile": profile if not errors else None,
        "facts": {
            "bbox": (row0, col0, row1, col1),
            "height": frame_height,
            "width": frame_width,
            "frame_color": frame_color,
            "inner_color": inner_color,
            "marker": markers[0] if len(markers) == 1 else None,
            "side": side,
            "distance": distance,
            "offset": offset,
            "corner_aligned": offset in (0, (frame_height if side in ("left", "right") else frame_width) - 1) if side is not None else None,
            "relationship": key,
        },
        "output": output,
    }


def canonical_profile_signature(grid):
    try:
        return _PUBLIC_EXACT.get(tuple(tuple(row) for row in grid))
    except TypeError:
        return None


def canonical_family_signature(grid):
    analysis = _analysis(grid)
    profile = analysis["scene_profile"]
    return profile if profile in PUBLIC_PROFILES and not analysis["errors"] else None


def observe_overrides(grid):
    analysis = _analysis(grid)
    return {"scene_profile": analysis["scene_profile"]} if not analysis["errors"] else {}


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    return _analysis(grid)["errors"]


def strict_canonical_like(grid):
    """Return reasons when a grid falls outside this task's teaching grammar."""
    return self_check(grid)


def _marker_line_only(grid):
    """Plausible rival: connect the marker but do not repaint the full new box."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("marker-line rival requires a calibrated task input")
    height, width = len(grid), len(grid[0])
    facts = analysis["facts"]
    row0, col0, row1, col1 = facts["bbox"]
    marker_row, marker_col = facts["marker"]
    frame_color = facts["frame_color"]
    output = [[0] * width for _ in range(height)]
    for row in range(row0, row1 + 1):
        for col in range(col0, col1 + 1):
            output[row][col] = grid[row][col]
    if facts["side"] == "left":
        for col in range(marker_col, col0):
            output[marker_row][col] = frame_color
    elif facts["side"] == "right":
        for col in range(col1 + 1, marker_col + 1):
            output[marker_row][col] = frame_color
    elif facts["side"] == "top":
        for row in range(marker_row, row0):
            output[row][marker_col] = frame_color
    else:
        for row in range(row1 + 1, marker_row + 1):
            output[row][marker_col] = frame_color
    return output


def _full_bbox_repaint(grid):
    return (
        strict_canonical_like(grid) == []
        and _marker_line_only(grid) != rule_mirror(grid)
    )


SEMANTIC_RIVALS = {"marker_line_only": _marker_line_only}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES = {"full_bbox_repaint": _full_bbox_repaint}
WITNESS_RIVALS = {"full_bbox_repaint": ["marker_line_only"]}


def lesson_identifiable(demos, query):
    """Reject lessons whose labelled demonstrations leave a named rival alive."""
    if not isinstance(demos, (list, tuple)) or not demos:
        return ["expected at least one labelled demonstration"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output grids"]
    reasons = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        errors = strict_canonical_like(pair["input"])
        if errors:
            reasons.append(f"demo {index} is outside the teaching grammar: {errors[0]}")
        elif rule_mirror(pair["input"]) != pair["output"]:
            reasons.append(f"demo {index} output does not match the selected rule")
    query_errors = strict_canonical_like(query["input"])
    if query_errors:
        reasons.append(f"query is outside the teaching grammar: {query_errors[0]}")
    elif rule_mirror(query["input"]) != query["output"]:
        reasons.append("query output does not match the selected rule")
    if reasons:
        return reasons
    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(pair["input"]) == pair["output"] for pair in demos):
            reasons.append(f"named rival {name!r} fits every demonstration")
    return reasons


def _rotate_spec(spec):
    height, width = spec["height"], spec["width"]
    side, offset = spec["side"], spec["offset"]
    if side == "top":
        new_side, new_offset = "right", offset
    elif side == "right":
        new_side, new_offset = "bottom", height - 1 - offset
    elif side == "bottom":
        new_side, new_offset = "left", offset
    else:
        new_side, new_offset = "top", height - 1 - offset
    return {
        **spec,
        "height": width,
        "width": height,
        "side": new_side,
        "offset": new_offset,
    }


def _mirror_spec(spec):
    side, offset = spec["side"], spec["offset"]
    if side in ("top", "bottom"):
        offset = spec["width"] - 1 - offset
    elif side == "left":
        side = "right"
    else:
        side = "left"
    return {**spec, "side": side, "offset": offset}


def _random_d4(spec, rng):
    result = dict(spec)
    for _ in range(rng.randrange(4)):
        result = _rotate_spec(result)
    if rng.random() < 0.5:
        result = _mirror_spec(result)
    return result


def _side_edge_length(height, width, side):
    return height if side in ("left", "right") else width


def _general_spec(profile, difficulty, rng):
    if difficulty == "easy":
        low, high = 3, 5
    elif difficulty == "hard":
        low, high = 5, 9
    else:
        low, high = 4, 7
    for _ in range(200):
        height, width = rng.randint(low, high), rng.randint(low, high)
        if profile == "left_reach":
            side = "left"
            distance = rng.randint(4, 8)
            offset = rng.randint(1, height - 2)
        elif profile == "near_reach":
            side = rng.choice(("top", "bottom", "left", "right"))
            distance = rng.randint(1, 3)
            edge = _side_edge_length(height, width, side)
            offset = rng.randint(0, edge - 1)
        elif profile == "corner_reach":
            side = rng.choice(("top", "bottom", "left", "right"))
            distance = rng.randint(4, 8)
            edge = _side_edge_length(height, width, side)
            offset = rng.choice((0, edge - 1))
        elif profile == "far_reach":
            side = rng.choice(("top", "bottom", "left", "right"))
            distance = rng.randint(9, 10 if difficulty == "easy" else 11 if difficulty in (None, "medium") else 12)
            edge = _side_edge_length(height, width, side)
            offset = rng.randint(0, edge - 1)
        else:
            raise ValueError(f"unknown generalized profile: {profile!r}")
        spec = {
            "height": height,
            "width": width,
            "side": side,
            "distance": distance,
            "offset": offset,
        }
        if _PUBLIC_KEYS.get(_relationship(height, width, side, distance, offset)) is None:
            return spec
    raise AssertionError(f"could not construct distinct generalized profile {profile!r}")


def _footprint(spec):
    height, width = spec["height"], spec["width"]
    side, distance, offset = spec["side"], spec["distance"], spec["offset"]
    marker = {
        "top": (-distance, offset),
        "bottom": (height - 1 + distance, offset),
        "left": (offset, -distance),
        "right": (offset, width - 1 + distance),
    }[side]
    min_row, min_col = min(0, marker[0]), min(0, marker[1])
    max_row, max_col = max(height - 1, marker[0]), max(width - 1, marker[1])
    return marker, min_row, min_col, max_row, max_col


def _limits(difficulty):
    if difficulty == "easy":
        return 10, 16
    if difficulty == "medium":
        return 12, 20
    if difficulty == "hard":
        return 16, 24
    return 12, 20


def _render_spec(spec, difficulty, rng, *, canonical_scale=False):
    marker, min_row, min_col, max_row, max_col = _footprint(spec)
    footprint_height = max_row - min_row + 1
    footprint_width = max_col - min_col + 1
    low, high = _limits(difficulty)
    if footprint_height > high or footprint_width > high:
        raise AssertionError("reach footprint exceeds calibrated canvas")
    if canonical_scale:
        candidates = [
            shape for shape in _CANONICAL_SHAPES
            if shape[0] >= footprint_height and shape[1] >= footprint_width
        ]
        if not candidates:
            raise AssertionError("reach footprint exceeds canonical canvas")
        height, width = rng.choice(candidates)
    else:
        height = rng.randint(max(low, footprint_height), high)
        width = rng.randint(max(low, footprint_width), high)
    foot_row = rng.randint(0, height - footprint_height)
    foot_col = rng.randint(0, width - footprint_width)
    row0, col0 = foot_row - min_row, foot_col - min_col
    palette = [color for color in range(1, 10) if color != 8]
    rng.shuffle(palette)
    frame_color, inner_color = palette[:2]
    grid = [[0] * width for _ in range(height)]
    row1, col1 = row0 + spec["height"] - 1, col0 + spec["width"] - 1
    for row in range(row0, row1 + 1):
        for col in range(col0, col1 + 1):
            grid[row][col] = (
                frame_color
                if row in (row0, row1) or col in (col0, col1)
                else inner_color
            )
    grid[foot_row + marker[0] - min_row][foot_col + marker[1] - min_col] = 8
    return grid


def _random_scene(profile, difficulty, rng, *, canonical_scale=False):
    for _ in range(300):
        spec = (
            _random_d4(_PUBLIC_SPECS[profile], rng)
            if profile in PUBLIC_PROFILES
            else _general_spec(profile, difficulty, rng)
        )
        try:
            grid = _render_spec(spec, difficulty, rng, canonical_scale=canonical_scale)
        except AssertionError:
            continue
        analysis = _analysis(grid)
        if not analysis["errors"] and analysis["scene_profile"] == profile:
            return grid
    raise AssertionError(f"could not construct rectangle-reach lesson {profile!r}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if type(seed) is not int:
        raise TypeError("seed must be a literal integer")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be a literal integer")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = set(overrides) - {"scene_profile"}
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)!r}")
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = ctx.draw_choice("scene_profile", list(PUBLIC_PROFILES) * 3 + list(GENERAL_PROFILES) * 2)
    if profile not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {profile!r}")
    if profile in PUBLIC_PROFILES and overrides.get("scene_profile") is not None:
        return [row[:] for row in _PUBLIC_INPUTS[profile]]
    canonical_scale = (
        profile in PUBLIC_PROFILES
        and ctx.draw_rng("canonical_scale").random() < 0.5
    )
    grid = _random_scene(
        profile,
        difficulty,
        ctx.draw_rng("scene"),
        canonical_scale=canonical_scale,
    )
    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid rectangle-reach lesson: " + "; ".join(errors))
    return grid
