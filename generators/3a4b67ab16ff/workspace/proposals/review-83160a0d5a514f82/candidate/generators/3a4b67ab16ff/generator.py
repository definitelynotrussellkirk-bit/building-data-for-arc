"""Semantic generator for ARC task 3a4b67ab16ff.

Color 5 defines one bounding rectangle.  The output first restores that whole
rectangle to gray and clears everything outside it.  For every other color,
all occurrences in the input define a bounding box; its intersection with the
gray rectangle is filled with that color.  Colors are applied from 1 through
9 (skipping 5), so a numerically later color wins where intersections overlap.
"""
from __future__ import annotations

from itertools import combinations

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "3a4b67ab16ff"
TASK_ID = "3a4b67ab16ff"
VERSION = "3.1.0"
RULE_HASH = "32c694357bd0"
SUMMARY = "Intersect each marker-color bounding box with the gray bounding rectangle, filling intersections in ascending color order."
INVARIANTS = [
    "background outside the gray bounding rectangle becomes zero",
    "the complete gray bounding rectangle is restored before colored fills",
    "all cells of each nonzero non-gray color jointly define one bounding box",
    "each color fills only the intersection of its bounding box with the gray rectangle",
    "colors are applied in ascending numeric order, so higher colors win overlaps",
]

PUBLIC_PROFILES = ("public_1", "public_2", "public_3", "public_4")
GENERAL_PROFILES = (
    "top_left_projection",
    "top_right_projection",
    "bottom_left_projection",
    "bottom_right_projection",
    "horizontal_band",
    "vertical_band",
    "interior_box",
    "split_extrema",
    "three_color_nonoverlap",
    "overlap_priority",
    "inactive_companion",
    "full_bbox_projection",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "four exact-public and twelve recoverable bbox-intersection lessons",
        "valid": "public_1|public_2|public_3|public_4|top_left_projection|top_right_projection|bottom_left_projection|bottom_right_projection|horizontal_band|vertical_band|interior_box|split_extrema|three_color_nonoverlap|overlap_priority|inactive_companion|full_bbox_projection",
    }
}

_PUBLIC_ROWS = (
    "000000000000000/000000003000000/003555555555500/005555555555500/005555555555500/005555555555500/035555555555500/005555555555540/005555555555500/005555555555500/005555555555500/005555555555500/005555555555400/000000004000000/000000000000000",
    "000000000000000/000000000000000/000000002000000/000255555555500/000555555555500/000555555555500/000555555555500/000555555555500/000555555555500/002555555555500/000555555555500/000555555555500/000555555555500/000000000000000/000000000000000",
    "000000100040000/001555555555540/005555555555550/005555555555550/015555555555550/005555555555550/005555555555550/005555555555554/065555555555550/005555555555550/005555555555550/005555555555550/005555555555550/006555555555550/000006000000000",
    "000060010000000/065555555555510/055555555555550/055555555555550/055555555555550/055555555555551/055555555555550/655555555555550/055555555555553/055555555555550/755555555555550/055555555555550/055555555555550/075555555555530/000000007003000",
)


def _decode(text):
    return [[int(value) for value in row] for row in text.split("/")]


_PUBLIC_INPUTS = {name: _decode(text) for name, text in zip(PUBLIC_PROFILES, _PUBLIC_ROWS)}
_PUBLIC_SIGNATURES = {tuple(map(tuple, grid)): profile for profile, grid in _PUBLIC_INPUTS.items()}
_MARKER_COLORS = (1, 2, 3, 4, 6, 7, 8, 9)


