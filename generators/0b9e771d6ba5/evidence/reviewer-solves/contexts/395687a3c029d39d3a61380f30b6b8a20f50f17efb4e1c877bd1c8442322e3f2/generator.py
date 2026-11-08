"""Semantic generator for ARC task 0b9e771d6ba5.

The rule first restores color bounding boxes that contain foreign foreground
but no background.  It then lets wholly collinear colors repaint original
non-background cells along their spans.  Both passes process colors 1..9 in
ascending order, so later line colors overwrite rectangle restorations and
lower-colored lines.
"""
from __future__ import annotations

from collections import Counter

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "0b9e771d6ba5"
TASK_ID = "0b9e771d6ba5"
VERSION = "4.3.0"
RULE_HASH = "654b94529e3a"
SUMMARY = "Restore foreground-only impure color bboxes, then repaint original non-background cells along complete horizontal, vertical, or diagonal color spans in ascending color order."
INVARIANTS = [
    "the unique modal color is background and foreground uses only colors 1..9 other than that mode",
    "a color bbox restores only when it contains foreign foreground and no background",
    "rectangle eligibility and all line paths are computed from the original input",
    "every cell of a line color must be collinear horizontally, vertically, or on one diagonal",
    "line spans repaint only cells that were non-background in the original input",
    "rectangle fills run in ascending color order, followed by ascending line-color order",
]

PUBLIC_PROFILES = tuple(f"public_{index}" for index in range(1, 5))
GENERAL_PROFILES = (
    "rect_impurity",
    "rect_occlusion",
    "rect_priority",
    "horizontal_bridge",
    "vertical_bridge",
    "diag_down_bridge",
    "diag_up_bridge",
    "background_gap_stays",
    "off_line_decoy_disables",
    "disconnected_bbox_blocks_fill",
    "multiple_lines_priority",
    "line_over_restoration",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
INERT_DECOY_COLORS = 2
INERT_COMPONENTS_PER_COLOR = 3
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "four exact-public and twelve observable restoration/line lessons",
        "valid": "public_1|public_2|public_3|public_4|rect_impurity|rect_occlusion|rect_priority|horizontal_bridge|vertical_bridge|diag_down_bridge|diag_up_bridge|background_gap_stays|off_line_decoy_disables|disconnected_bbox_blocks_fill|multiple_lines_priority|line_over_restoration",
    }
}

_PUBLIC_ROWS = (
    "7777777777777777/7777777777777777/7777777777777777/7777777777777777/7777777444477777/7777777444477777/7777111114477777/7777111114477777/7777111114477777/7777111114477777/7777111117777777/7777111117777777/7777111117777777/7777777777777777/7777777777777777/7777777777777777",
    "7777777777777777/7777777777777777/7777757777777777/7777757777777777/7777757777777777/7777757777777777/7777757777777777/7799959999997777/7777757777777777/7777757777777777/7777757777777777/7777757777777777/7777757777777777/7777777777777777/7777777777777777/7777777777777777",
    "7777777777777777/7777777777777777/7755778877666677/7755778877666677/7955998899666697/7955998899666697/7755778877666677/7755778877666677/7755778877666677/1155118811666611/1155118811666611/1155118811666611/7755778877666677/7755778877666677/7777777777777777/7777777777777777",
    "7777777777777777/3777777777777777/7377777777777777/7737777777787777/7773777777887222/7777377778888222/7777737788888222/7777773888888822/7777778888888822/7777788888888887/7777888888888887/7777777777377777/7777777777737777/7777777777773777/7777777777777377/7777777777777737",
)


def _decode(text):
    return [[int(value) for value in row] for row in text.split("/")]


_PUBLIC_INPUTS = {name: _decode(text) for name, text in zip(PUBLIC_PROFILES, _PUBLIC_ROWS)}
_PUBLIC_SIGNATURES = {tuple(map(tuple, grid)): name for name, grid in _PUBLIC_INPUTS.items()}


