"""Semantic generator for ARC task 888fb4310749 (source fd4b2b02).

The nonzero input bounding box defines a rectangular source block.  With
period ``block_height + block_width``, stamp same-orientation copies in the
source color along both diagonals and adjacent quarter-turned copies in the
complementary color ``9 - source_color``.  Rectangles that only partly
intersect the canvas are clipped, and same-orientation stamps are applied last.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "888fb4310749"
TASK_ID = "888fb4310749"
VERSION = "3.0.0"
RULE_HASH = "2e44fadee3f2"
SUMMARY = "Tile both diagonal periods with source-color blocks and adjacent rotated 9-minus-color blocks, clipping at the canvas."
INVARIANTS = [
    "the calibrated input contains one solid monochromatic nonzero rectangle on black",
    "the period equals source height plus source width",
    "same-orientation diagonal stamps use the source color and are applied last",
    "adjacent quarter-turned stamps swap height/width and use color 9 minus source color",
    "every stamp that intersects the canvas is drawn with out-of-bounds cells clipped",
]

PUBLIC_PROFILES = ("public_1", "public_2", "public_3", "public_4")
GENERAL_PROFILES = (
    "horizontal_bar",
    "vertical_bar",
    "square_block",
    "corner_anchor",
    "edge_anchor",
    "wide_block",
    "tall_block",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "official-family and eight shape/anchor/rotation contrasts",
        "valid": "|".join(SCENE_PROFILES),
    }
}


def _rect_grid(height, width, row0, col0, block_height, block_width, color):
    grid = [[0] * width for _ in range(height)]
    for row in range(row0, row0 + block_height):
        for col in range(col0, col0 + block_width):
            grid[row][col] = color
    return grid


_PUBLIC_INPUTS = {
    "public_1": _rect_grid(16, 16, 7, 7, 1, 3, 3),
    "public_2": _rect_grid(23, 23, 5, 6, 4, 2, 6),
    "public_3": _rect_grid(26, 26, 5, 11, 5, 2, 3),
    "public_4": _rect_grid(16, 16, 7, 5, 2, 1, 6),
}
_PUBLIC_SIGNATURES = {tuple(map(tuple, grid)): name for name, grid in _PUBLIC_INPUTS.items()}


def _valid_grid(grid):
    if not isinstance(grid, (list, tuple)) or not 5 <= len(grid) <= 30:
        return ["input must contain five through thirty rows"]
    if not isinstance(grid[0], (list, tuple)) or not 5 <= len(grid[0]) <= 30:
        return ["input must contain five through thirty columns"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["input must be rectangular"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["input cells must be literal ARC color integers from zero through nine"]
    return []


def _rule_facts(grid):
    cells = [(row, col) for row, values in enumerate(grid) for col, value in enumerate(values) if value != 0]
    if not cells:
        raise ValueError("the executable rule requires at least one nonzero cell")
    row0, row1 = min(row for row, _ in cells), max(row for row, _ in cells)
    col0, col1 = min(col for _, col in cells), max(col for _, col in cells)
    block_height, block_width = row1 - row0 + 1, col1 - col0 + 1
    color = grid[row0][col0]
    return {
        "row0": row0,
        "row1": row1,
        "col0": col0,
        "col1": col1,
        "block_height": block_height,
        "block_width": block_width,
        "block_area": block_height * block_width,
        "nonzero_count": len(cells),
        "color": color,
        "alt_color": 9 - color,
        "step": block_height + block_width,
    }


def _intersects(row0, col0, block_height, block_width, height, width):
    return row0 <= height - 1 and row0 + block_height - 1 >= 0 and col0 <= width - 1 and col0 + block_width - 1 >= 0


def _stamp(grid, row0, col0, block_height, block_width, color):
    height, width = len(grid), len(grid[0])
    for row in range(row0, row0 + block_height):
        for col in range(col0, col0 + block_width):
            if 0 <= row < height and 0 <= col < width:
                grid[row][col] = color


def rule_mirror(grid):
    """Exact Python mirror of the broad executable Racket program."""
    errors = _valid_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    facts = _rule_facts(grid)
    height, width = len(grid), len(grid[0])
    row0, col0 = facts["row0"], facts["col0"]
    block_height, block_width, step = facts["block_height"], facts["block_width"], facts["step"]
    output = [list(row) for row in grid]

    for multiple in range(-40, 41):
        for sign in (1, -1):
            diagonal_row = row0 + multiple * step
            diagonal_col = col0 + sign * multiple * step
            rotated_row = diagonal_row + block_height
            rotated_col = diagonal_col + (block_width if sign == 1 else -block_height)
            if _intersects(rotated_row, rotated_col, block_width, block_height, height, width):
                _stamp(output, rotated_row, rotated_col, block_width, block_height, facts["alt_color"])

    same_anchors = []
    for multiple in range(-40, 41):
        for sign in (1, -1):
            anchor = row0 + multiple * step, col0 + sign * multiple * step
            if _intersects(anchor[0], anchor[1], block_height, block_width, height, width) and anchor not in same_anchors:
                same_anchors.append(anchor)
    for anchor_row, anchor_col in same_anchors:
        _stamp(output, anchor_row, anchor_col, block_height, block_width, facts["color"])
    return output


def _strict_facts(grid):
    errors = _valid_grid(grid)
    if errors:
        return errors, None
    try:
        facts = _rule_facts(grid)
    except ValueError as exc:
        return [str(exc)], None
    height, width = len(grid), len(grid[0])
    color = facts["color"]
    if color not in range(1, 9):
        errors.append("source rectangle color must be one through eight")
    if facts["block_height"] > 8 or facts["block_width"] > 8:
        errors.append("calibrated source sides must contain at most eight cells")
    if facts["block_area"] < 2:
        errors.append("calibrated sources must contain at least two cells")
    if min(facts["block_height"], facts["block_width"]) == 1 and max(facts["block_height"], facts["block_width"]) > 3:
        errors.append("calibrated one-cell bars are limited to lengths two and three")
    if facts["block_height"] == facts["block_width"] == 2:
        errors.append("calibrated square sources begin at side length three")
    expected = {
        (row, col)
        for row in range(facts["row0"], facts["row1"] + 1)
        for col in range(facts["col0"], facts["col1"] + 1)
    }
    actual = {(row, col) for row, values in enumerate(grid) for col, value in enumerate(values) if value != 0}
    if actual != expected or any(grid[row][col] != color for row, col in expected):
        errors.append("all nonzero cells must form one solid monochromatic bounding rectangle")
    if facts["block_area"] == height * width:
        errors.append("the source rectangle must leave visible black background")
    facts.update(
        {
            "height": height,
            "width": width,
            "touch_top": facts["row0"] == 0,
            "touch_bottom": facts["row1"] == height - 1,
            "touch_left": facts["col0"] == 0,
            "touch_right": facts["col1"] == width - 1,
        }
    )
    facts["edge_count"] = sum(facts[name] for name in ("touch_top", "touch_bottom", "touch_left", "touch_right"))
    facts["corner_anchor"] = facts["edge_count"] == 2
    return errors, facts


def _public_family_key(grid):
    errors, facts = _strict_facts(grid)
    if errors:
        return None
    return min(facts["block_height"], facts["block_width"]), max(facts["block_height"], facts["block_width"]), facts["color"]


_PUBLIC_FAMILIES = {_public_family_key(grid): profile for profile, grid in _PUBLIC_INPUTS.items()}


def canonical_profile_signature(grid):
    try:
        signature = tuple(tuple(row) for row in grid)
    except TypeError:
        return None
    return _PUBLIC_SIGNATURES.get(signature)


def canonical_family_signature(grid):
    return _PUBLIC_FAMILIES.get(_public_family_key(grid))


def _general_profile(facts):
    block_height, block_width = facts["block_height"], facts["block_width"]
    if block_height == 1:
        return "horizontal_bar"
    if block_width == 1:
        return "vertical_bar"
    if block_height == block_width:
        return "square_block"
    if facts["corner_anchor"]:
        return "corner_anchor"
    if facts["edge_count"]:
        return "edge_anchor"
    return "wide_block" if block_width > block_height else "tall_block"


def _analysis(grid):
    errors, facts = _strict_facts(grid)
    if errors:
        return {"errors": errors, "scene_profile": None, "facts": facts, "output": None}
    profile = canonical_profile_signature(grid)
    if profile is None:
        profile = canonical_family_signature(grid)
    if profile is None:
        profile = _general_profile(facts)
    if profile not in SCENE_PROFILES:
        errors.append("grid does not match a declared block geometry or anchor profile")
    output = None if errors else rule_mirror(grid)
    if output is not None:
        if output == [list(row) for row in grid]:
            errors.append("the periodic stamping rule must visibly change every lesson")
        facts["source_color_cells"] = sum(value == facts["color"] for row in output for value in row)
        facts["alt_color_cells"] = sum(value == facts["alt_color"] for row in output for value in row)
        if not facts["source_color_cells"] or not facts["alt_color_cells"]:
            errors.append("both source and complementary stamp colors must be visible")
    return {"errors": errors, "scene_profile": profile, "facts": facts, "output": None if errors else output}


def self_check(grid, *, difficulty=None, meta=None):
    return _analysis(grid)["errors"]


def observe_overrides(grid):
    analysis = _analysis(grid)
    return {"scene_profile": analysis["scene_profile"]} if not analysis["errors"] else {}


def _limits(difficulty):
    if difficulty == "easy":
        return 10, 15
    if difficulty == "medium":
        return 16, 22
    if difficulty == "hard":
        return 23, 30
    return 14, 26


def _unequal_dims(height, width, rng, orientation=None):
    for _ in range(100):
        block_height = rng.randint(2, min(7, height - 2))
        block_width = rng.randint(2, min(7, width - 2))
        if block_height == block_width:
            continue
        if orientation == "wide" and block_width <= block_height:
            continue
        if orientation == "tall" and block_height <= block_width:
            continue
        return block_height, block_width
    raise AssertionError("could not choose unequal block dimensions")


def _shape_for_profile(profile, height, width, rng):
    if profile == "horizontal_bar":
        return 1, rng.randint(2, 3)
    if profile == "vertical_bar":
        return rng.randint(2, 3), 1
    if profile == "square_block":
        side = rng.randint(3, min(6, height - 2, width - 2))
        return side, side
    if profile == "wide_block":
        return _unequal_dims(height, width, rng, "wide")
    if profile == "tall_block":
        return _unequal_dims(height, width, rng, "tall")
    if profile in ("corner_anchor", "edge_anchor"):
        return _unequal_dims(height, width, rng)
    raise ValueError(f"unknown scene_profile: {profile!r}")


def _anchor_for_profile(profile, height, width, block_height, block_width, rng):
    if profile == "corner_anchor":
        return rng.choice((0, height - block_height)), rng.choice((0, width - block_width))
    if profile == "edge_anchor":
        side = rng.choice(("top", "bottom", "left", "right"))
        if side in ("top", "bottom"):
            return (0 if side == "top" else height - block_height), rng.randint(1, width - block_width - 1)
        return rng.randint(1, height - block_height - 1), (0 if side == "left" else width - block_width)
    if profile in ("wide_block", "tall_block"):
        return rng.randint(1, height - block_height - 1), rng.randint(1, width - block_width - 1)
    return rng.randint(0, height - block_height), rng.randint(0, width - block_width)


def _general_scene_once(profile, difficulty, rng):
    low, high = _limits(difficulty)
    height, width = rng.randint(low, high), rng.randint(low, high)
    block_height, block_width = _shape_for_profile(profile, height, width, rng)
    row0, col0 = _anchor_for_profile(profile, height, width, block_height, block_width, rng)
    color = rng.choice((3, 3, 3, 6, 6, 6, 1, 2, 4, 5, 7, 8))
    return _rect_grid(height, width, row0, col0, block_height, block_width, color)


def _general_scene(profile, difficulty, rng):
    for _ in range(160):
        try:
            grid = _general_scene_once(profile, difficulty, rng)
        except (AssertionError, ValueError):
            continue
        analysis = _analysis(grid)
        if not analysis["errors"] and analysis["scene_profile"] == profile:
            return grid
    raise AssertionError(f"could not construct periodic-block profile {profile!r}")


def _public_nuisance(profile, difficulty, rng):
    source = _PUBLIC_INPUTS[profile]
    _, source_facts = _strict_facts(source)
    block_height, block_width = source_facts["block_height"], source_facts["block_width"]
    if rng.choice((False, True)):
        block_height, block_width = block_width, block_height
    low, high = _limits(difficulty)
    minimum = max(low, block_height + 2, block_width + 2)
    height, width = rng.randint(minimum, max(high, minimum)), rng.randint(minimum, max(high, minimum))
    row0, col0 = rng.randint(0, height - block_height), rng.randint(0, width - block_width)
    grid = _rect_grid(height, width, row0, col0, block_height, block_width, source_facts["color"])
    analysis = _analysis(grid)
    if analysis["errors"] or analysis["scene_profile"] != profile:
        raise AssertionError(f"invalid public-family nuisance for {profile!r}")
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
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
    public_prior = PUBLIC_PROFILES * 2
    general_prior = (
        ("horizontal_bar",) * 4
        + ("vertical_bar",) * 4
        + ("square_block",) * 3
        + ("corner_anchor",) * 3
        + ("edge_anchor",) * 4
        + ("wide_block",) * 6
        + ("tall_block",) * 6
    )
    profile = ctx.draw_choice("scene_profile", public_prior + general_prior)
    if profile not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {profile!r}")
    if profile in PUBLIC_PROFILES:
        if overrides.get("scene_profile") is not None:
            return [row[:] for row in _PUBLIC_INPUTS[profile]]
        grid = _public_nuisance(profile, difficulty, ctx.draw_rng("public_nuisance"))
    else:
        grid = _general_scene(profile, difficulty, ctx.draw_rng("scene"))
    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid periodic-block lesson: " + "; ".join(errors))
    return grid