def _valid_grid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be non-empty"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if not 5 <= len(grid) <= 30 or not 5 <= width <= 30:
        return ["input dimensions must be between 5 and 30 on both axes"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["cells must be literal ARC integers 0..9"]
    return []


def _bbox(cells):
    return (
        min(row for row, _ in cells),
        min(col for _, col in cells),
        max(row for row, _ in cells),
        max(col for _, col in cells),
    )


def _intersection(first, second):
    row0, col0 = max(first[0], second[0]), max(first[1], second[1])
    row1, col1 = min(first[2], second[2]), min(first[3], second[3])
    return (row0, col0, row1, col1) if row0 <= row1 and col0 <= col1 else None


def _rect_cells(rect):
    if rect is None:
        return set()
    row0, col0, row1, col1 = rect
    return {(row, col) for row in range(row0, row1 + 1) for col in range(col0, col1 + 1)}


def _extract_facts(grid):
    height, width = len(grid), len(grid[0])
    gray_cells = [(row, col) for row in range(height) for col in range(width) if grid[row][col] == 5]
    if not gray_cells:
        return {"errors": ["at least one gray cell is required"]}
    gray_bbox = _bbox(gray_cells)
    colors = {}
    for color in _MARKER_COLORS:
        cells = [(row, col) for row in range(height) for col in range(width) if grid[row][col] == color]
        if cells:
            box = _bbox(cells)
            colors[color] = {"cells": tuple(cells), "bbox": box, "intersection": _intersection(box, gray_bbox)}
    active = tuple(color for color in sorted(colors) if colors[color]["intersection"] is not None)
    inactive = tuple(color for color in sorted(colors) if colors[color]["intersection"] is None)
    gray_area = _rect_cells(gray_bbox)
    holes = tuple(sorted(cell for cell in gray_area if grid[cell[0]][cell[1]] != 5))
    invalid_holes = tuple(cell for cell in holes if grid[cell[0]][cell[1]] in (0, 5))
    output = [[0 for _ in range(width)] for _ in range(height)]
    for row, col in gray_area:
        output[row][col] = 5
    for color in sorted(colors):
        for row, col in _rect_cells(colors[color]["intersection"]):
            output[row][col] = color
    overlaps = tuple(
        (left, right)
        for left, right in combinations(active, 2)
        if _rect_cells(colors[left]["intersection"]) & _rect_cells(colors[right]["intersection"])
    )
    return {
        "errors": [],
        "height": height,
        "width": width,
        "gray_cells": tuple(gray_cells),
        "gray_bbox": gray_bbox,
        "gray_area": gray_area,
        "gray_height": gray_bbox[2] - gray_bbox[0] + 1,
        "gray_width": gray_bbox[3] - gray_bbox[1] + 1,
        "holes": holes,
        "invalid_holes": invalid_holes,
        "colors": colors,
        "active_colors": active,
        "inactive_colors": inactive,
        "overlaps": overlaps,
        "output": output,
    }


def rule_mirror(grid):
    """Independent Python oracle for the canonical Racket transformation."""
    errors = _valid_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    facts = _extract_facts(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    return [row[:] for row in facts["output"]]


def _touches(intersection, gray_bbox):
    return frozenset(
        name
        for name, yes in (
            ("top", intersection[0] == gray_bbox[0]),
            ("left", intersection[1] == gray_bbox[1]),
            ("bottom", intersection[2] == gray_bbox[2]),
            ("right", intersection[3] == gray_bbox[3]),
        )
        if yes
    )


def _is_split_extrema(facts):
    """Recognize four non-corner markers that jointly supply all bbox extrema."""
    active, inactive = facts["active_colors"], facts["inactive_colors"]
    if len(active) != 1 or inactive:
        return False
    cells = facts["colors"][active[0]]["cells"]
    if len(cells) != 4:
        return False
    row0, col0, row1, col1 = facts["colors"][active[0]]["bbox"]
    if row1 - row0 < 2 or col1 - col0 < 2:
        return False
    cell_set = set(cells)
    corners = {(row0, col0), (row0, col1), (row1, col0), (row1, col1)}
    if cell_set & corners:
        return False
    touches_all_sides = (
        any(row == row0 for row, _ in cells)
        and any(row == row1 for row, _ in cells)
        and any(col == col0 for _, col in cells)
        and any(col == col1 for _, col in cells)
    )
    endpoint_bbox = _bbox((cells[0], cells[-1]))
    return touches_all_sides and endpoint_bbox != (row0, col0, row1, col1)


def _profile_for(grid, facts):
    public = _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid)))
    if public:
        return public
    active, inactive = facts["active_colors"], facts["inactive_colors"]
    if inactive and active:
        return "inactive_companion"
    if _is_split_extrema(facts):
        return "split_extrema"
    if len(active) >= 3 and not facts["overlaps"]:
        return "three_color_nonoverlap"
    if len(active) == 2 and facts["overlaps"]:
        return "overlap_priority"
    if len(active) != 1:
        return None
    intersection = facts["colors"][active[0]]["intersection"]
    touched = _touches(intersection, facts["gray_bbox"])
    return {
        frozenset(("top", "left")): "top_left_projection",
        frozenset(("top", "right")): "top_right_projection",
        frozenset(("bottom", "left")): "bottom_left_projection",
        frozenset(("bottom", "right")): "bottom_right_projection",
        frozenset(("left", "right")): "horizontal_band",
        frozenset(("top", "bottom")): "vertical_band",
        frozenset(): "interior_box",
        frozenset(("top", "left", "bottom", "right")): "full_bbox_projection",
    }.get(touched)