def _valid_grid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be non-empty"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if len(grid) > 30 or width > 30:
        return ["grid dimensions must not exceed 30"]
    if any(isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be literal ARC integers 0..9"]
    return []


def _components(cells):
    return len(_component_groups(cells))


def _component_groups(cells):
    remaining = set(cells)
    groups = []
    while remaining:
        group = {remaining.pop()}
        stack = list(group)
        while stack:
            row, col = stack.pop()
            for neighbor in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    group.add(neighbor)
                    stack.append(neighbor)
        groups.append(group)
    return groups


def _line_facts(cells):
    if len(cells) <= 1:
        return None, []
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    same_row = min(rows) == max(rows)
    same_col = min(cols) == max(cols)
    diag_down = len({row - col for row, col in cells}) == 1
    diag_up = len({row + col for row, col in cells}) == 1
    if same_row:
        kind, direction = "horizontal", (0, 1)
    elif same_col:
        kind, direction = "vertical", (1, 0)
    elif diag_down:
        kind, direction = "diag_down", (1, 1)
    elif diag_up:
        kind, direction = "diag_up", (1, -1)
    else:
        return None, []
    ordered = sorted(cells, key=lambda point: 1000 * point[0] + point[1])
    start, end = ordered[0], ordered[-1]
    steps = abs(end[1] - start[1]) if same_row else abs(end[0] - start[0])
    path = [(start[0] + step * direction[0], start[1] + step * direction[1]) for step in range(steps + 1)]
    return kind, path


def _extract_facts(grid):
    height, width = len(grid), len(grid[0])
    counts = Counter(value for row in grid for value in row)
    maximum = max(counts.values())
    modes = [color for color, count in counts.items() if count == maximum]
    if len(modes) != 1:
        raise ValueError("background mode must be unique")
    background = modes[0]
    result = [list(row) for row in grid]
    color_facts = {}
    rectangle_order = []
    line_order = []
    for color in range(1, 10):
        if color == background:
            continue
        cells = [(row, col) for row in range(height) for col in range(width) if grid[row][col] == color]
        if not cells:
            continue
        top = min(row for row, _ in cells)
        bottom = max(row for row, _ in cells)
        left = min(col for _, col in cells)
        right = max(col for _, col in cells)
        values = [grid[row][col] for row in range(top, bottom + 1) for col in range(left, right + 1)]
        has_background = background in values
        foreign = any(value not in (background, color) for value in values)
        qualifies = foreign and not has_background
        line_kind, line_path = _line_facts(cells)
        color_facts[color] = {
            "cells": cells,
            "count": len(cells),
            "bbox": (top, left, bottom, right),
            "has_background": has_background,
            "foreign": foreign,
            "qualifies_rectangle": qualifies,
            "components": _components(cells),
            "line_kind": line_kind,
            "line_path": line_path,
        }
        if qualifies:
            rectangle_order.append(color)
            for row in range(top, bottom + 1):
                for col in range(left, right + 1):
                    result[row][col] = color
    for color in range(1, 10):
        if color not in color_facts:
            continue
        facts = color_facts[color]
        if facts["line_kind"] is None:
            continue
        line_order.append(color)
        for row, col in facts["line_path"]:
            if 0 <= row < height and 0 <= col < width and grid[row][col] != background:
                result[row][col] = color
    return {
        "background": background,
        "background_count": counts[background],
        "color_facts": color_facts,
        "rectangle_order": rectangle_order,
        "line_order": line_order,
        "output": result,
        "changed": sum(before != after for old, new in zip(grid, result) for before, after in zip(old, new)),
    }


def _is_inert_decoy(entry):
    top, left, bottom, right = entry["bbox"]
    return (
        entry["count"] == INERT_COMPONENTS_PER_COLOR
        and entry["components"] == INERT_COMPONENTS_PER_COLOR
        and sorted((bottom - top + 1, right - left + 1)) == [2, 3]
        and entry["has_background"]
        and entry["foreign"]
        and not entry["qualifies_rectangle"]
        and entry["line_kind"] is None
    )


def _general_signature(facts):
    all_entries = facts["color_facts"]
    inert = [entry for entry in all_entries.values() if _is_inert_decoy(entry)]
    if len(inert) != INERT_DECOY_COLORS:
        return None
    entries = {color: entry for color, entry in all_entries.items() if not _is_inert_decoy(entry)}
    qualifiers = [entry for entry in entries.values() if entry["qualifies_rectangle"]]
    lines = [entry for entry in entries.values() if entry["line_kind"]]
    kinds = sorted(entry["line_kind"] for entry in lines)
    if len(entries) == 2 and len(qualifiers) == 1 and not lines:
        other = next(entry for entry in entries.values() if not entry["qualifies_rectangle"])
        return "rect_impurity" if other["count"] == 1 else "rect_occlusion"
    if len(entries) == 2 and len(qualifiers) == 2 and not lines:
        return "rect_priority"
    if (
        len(entries) == 2
        and len(lines) == 1
        and all(entry["line_kind"] is not None for entry in qualifiers)
    ):
        support = next(entry for entry in entries.values() if not entry["line_kind"])
        kind = lines[0]["line_kind"]
        if kind == "horizontal" and support["components"] > 1:
            return "background_gap_stays"
        return {
            "horizontal": "horizontal_bridge",
            "vertical": "vertical_bridge",
            "diag_down": "diag_down_bridge",
            "diag_up": "diag_up_bridge",
        }.get(kind)
    if len(entries) == 3 and len(qualifiers) == 1 and not lines:
        others = [entry for entry in entries.values() if not entry["qualifies_rectangle"] and entry["count"] > 1]
        if len(others) == 1 and others[0]["count"] == 3 and others[0]["components"] == 3:
            return "off_line_decoy_disables"
        if len(others) == 1 and others[0]["count"] == 8 and others[0]["components"] == 2:
            return "disconnected_bbox_blocks_fill"
    if (
        len(entries) == 3
        and len(lines) == 2
        and all(entry["line_kind"] is not None for entry in qualifiers)
        and kinds == ["horizontal", "vertical"]
    ):
        return "multiple_lines_priority"
    if (
        len(entries) == 3
        and len(lines) == 1
        and len([entry for entry in qualifiers if entry["line_kind"] is None]) == 1
    ):
        return "line_over_restoration"
    return None


def _analysis(grid):
    errors = _valid_grid(grid)
    if errors:
        return {"errors": errors, "scene_profile": None}
    try:
        facts = _extract_facts(grid)
    except (TypeError, ValueError) as exc:
        return {"errors": [str(exc)], "scene_profile": None}
    foreground = {value for row in grid for value in row if value != facts["background"]}
    if not foreground:
        errors.append("at least one foreground color is required")
    if 0 in foreground:
        errors.append("foreground color 0 is outside the canonical 1..9 processing loop")
    if facts["changed"] <= 0:
        errors.append("the canonical rule must visibly change the input")
    profile = _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid))) or _general_signature(facts)
    if profile is None:
        errors.append("scene does not match a declared semantic profile")
    return {"errors": errors, "scene_profile": profile, "facts": facts, "output": facts["output"]}


