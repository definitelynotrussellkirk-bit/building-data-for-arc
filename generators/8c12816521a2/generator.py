"""Semantic generator for ARC task 8c12816521a2 (source 05a7bcf2).

A complete cyan separator row or column divides yellow markers from a red
shape.  Normalize a horizontal separator by transposition.  In every lane
that contains yellow on the globally selected yellow side, recolor the
original yellow cells green, extend yellow toward the separator, extend cyan
through the opposite side, and rebuild the same number of red cells flush
with the far edge.  Lanes without selected-side yellow remain unchanged.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "8c12816521a2"
TASK_ID = "8c12816521a2"
VERSION = "3.0.1"
RULE_HASH = "bdca6d13f74f"
SUMMARY = "Recolor yellow tips green and extend yellow/cyan/red bands across a full separator in triggered lanes."

INVARIANTS = [
    "exactly one full cyan row or column is the separator",
    "all yellow cells lie on one selected side of the separator",
    "all red cells form one connected shape on the opposite side",
    "only lanes containing selected-side yellow are transformed",
    "red cells are counted per triggered lane and rebuilt flush with the far edge",
]

PUBLIC_PROFILES = ("public_1", "public_2", "public_3", "public_4")
GENERAL_PROFILES = (
    "vertical_left",
    "vertical_right",
    "horizontal_above",
    "horizontal_below",
    "multi_yellow",
    "deep_yellow",
    "near_edge_separator",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "official-family and seven orientation/side/component contrasts",
        "valid": "|".join(SCENE_PROFILES),
    }
}


_PUBLIC_ROWS = {
    "public_1": (
        "000000000800000000002000000000", "000000000800000000022000000000",
        "000000000800000000222000000000", "000000000800000000022000000000",
        "004400000800000000002000000000", "004400000800000000002000000000",
        "000000000800000000222000000000", "000000000800000000022000000000",
        "000000000800000002222000000000", "000000000800000000222000000000",
        "000000000800000000002000000000", "004000000800000000022000000000",
        "004000000800000000222000000000", "000000000800000000022000000000",
        "000000000800000000002000000000", "000000000800000000022000000000",
        "000000000800000000002000000000", "000000000800000000002000000000",
        "000044000800000000022000000000", "000044000800000000222000000000",
        "000004000800000000222000000000", "000000000800000000002000000000",
        "000000000800000000002000000000", "000000000800000000022000000000",
        "000000000800000000002000000000", "000440000800000000022000000000",
        "000000000800000000002000000000", "000000000800000000022000000000",
        "000000000800000000022000000000", "000000000800000000002000000000",
    ),
    "public_2": (
        "000000000000000000000000000000", "000000000000000000000000000000",
        "000000000000000000000000000000", "000000000040000004440000000000",
        "000000000440000004440000000000", "000440000000000000000000440000",
        "000000000000000000000000440000", "000000000000000000000004440000",
        "000000000000000000000000000000", "000000000000000000000000000000",
        "888888888888888888888888888888", "000000000000000000000000000000",
        "000000000000000000000000000000", "000000000000000000000000000000",
        "000000000000000000000000000000", "000000000000000000000000000000",
        "000000000000000000000000000000", "000000000000000000000000000000",
        "000000000000000000000000000000", "000000000000020000000022000000",
        "200220020200220002020022200200", "222222222222222222222222222222",
        "000000000000000000000000000000", "000000000000000000000000000000",
        "000000000000000000000000000000", "000000000000000000000000000000",
        "000000000000000000000000000000", "000000000000000000000000000000",
        "000000000000000000000000000000", "000000000000000000000000000000",
    ),
    "public_3": (
        "000000000000000000000000000000", "000000000000000000000000000000",
        "000000444440000000000000000000", "000000000000000000000000000000",
        "000000000000000044440000044000", "000000000000000044440000000000",
        "000000000000000000000000000000", "000000000000000000000000000000",
        "000000000000000000000000000000", "888888888888888888888888888888",
        "000000000000000000000000000000", "000000000000000000000000000000",
        "000000000000000000000000000000", "000000000000000000000000000000",
        "000000000000000000000000000000", "000000000000000000000000000000",
        "000000000000000000000000000000", "000000000000000000000000000000",
        "000000000000000000000000000000", "000000002200000200000000000000",
        "000000022200000220000000000000", "002202222220202220202202022000",
        "222222222222222222222222222222", "000000000000000000000000000000",
        "000000000000000000000000000000", "000000000000000000000000000000",
        "000000000000000000000000000000", "000000000000000000000000000000",
        "000000000000000000000000000000", "000000000000000000000000000000",
    ),
    "public_4": (
        "000000000020000000080000000000", "000000000022200000080000044000",
        "000000000022000000080000044000", "000000000022000000080000044400",
        "000000000022200000080000000000", "000000000022000000080000000000",
        "000000000022222000080000000000", "000000000022220000080000000000",
        "000000000020000000080000000000", "000000000020000000080000000000",
        "000000000022200000080000440000", "000000000022000000080000440000",
        "000000000020000000080000440000", "000000000022200000080000440000",
        "000000000022220000080000400000", "000000000022000000080000400000",
        "000000000020000000080000000000", "000000000022000000080000000000",
        "000000000020000000080000000000", "000000000022000000080000000000",
        "000000000022200000080000400000", "000000000022222000080000400000",
        "000000000022000000080000400000", "000000000022200000080000400000",
        "000000000022220000080000000000", "000000000022000000080000000000",
        "000000000022000000080000000004", "000000000022200000080000040000",
        "000000000022200000080000000000", "000000000020000000080000000000",
    ),
}
_PUBLIC_INPUTS = {name: [[int(value) for value in row] for row in rows] for name, rows in _PUBLIC_ROWS.items()}
_PUBLIC_SIGNATURES = {tuple(map(tuple, grid)): name for name, grid in _PUBLIC_INPUTS.items()}
_PUBLIC_FAMILIES = {
    ("vertical", "left", 4): "public_1",
    ("horizontal", "above", 4): "public_2",
    ("horizontal", "above", 3): "public_3",
    ("vertical", "right", 5): "public_4",
}


def _transpose(grid):
    return [list(row) for row in zip(*grid)]


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
        for row in grid for value in row
    ):
        return ["input cells must be literal ARC color integers from zero through nine"]
    return []


def _normalize(grid):
    height, width = len(grid), len(grid[0])
    horizontal_rows = [row for row in range(height) if all(grid[row][col] == 8 for col in range(width))]
    is_horizontal = bool(horizontal_rows)
    normalized = _transpose(grid) if is_horizontal else [list(row) for row in grid]
    nheight, nwidth = len(normalized), len(normalized[0])
    columns = [col for col in range(nwidth) if all(normalized[row][col] == 8 for row in range(nheight))]
    if not columns:
        raise ValueError("the executable rule requires a complete cyan separator row or column")
    return normalized, is_horizontal, columns[0]


def rule_mirror(grid):
    """Exact Python mirror of the broad executable canonical Racket rule."""
    errors = _valid_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    normalized, is_horizontal, separator = _normalize(grid)
    height, width = len(normalized), len(normalized[0])
    left_yellow = sum(normalized[row][col] == 4 for row in range(height) for col in range(separator))
    right_yellow = sum(normalized[row][col] == 4 for row in range(height) for col in range(separator + 1, width))
    yellow_left = left_yellow > right_yellow
    result = []
    for row in range(height):
        yellow_range = range(separator) if yellow_left else range(separator + 1, width)
        red_range = range(separator + 1, width) if yellow_left else range(separator)
        yellow_cells = [col for col in yellow_range if normalized[row][col] == 4]
        red_count = sum(normalized[row][col] == 2 for col in red_range)
        if not yellow_cells:
            result.append(list(normalized[row]))
            continue
        values = []
        for col, value in enumerate(normalized[row]):
            if value == 4:
                new_value = 3
            elif col == separator:
                new_value = 8
            elif yellow_left and col < separator and col > yellow_cells[-1]:
                new_value = 4
            elif not yellow_left and col > separator and col < yellow_cells[0]:
                new_value = 4
            elif yellow_left and col > separator and col < width - red_count:
                new_value = 8
            elif not yellow_left and col < separator and col >= red_count:
                new_value = 8
            elif yellow_left and col >= width - red_count:
                new_value = 2
            elif not yellow_left and col < red_count:
                new_value = 2
            else:
                new_value = value
            values.append(new_value)
        result.append(values)
    return _transpose(result) if is_horizontal else result


def _components(grid, color):
    points = {(row, col) for row, values in enumerate(grid) for col, value in enumerate(values) if value == color}
    components = []
    while points:
        todo = [points.pop()]
        component = []
        while todo:
            row, col = todo.pop()
            component.append((row, col))
            for neighbor in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
                if neighbor in points:
                    points.remove(neighbor)
                    todo.append(neighbor)
        components.append(component)
    return components


def _strict_facts(grid):
    errors = _valid_grid(grid)
    if errors:
        return errors, None
    height, width = len(grid), len(grid[0])
    values = {value for row in grid for value in row}
    if not values <= {0, 2, 4, 8}:
        errors.append("calibrated inputs use only black, red, yellow, and cyan")
    full_rows = [row for row in range(height) if all(grid[row][col] == 8 for col in range(width))]
    full_cols = [col for col in range(width) if all(grid[row][col] == 8 for row in range(height))]
    if len(full_rows) + len(full_cols) != 1:
        errors.append("calibrated inputs require exactly one full cyan separator row or column")
        return errors, None
    normalized, is_horizontal, separator = _normalize(grid)
    nheight, nwidth = len(normalized), len(normalized[0])
    if separator < 2 or separator > nwidth - 3:
        errors.append("separator must leave at least two cells on each side")
    left_yellow = [(row, col) for row in range(nheight) for col in range(separator) if normalized[row][col] == 4]
    right_yellow = [(row, col) for row in range(nheight) for col in range(separator + 1, nwidth) if normalized[row][col] == 4]
    if bool(left_yellow) == bool(right_yellow):
        errors.append("all yellow cells must occupy exactly one side of the separator")
    yellow_left = bool(left_yellow) and not right_yellow
    selected_yellow = left_yellow if yellow_left else right_yellow
    left_red = [(row, col) for row in range(nheight) for col in range(separator) if normalized[row][col] == 2]
    right_red = [(row, col) for row in range(nheight) for col in range(separator + 1, nwidth) if normalized[row][col] == 2]
    selected_red = right_red if yellow_left else left_red
    wrong_red = left_red if yellow_left else right_red
    if not selected_red or wrong_red:
        errors.append("all red cells must occupy the side opposite the yellow cells")
    yellow_components = _components(grid, 4)
    red_components = _components(grid, 2)
    if not 1 <= len(yellow_components) <= 5:
        errors.append("calibrated yellow markers form one through five components")
    if len(red_components) != 1:
        errors.append("calibrated red cells must form one connected component")
    trigger_lanes = len({row for row, _ in selected_yellow})
    facts = {
        "height": height,
        "width": width,
        "orientation": "horizontal" if is_horizontal else "vertical",
        "separator": separator,
        "normalized_width": nwidth,
        "yellow_side": ("above" if yellow_left else "below") if is_horizontal else ("left" if yellow_left else "right"),
        "yellow_left": yellow_left,
        "yellow_count": len(selected_yellow),
        "yellow_components": len(yellow_components),
        "red_count": len(selected_red),
        "trigger_lanes": trigger_lanes,
        "near_edge": min(separator, nwidth - separator - 1) <= 4,
    }
    if not selected_yellow or trigger_lanes == 0:
        errors.append("at least one selected-side yellow trigger is required")
    if not errors:
        output = rule_mirror(grid)
        if output == [list(row) for row in grid]:
            errors.append("calibrated inputs must produce a visible transformation")
    return errors, facts


def canonical_profile_signature(grid):
    return _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid)))


def _profile_from_facts(facts):
    family = _PUBLIC_FAMILIES.get((facts["orientation"], facts["yellow_side"], facts["yellow_components"]))
    if family:
        return family
    if facts["near_edge"]:
        return "near_edge_separator"
    if facts["yellow_components"] == 2:
        return "multi_yellow"
    if facts["yellow_components"] == 1 and facts["trigger_lanes"] * 2 >= facts["height"]:
        return "deep_yellow"
    return {
        ("vertical", "left"): "vertical_left",
        ("vertical", "right"): "vertical_right",
        ("horizontal", "above"): "horizontal_above",
        ("horizontal", "below"): "horizontal_below",
    }[(facts["orientation"], facts["yellow_side"])]


def _analysis(grid):
    errors, facts = _strict_facts(grid)
    profile = None if errors else canonical_profile_signature(grid) or _profile_from_facts(facts)
    return {"errors": errors, "facts": facts, "scene_profile": profile, "output": None if errors else rule_mirror(grid)}


def canonical_family_signature(grid):
    analysis = _analysis(grid)
    return analysis["scene_profile"] if analysis["scene_profile"] in PUBLIC_PROFILES else None


def observe_overrides(grid):
    analysis = _analysis(grid)
    return {} if analysis["errors"] else {"scene_profile": analysis["scene_profile"]}


def self_check(grid, *, difficulty=None, meta=None):
    analysis = _analysis(grid)
    errors = list(analysis["errors"])
    expected = (meta or {}).get("scene_profile")
    if expected in SCENE_PROFILES and not errors and analysis["scene_profile"] != expected:
        errors.append(f"scene_profile requested {expected!r}, observed {analysis['scene_profile']!r}")
    return errors


def _band_bounds(difficulty):
    return {
        None: (18, 30),
        "easy": (15, 18),
        "medium": (19, 24),
        "hard": (25, 30),
    }[difficulty]


def _component_spans(rng, height, count, trigger_rows):
    heights = [1] * count
    for _ in range(trigger_rows - count):
        heights[rng.randrange(count)] += 1
    occupied = sum(heights) + count - 1
    start = rng.randint(1, height - occupied - 1)
    spans = []
    for component_height in heights:
        spans.append((start, component_height))
        start += component_height + 1
    return spans


def _make_normalized(rng, height, width, *, yellow_left, component_count, deep=False, near_edge=False):
    if near_edge:
        separator = 4 if yellow_left else width - 5
    else:
        low = max(5, width // 4)
        high = min(width - 6, (3 * width) // 4)
        separator = rng.randint(low, high)
    grid = [[0] * width for _ in range(height)]
    for row in range(height):
        grid[row][separator] = 8

    if yellow_left:
        red_spine = rng.randint(separator + 2, width - 2)
        for row in range(height):
            length = rng.randint(1, min(5, width - red_spine))
            for col in range(red_spine, red_spine + length):
                grid[row][col] = 2
    else:
        red_spine = rng.randint(1, separator - 2)
        for row in range(height):
            length = rng.randint(1, min(5, red_spine + 1))
            for col in range(red_spine - length + 1, red_spine + 1):
                grid[row][col] = 2

    trigger_rows = max(component_count, (height + (1 if deep else 3)) // (2 if deep else 4))
    spans = _component_spans(rng, height, component_count, trigger_rows)
    for start_row, component_height in spans:
        available = separator if yellow_left else width - separator - 1
        minimum = 2 if component_count == 1 else 1
        run_width = rng.randint(minimum, min(4, available - 1))
        if yellow_left:
            end = rng.randint(run_width - 1, separator - 1)
            start = end - run_width + 1
        else:
            start = rng.randint(separator + 1, width - run_width)
            end = start + run_width - 1
        for row in range(start_row, start_row + component_height):
            for col in range(start, end + 1):
                grid[row][col] = 4
    return grid


def _profile_spec(profile):
    return {
        "public_1": ("vertical", True, 4, False, False),
        "public_2": ("horizontal", True, 4, False, False),
        "public_3": ("horizontal", True, 3, False, False),
        "public_4": ("vertical", False, 5, False, False),
        "vertical_left": ("vertical", True, 1, False, False),
        "vertical_right": ("vertical", False, 1, False, False),
        "horizontal_above": ("horizontal", True, 1, False, False),
        "horizontal_below": ("horizontal", False, 1, False, False),
        "multi_yellow": ("vertical", True, 2, False, False),
        "deep_yellow": ("vertical", True, 1, True, False),
        "near_edge_separator": ("vertical", True, 1, False, True),
    }[profile]


def _make_scene(profile, difficulty, rng):
    orientation, yellow_first, component_count, deep, near_edge = _profile_spec(profile)
    low, high = _band_bounds(difficulty)
    original_height = rng.randint(low, high)
    original_width = rng.randint(low, high)
    normalized_height, normalized_width = (original_width, original_height) if orientation == "horizontal" else (original_height, original_width)
    normalized = _make_normalized(
        rng,
        normalized_height,
        normalized_width,
        yellow_left=yellow_first,
        component_count=component_count,
        deep=deep,
        near_edge=near_edge,
    )
    return _transpose(normalized) if orientation == "horizontal" else normalized


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unsupported difficulty {difficulty!r}")
    unknown = set(overrides) - {"scene_profile"}
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(sorted(unknown))}")
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = ctx.draw_choice("scene_profile", list(SCENE_PROFILES))
    if "scene_profile" in overrides and profile in PUBLIC_PROFILES:
        return [row[:] for row in _PUBLIC_INPUTS[profile]]
    grid = _make_scene(profile, difficulty, ctx.draw_rng("scene"))
    errors = self_check(grid, difficulty=difficulty, meta={"scene_profile": profile})
    if errors:
        raise AssertionError("generated invalid scene: " + "; ".join(errors))
    return grid