def _analysis(grid):
    errors = _valid_grid(grid)
    if errors:
        return {"errors": errors, "facts": None, "scene_profile": None, "output": None}
    facts = _extract_facts(grid)
    if facts["errors"]:
        return {"errors": facts["errors"], "facts": facts, "scene_profile": None, "output": None}
    profile = _profile_for(grid, facts)
    if facts["gray_height"] < 5 or facts["gray_width"] < 5:
        errors.append("gray bounding rectangle must be at least 5x5")
    if facts["invalid_holes"]:
        errors.append("gray bounding rectangle may be punctured only by marker colors")
    if not facts["active_colors"]:
        errors.append("at least one marker color must intersect the gray rectangle")
    if profile not in SCENE_PROFILES:
        errors.append("grid does not match a declared bbox-intersection profile")
    if facts["output"] == [list(row) for row in grid]:
        errors.append("generated lesson must visibly transform the input")
    if not any(value == 0 for row in facts["output"] for value in row):
        errors.append("output must retain zero margin outside the gray rectangle")
    for color in facts["active_colors"]:
        if len(facts["colors"][color]["cells"]) < 2:
            errors.append("active colors require at least two markers to define an extent")
        if len(_rect_cells(facts["colors"][color]["intersection"])) < 4:
            errors.append("active intersection must cover at least four cells")
    facts["scene_profile"] = profile
    return {"errors": errors, "facts": facts, "scene_profile": profile, "output": facts["output"]}


def _endpoint_only_bbox_rule(grid):
    """Plausible shortcut: infer each marker bbox from row-major endpoints only."""
    errors = _valid_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    facts = _extract_facts(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    output = [[0 for _ in row] for row in grid]
    for row, col in facts["gray_area"]:
        output[row][col] = 5
    for color in sorted(facts["colors"]):
        cells = facts["colors"][color]["cells"]
        endpoint_bbox = _bbox((cells[0], cells[-1]))
        for row, col in _rect_cells(_intersection(endpoint_bbox, facts["gray_bbox"])):
            output[row][col] = color
    return output


def _split_extrema_refutes_endpoint_only_bbox(grid):
    analysis = _analysis(grid)
    return (
        not analysis["errors"]
        and analysis["scene_profile"] == "split_extrema"
        and _endpoint_only_bbox_rule(grid) != analysis["output"]
    )


SEMANTIC_RIVALS = {"endpoint_only_bbox": _endpoint_only_bbox_rule}
SEMANTIC_WITNESSES = {
    "split_extrema_refutes_endpoint_only_bbox": _split_extrema_refutes_endpoint_only_bbox
}
WITNESS_RIVALS = {
    "split_extrema_refutes_endpoint_only_bbox": ["endpoint_only_bbox"]
}


def self_check(grid, *, difficulty=None, meta=None):
    return _analysis(grid)["errors"]


def canonical_profile_signature(grid):
    return _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid)))


def observe_overrides(grid):
    analysis = _analysis(grid)
    return {"scene_profile": analysis["scene_profile"]} if not analysis["errors"] else {}