def rule_mirror(grid):
    errors = _valid_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return _extract_facts(grid)["output"]


def self_check(grid, *, difficulty=None, meta=None):
    return _analysis(grid)["errors"]


def canonical_profile_signature(grid):
    return _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid)))


def observe_overrides(grid):
    analysis = _analysis(grid)
    return {"scene_profile": analysis["scene_profile"]} if not analysis["errors"] else {}


def _draw_rect(grid, top, left, height, width, color):
    for row in range(top, top + height):
        for col in range(left, left + width):
            grid[row][col] = color


def _size_ranges(difficulty):
    if difficulty == "easy":
        return 12, 18, 3, 5
    if difficulty == "medium":
        return 16, 24, 4, 7
    if difficulty == "hard":
        return 20, 30, 5, 9
    return 14, 26, 3, 8


def _add_inert_decoys(grid, background, rng):
    """Add visual-density objects that cannot participate in either rule pass.

    A two-color zigzag contributes six monochrome components while remaining one
    color-blind object attached to the active scene.  Its rectangle contains
    background and neither color is collinear.  The patch is also outside every
    active color bbox and line path, so it cannot alter either rule pass.
    """
    facts = _extract_facts(grid)
    blocked = set()
    for entry in facts["color_facts"].values():
        top, left, bottom, right = entry["bbox"]
        blocked.update((row, col) for row in range(top, bottom + 1) for col in range(left, right + 1))
        blocked.update(entry["line_path"])

    active_cells = {
        point for entry in facts["color_facts"].values() for point in entry["cells"]
    }
    base = ((0, 0, 0), (0, 1, 1), (1, 1, 0), (1, 2, 1), (0, 2, 0), (0, 3, 1))
    variants = set()
    for reflected in (False, True):
        points = [(row, -col if reflected else col, label) for row, col, label in base]
        for _ in range(4):
            min_row = min(row for row, _, _ in points)
            min_col = min(col for _, col, _ in points)
            normalized = tuple(sorted((row - min_row, col - min_col, label) for row, col, label in points))
            variants.add(normalized)
            points = [(col, -row, label) for row, col, label in points]

    height, width = len(grid), len(grid[0])

    def placed_if_valid(pattern, top, left):
        patch_height = max(row for row, _, _ in pattern) + 1
        patch_width = max(col for _, col, _ in pattern) + 1
        placed = tuple((top + row, left + col, label) for row, col, label in pattern)
        if not any(
            neighbor in active_cells
            for row, col, _ in placed
            for neighbor in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1))
        ):
            return None
        if not all(
            grid[top + row][left + col] == background and (top + row, left + col) not in blocked
            for row in range(patch_height)
            for col in range(patch_width)
        ):
            return None
        return placed

    variant_list = list(variants)
    selected = None
    for _ in range(200):
        pattern = rng.choice(variant_list)
        patch_height = max(row for row, _, _ in pattern) + 1
        patch_width = max(col for _, col, _ in pattern) + 1
        top = rng.randrange(height - patch_height + 1)
        left = rng.randrange(width - patch_width + 1)
        selected = placed_if_valid(pattern, top, left)
        if selected is not None:
            break
    if selected is None:
        for pattern in variant_list:
            patch_height = max(row for row, _, _ in pattern) + 1
            patch_width = max(col for _, col, _ in pattern) + 1
            for top in range(height - patch_height + 1):
                for left in range(width - patch_width + 1):
                    selected = placed_if_valid(pattern, top, left)
                    if selected is not None:
                        break
                if selected is not None:
                    break
            if selected is not None:
                break
    used_colors = set(facts["color_facts"]) | {background}
    available_colors = [color for color in range(1, 10) if color not in used_colors]
    if selected is None or len(available_colors) < INERT_DECOY_COLORS:
        return False

    colors = rng.sample(available_colors, INERT_DECOY_COLORS)
    for row, col, label in selected:
        grid[row][col] = colors[label]
    return True


def _general_scene(ctx, profile, rng):
    low, high, shape_low, shape_high = _size_ranges(ctx.difficulty)
    for _ in range(100):
        height, width = rng.randint(low, high), rng.randint(low, high)
        background = rng.choice([0, 0, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9])
        legal = [color for color in range(1, 10) if color != background]
        needed = 3 if profile in {"off_line_decoy_disables", "disconnected_bbox_blocks_fill", "multiple_lines_priority", "line_over_restoration"} else 2
        colors = rng.sample(legal, needed)
        grid = [[background for _ in range(width)] for _ in range(height)]

        if profile == "rect_impurity":
            main, intruder = colors
            rh = rng.randint(shape_low, min(shape_high, height - 4))
            rw = rng.randint(shape_low, min(shape_high, width - 4))
            top, left = rng.randint(1, height - rh - 1), rng.randint(1, width - rw - 1)
            _draw_rect(grid, top, left, rh, rw, main)
            grid[rng.randint(top + 1, top + rh - 2)][rng.randint(left + 1, left + rw - 2)] = intruder
        elif profile == "rect_occlusion":
            buried, overlay = colors
            rh = rng.randint(max(4, shape_low), min(shape_high, height - 4))
            rw = rng.randint(max(4, shape_low), min(shape_high, width - 4))
            top, left = rng.randint(1, height - rh - 1), rng.randint(1, width - rw - 1)
            _draw_rect(grid, top, left, rh, rw, buried)
            oh, ow = rng.randint(2, rh - 1), rng.randint(2, rw - 1)
            ot, ol = rng.randint(top + 1, top + rh - oh), rng.randint(left + 1, left + rw - ow)
            _draw_rect(grid, ot, ol, oh, ow, overlay)
        elif profile == "rect_priority":
            first, second = colors
            rh = rng.randint(4, min(shape_high, height - 4))
            rw = rng.randint(4, min(shape_high, width - 4))
            top, left = rng.randint(1, height - rh - 1), rng.randint(1, width - rw - 1)
            for row in range(rh):
                for col in range(rw):
                    grid[top + row][left + col] = first if (row + col) % 2 == 0 else second
        elif profile in {"horizontal_bridge", "vertical_bridge"}:
            support, line = colors
            rh = rng.randint(3, min(shape_high, height - 7))
            rw = rng.randint(3, min(shape_high, width - 7))
            top, left = rng.randint(3, height - rh - 4), rng.randint(3, width - rw - 4)
            _draw_rect(grid, top, left, rh, rw, support)
            if profile == "horizontal_bridge":
                row = rng.randint(top, top + rh - 1)
                before, after = rng.randint(1, 3), rng.randint(1, 3)
                grid[row][left - before] = line
                grid[row][left + rw - 1 + after] = line
                for col in range(left - before + 1, left):
                    grid[row][col] = support
                for col in range(left + rw, left + rw - 1 + after):
                    grid[row][col] = support
            else:
                col = rng.randint(left, left + rw - 1)
                before, after = rng.randint(1, 3), rng.randint(1, 3)
                grid[top - before][col] = line
                grid[top + rh - 1 + after][col] = line
                for row in range(top - before + 1, top):
                    grid[row][col] = support
                for row in range(top + rh, top + rh - 1 + after):
                    grid[row][col] = support
        elif profile in {"diag_down_bridge", "diag_up_bridge"}:
            support, line = colors
            side = rng.randint(3, min(shape_high, height - 7, width - 7))
            top, left = rng.randint(3, height - side - 4), rng.randint(3, width - side - 4)
            _draw_rect(grid, top, left, side, side, support)
            if profile == "diag_down_bridge":
                grid[top - 1][left - 1] = line
                grid[top - 1][left] = support
                grid[top + side][left + side] = line
                grid[top + side][left + side - 1] = support
            else:
                grid[top - 1][left + side] = line
                grid[top - 1][left + side - 1] = support
                grid[top + side][left - 1] = line
                grid[top + side][left] = support
        elif profile == "background_gap_stays":
            support, line = colors
            gap = rng.randint(2, min(6, width - 10))
            span = 4 + gap
            left = rng.randint(2, width - span - 3)
            top = rng.randint(2, height - 4)
            _draw_rect(grid, top, left, 2, 2, support)
            _draw_rect(grid, top, left + 2 + gap, 2, 2, support)
            grid[top][left - rng.randint(1, 2)] = line
            grid[top][left + span - 1 + rng.randint(1, 2)] = line
        elif profile in {"off_line_decoy_disables", "disconnected_bbox_blocks_fill"}:
            main, intruder, rival = colors
            rh = rng.randint(3, min(5, height - 8))
            rw = rng.randint(3, min(6, width - 4))
            top, left = rng.randint(6, height - rh - 1), rng.randint(1, width - rw - 1)
            _draw_rect(grid, top, left, rh, rw, main)
            grid[top + 1][left + 1] = intruder
            if profile == "off_line_decoy_disables":
                grid[1][1] = rival
                grid[1][width - 2] = rival
                grid[3][2] = rival
            else:
                _draw_rect(grid, 1, 1, 2, 2, rival)
                _draw_rect(grid, 1, width - 3, 2, 2, rival)
        elif profile == "multiple_lines_priority":
            support, horizontal, vertical = colors
            rh = rng.randint(3, min(shape_high, height - 7))
            rw = rng.randint(3, min(shape_high, width - 7))
            top, left = rng.randint(3, height - rh - 4), rng.randint(3, width - rw - 4)
            _draw_rect(grid, top, left, rh, rw, support)
            row, col = rng.randint(top, top + rh - 1), rng.randint(left, left + rw - 1)
            left_gap, right_gap = rng.randint(1, 3), rng.randint(1, 3)
            top_gap, bottom_gap = rng.randint(1, 3), rng.randint(1, 3)
            grid[row][left - left_gap] = horizontal
            grid[row][left + rw - 1 + right_gap] = horizontal
            grid[top - top_gap][col] = vertical
            grid[top + rh - 1 + bottom_gap][col] = vertical
            for arm_col in range(left - left_gap + 1, left):
                grid[row][arm_col] = support
            for arm_col in range(left + rw, left + rw - 1 + right_gap):
                grid[row][arm_col] = support
            for arm_row in range(top - top_gap + 1, top):
                grid[arm_row][col] = support
            for arm_row in range(top + rh, top + rh - 1 + bottom_gap):
                grid[arm_row][col] = support
        elif profile == "line_over_restoration":
            buried, overlay, line = colors
            rh = rng.randint(4, min(shape_high, height - 7))
            rw = rng.randint(4, min(shape_high, width - 7))
            top, left = rng.randint(3, height - rh - 4), rng.randint(3, width - rw - 4)
            _draw_rect(grid, top, left, rh, rw, buried)
            oh, ow = rng.randint(2, rh - 1), rng.randint(2, rw - 1)
            ot, ol = rng.randint(top + 1, top + rh - oh), rng.randint(left + 1, left + rw - ow)
            _draw_rect(grid, ot, ol, oh, ow, overlay)
            row = rng.randint(ot, ot + oh - 1)
            before, after = rng.randint(1, 3), rng.randint(1, 3)
            grid[row][left - before] = line
            grid[row][left + rw - 1 + after] = line
            for col in range(left - before + 1, left):
                grid[row][col] = overlay
            for col in range(left + rw, left + rw - 1 + after):
                grid[row][col] = overlay
        else:
            raise ValueError(f"unknown scene_profile: {profile!r}")

        if not _add_inert_decoys(grid, background, rng):
            continue
        analysis = _analysis(grid)
        if not analysis["errors"] and analysis["scene_profile"] == profile:
            return grid
    raise AssertionError(f"could not construct {profile}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - {"scene_profile"})
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION, task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    profile = ctx.draw_choice("scene_profile", PUBLIC_PROFILES + GENERAL_PROFILES * 4)
    if profile in PUBLIC_PROFILES:
        return [row[:] for row in _PUBLIC_INPUTS[profile]]
    return _general_scene(ctx, profile, ctx.draw_rng("geometry"))