def _dimensions(difficulty, rng):
    bands = {
        None: ((13, 22), (13, 22)),
        "easy": ((11, 15), (11, 15)),
        "medium": ((15, 21), (15, 21)),
        "hard": ((20, 29), (20, 29)),
    }
    (h0, h1), (w0, w1) = bands[difficulty]
    return rng.randint(h0, h1), rng.randint(w0, w1)


def _base_canvas(difficulty, rng):
    height, width = _dimensions(difficulty, rng)
    margin_top = rng.randint(2, min(4, height - 7))
    margin_left = rng.randint(2, min(4, width - 7))
    margin_bottom = rng.randint(2, min(4, height - margin_top - 5))
    margin_right = rng.randint(2, min(4, width - margin_left - 5))
    gray_bbox = (margin_top, margin_left, height - margin_bottom - 1, width - margin_right - 1)
    grid = [[0 for _ in range(width)] for _ in range(height)]
    for row, col in _rect_cells(gray_bbox):
        grid[row][col] = 5
    return grid, gray_bbox


def _raw_bounds_for_touch(gray_bbox, touch, rng, height, width):
    gr0, gc0, gr1, gc1 = gray_bbox
    inner_h = gr1 - gr0 + 1
    inner_w = gc1 - gc0 + 1
    row0 = gr0 if "top" in touch else rng.randint(gr0 + 1, gr0 + max(1, inner_h // 3))
    row1 = gr1 if "bottom" in touch else rng.randint(gr1 - max(1, inner_h // 3), gr1 - 1)
    col0 = gc0 if "left" in touch else rng.randint(gc0 + 1, gc0 + max(1, inner_w // 3))
    col1 = gc1 if "right" in touch else rng.randint(gc1 - max(1, inner_w // 3), gc1 - 1)
    raw_row0 = rng.randint(0, gr0) if "top" in touch else row0
    raw_row1 = rng.randint(gr1, height - 1) if "bottom" in touch else row1
    raw_col0 = rng.randint(0, gc0) if "left" in touch else col0
    raw_col1 = rng.randint(gc1, width - 1) if "right" in touch else col1
    return (raw_row0, raw_col0, raw_row1, raw_col1)


def _mark_bbox(grid, color, bounds, rng):
    row0, col0, row1, col1 = bounds
    candidates = [(row0, col0), (row1, col1), (row0, col1), (row1, col0)]
    chosen = [candidates[0], candidates[1], rng.choice(candidates[2:])]
    for row, col in set(chosen):
        grid[row][col] = color


def _single_projection(profile, difficulty, rng):
    grid, gray_bbox = _base_canvas(difficulty, rng)
    touches = {
        "top_left_projection": {"top", "left"},
        "top_right_projection": {"top", "right"},
        "bottom_left_projection": {"bottom", "left"},
        "bottom_right_projection": {"bottom", "right"},
        "horizontal_band": {"left", "right"},
        "vertical_band": {"top", "bottom"},
        "interior_box": set(),
        "full_bbox_projection": {"top", "left", "bottom", "right"},
    }[profile]
    color = rng.choice(_MARKER_COLORS)
    bounds = _raw_bounds_for_touch(gray_bbox, touches, rng, len(grid), len(grid[0]))
    _mark_bbox(grid, color, bounds, rng)
    return grid


def _split_extrema_scene(difficulty, rng):
    grid, (gr0, gc0, gr1, gc1) = _base_canvas(difficulty, rng)
    row0 = rng.randint(gr0 + 1, gr1 - 3)
    row1 = rng.randint(row0 + 2, gr1 - 1)
    col0 = rng.randint(gc0 + 1, gc1 - 3)
    col1 = rng.randint(col0 + 2, gc1 - 1)
    middle_row = rng.randint(row0 + 1, row1 - 1)
    middle_col = rng.randint(col0 + 1, col1 - 1)
    color = rng.choice(_MARKER_COLORS)
    for row, col in (
        (row0, middle_col),
        (middle_row, col0),
        (middle_row, col1),
        (row1, middle_col),
    ):
        grid[row][col] = color
    return grid


def _three_nonoverlap(difficulty, rng):
    grid, (gr0, gc0, gr1, gc1) = _base_canvas(difficulty, rng)
    colors = rng.sample(_MARKER_COLORS, 3)
    midr, midc = (gr0 + gr1) // 2, (gc0 + gc1) // 2
    rectangles = (
        (gr0, gc0, max(gr0 + 1, midr - 1), max(gc0 + 1, midc - 1)),
        (gr0, min(gc1 - 1, midc + 1), max(gr0 + 1, midr - 1), gc1),
        (min(gr1, midr + 1), gc0, gr1, max(gc0 + 2, midc)),
    )
    for color, bounds in zip(colors, rectangles):
        _mark_bbox(grid, color, bounds, rng)
    return grid


def _overlap_scene(difficulty, rng):
    grid, (gr0, gc0, gr1, gc1) = _base_canvas(difficulty, rng)
    low, high = sorted(rng.sample(_MARKER_COLORS, 2))
    midr, midc = (gr0 + gr1) // 2, (gc0 + gc1) // 2
    first = (gr0 + 1, gc0 + 1, min(gr1 - 1, midr + 2), min(gc1 - 1, midc + 2))
    second = (max(gr0 + 1, midr - 1), max(gc0 + 1, midc - 1), gr1 - 1, gc1 - 1)
    _mark_bbox(grid, low, first, rng)
    _mark_bbox(grid, high, second, rng)
    return grid


def _inactive_scene(difficulty, rng):
    grid, gray_bbox = _base_canvas(difficulty, rng)
    active, inactive = rng.sample(_MARKER_COLORS, 2)
    bounds = _raw_bounds_for_touch(gray_bbox, {"top", "left"}, rng, len(grid), len(grid[0]))
    _mark_bbox(grid, active, bounds, rng)
    gr0, gc0, _, gc1 = gray_bbox
    row = rng.randint(0, gr0 - 1)
    col0 = rng.randint(gc0, max(gc0, gc1 - 2))
    grid[row][col0] = inactive
    grid[row][min(len(grid[0]) - 1, col0 + 2)] = inactive
    return grid


def _candidate_scene(difficulty, profile, rng):
    if profile in {
        "top_left_projection", "top_right_projection", "bottom_left_projection", "bottom_right_projection",
        "horizontal_band", "vertical_band", "interior_box", "full_bbox_projection",
    }:
        return _single_projection(profile, difficulty, rng)
    if profile == "split_extrema":
        return _split_extrema_scene(difficulty, rng)
    if profile == "three_color_nonoverlap":
        return _three_nonoverlap(difficulty, rng)
    if profile == "overlap_priority":
        return _overlap_scene(difficulty, rng)
    if profile == "inactive_companion":
        return _inactive_scene(difficulty, rng)
    raise ValueError(f"unknown scene_profile: {profile!r}")


def _general_scene(difficulty, profile, rng):
    for _ in range(200):
        grid = _candidate_scene(difficulty, profile, rng)
        analysis = _analysis(grid)
        if not analysis["errors"] and analysis["scene_profile"] == profile:
            return grid
    raise AssertionError(f"could not construct {profile}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer (not bool)")
    if sample_index < 0:
        raise ValueError("sample_index must be non-negative")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - {"scene_profile"})
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION, task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    weighted = (
        # Keep canonical 15x15 lessons above the strict 25% profile-envelope
        # floor after adding split_extrema to the default curriculum.
        PUBLIC_PROFILES * 7
        + ("top_left_projection", "top_right_projection", "bottom_left_projection", "bottom_right_projection") * 5
        + ("horizontal_band", "vertical_band", "interior_box") * 5
        + ("split_extrema",) * 8
        + ("three_color_nonoverlap",) * 9
        + ("overlap_priority",) * 8
        + ("inactive_companion",) * 5
        + ("full_bbox_projection",) * 2
    )
    profile = ctx.draw_choice("scene_profile", weighted)
    if profile not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {profile!r}")
    if profile in PUBLIC_PROFILES:
        return [row[:] for row in _PUBLIC_INPUTS[profile]]
    return _general_scene(difficulty, profile, ctx.draw_rng("scene"))
