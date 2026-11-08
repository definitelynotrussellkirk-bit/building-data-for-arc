"""Generator for H43 — select by size rank, transform, and stamp.

The input contains three disconnected blue components with distinct areas.
The number of red cells selects the component's one-based size rank.  The
number of green cells selects the transform (1 identity, 2 clockwise 90°, 3
180°, 4 left-right mirror).  The transformed normalized component is stamped
in orange with its top-left cell at the unique cyan target, on an otherwise
blank output grid.
"""
from __future__ import annotations

from collections import deque
from typing import Callable, Iterable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "72dbce4d594b"
TASK_ID = "72dbce4d594b"
VERSION = "2.1.0"
RULE_HASH = "d291f7b88b55"
SUMMARY = (
    "Three disconnected blue components have distinct sizes. Red marker count "
    "selects the one-based size rank; green marker count selects identity, 90° "
    "clockwise, 180°, or left-right mirror. Stamp the transformed normalized "
    "component in orange at the unique cyan target on a blank grid."
)

INVARIANTS = [
    "the input palette is exactly a subset of {0,1,2,3,8}",
    "there are three 4-connected blue components with distinct areas",
    "1..3 red cells select a valid one-based blue-component size rank",
    "1..4 green cells select identity, clockwise 90, 180, or left-right mirror",
    "there is exactly one cyan target and the selected transformed shape fits",
]

_SIZE_PROFILES = {
    "canonical_234": (2, 3, 4),
    "spread_246": (2, 4, 6),
    "wide_358": (3, 5, 8),
    "asymmetric_457": (4, 5, 7),
    "asymmetric_468": (4, 6, 8),
}
_RED_LAYOUTS = ("top", "left", "scattered")
_GREEN_LAYOUTS = ("right", "bottom", "scattered")
_TARGET_ZONES = ("top_left", "top_right", "center", "bottom_left", "bottom_right")
_CANONICAL_DIMS = ((11, 13), (11, 14), (12, 12), (12, 13), (12, 14))

AXES = {
    "grid_h": {"type": "int", "default": "profile-linked 11..16", "valid": "11..16"},
    "grid_w": {"type": "int", "default": "profile-linked 12..19", "valid": "12..19"},
    "rank": {"type": "int", "default": "scheduled 1..3", "valid": "1..3"},
    "transform": {"type": "int", "default": "scheduled 1..4", "valid": "1..4"},
    "size_profile": {
        "type": "str",
        "default": "profile-linked",
        "valid": "canonical_234|spread_246|wide_358|asymmetric_457|asymmetric_468",
    },
    "red_layout": {"type": "str", "default": "profile-linked", "valid": "top|left|scattered"},
    "green_layout": {
        "type": "str",
        "default": "profile-linked",
        "valid": "right|bottom|scattered",
    },
    "target_zone": {
        "type": "str",
        "default": "scheduled across five zones",
        "valid": "top_left|top_right|center|bottom_left|bottom_right",
    },
}

EXAMPLES_NEEDED = 5
SCHEDULE_PROFILES = ("canonical_anchor", "layout_shift", "size_spread", "mixed")


def schedule_profile(seed, sample_index, difficulty=None):
    """Every five-sample window includes an anchor and four teaching slots.

    The old step of two modulo four permanently omitted half the profiles
    for each seed.  This schedule is periodic in five, coprime to rank's three.
    """
    del difficulty
    phase = (seed + sample_index) % 5
    return SCHEDULE_PROFILES[(0, 1, 2, 3, 3)[phase]]


def _norm(cells: Iterable[tuple[int, int]]) -> list[tuple[int, int]]:
    cells = list(cells)
    if not cells:
        return []
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return sorted((r - min_r, c - min_c) for r, c in cells)


def _dims(cells: Sequence[tuple[int, int]]) -> tuple[int, int]:
    cells = list(cells)
    return max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1


def _rot90(cells: Sequence[tuple[int, int]]) -> list[tuple[int, int]]:
    cells = _norm(cells)
    height, _ = _dims(cells)
    return _norm((c, height - 1 - r) for r, c in cells)


def _transform(cells: Sequence[tuple[int, int]], code: int) -> list[tuple[int, int]]:
    cells = _norm(cells)
    if code == 1:
        return cells
    if code == 2:
        return _rot90(cells)
    if code == 3:
        return _rot90(_rot90(cells))
    if code == 4:
        _, width = _dims(cells)
        return _norm((r, width - 1 - c) for r, c in cells)
    raise ValueError(f"transform code must be 1..4, got {code}")


def _rot270(cells: Sequence[tuple[int, int]]) -> list[tuple[int, int]]:
    return _rot90(_rot90(_rot90(cells)))


_D4_NAMES = ("identity", "rot90", "rot180", "rot270", "flip_lr", "flip_ud", "transpose", "anti_transpose")
_TRUE_D4 = (0, 1, 2, 4)


def _d4(cells: Sequence[tuple[int, int]], variant: int) -> list[tuple[int, int]]:
    """The eight square symmetries, normalized to their bounding boxes."""
    cells = _norm(cells)
    if variant < 4:
        for _ in range(variant):
            cells = _rot90(cells)
        return cells
    height, width = _dims(cells)
    if variant == 4:
        return _norm((r, width - 1 - c) for r, c in cells)
    if variant == 5:
        return _norm((height - 1 - r, c) for r, c in cells)
    if variant == 6:
        return _norm((c, r) for r, c in cells)
    if variant == 7:
        return _norm((width - 1 - c, height - 1 - r) for r, c in cells)
    raise ValueError(f"D4 variant must be 0..7, got {variant}")


def _asymmetric(cells: Sequence[tuple[int, int]]) -> bool:
    return len({tuple(_d4(cells, v)) for v in range(8)}) == 8


def _components(grid, color: int) -> list[list[tuple[int, int]]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[list[tuple[int, int]]] = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] != color or (row, col) in seen:
                continue
            queue = deque([(row, col)])
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while queue:
                r, c = queue.popleft()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] == color
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            result.append(cells)
    return result


def _analyze(grid):
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return ["empty grid"], None
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["ragged grid"], None
    height = len(grid)
    if height > 30 or width > 30:
        errors.append(f"grid too large: {height}x{width}")
    bad_values = sorted({value for row in grid for value in row if value not in {0, 1, 2, 3, 8}})
    if bad_values:
        errors.append(f"unexpected input colors: {bad_values}")

    blue = _components(grid, 1)
    sizes = [len(cells) for cells in blue]
    red = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2]
    green = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 3]
    cyan = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 8]

    if len(blue) != 3:
        errors.append(f"expected exactly three blue components, got {len(blue)}")
    if len(set(sizes)) != len(sizes):
        errors.append(f"blue component areas must be distinct, got {sorted(sizes)}")
    if not (1 <= len(red) <= len(blue)):
        errors.append(f"red marker count {len(red)} does not select one of {len(blue)} components")
    if not (1 <= len(green) <= 4):
        errors.append(f"green transform count must be 1..4, got {len(green)}")
    if len(cyan) != 1:
        errors.append(f"expected exactly one cyan target, got {len(cyan)}")

    selected = transformed = None
    if blue and len(set(sizes)) == len(sizes) and 1 <= len(red) <= len(blue):
        selected = sorted(blue, key=len)[len(red) - 1]
        if 1 <= len(green) <= 4:
            transformed = _transform(_norm(selected), len(green))
            if len(cyan) == 1:
                shape_h, shape_w = _dims(transformed)
                target_r, target_c = cyan[0]
                if target_r + shape_h > height or target_c + shape_w > width:
                    errors.append(
                        f"transformed {shape_h}x{shape_w} shape does not fit at target {cyan[0]}"
                    )

    return errors, {
        "height": height,
        "width": width,
        "blue": blue,
        "sizes": sorted(sizes),
        "rank": len(red),
        "transform": len(green),
        "red": red,
        "green": green,
        "cyan": cyan,
        "selected": selected,
        "transformed": transformed,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed, ambiguous, or out-of-bounds rule inputs."""
    del difficulty, meta
    errors, _ = _analyze(grid)
    return errors


def _layout_name(cells, *, first: str, second: str, height: int, width: int) -> str:
    if first == "top" and cells and all(r == 0 for r, _ in cells):
        return "top"
    if first == "right" and cells and all(c == width - 1 for _, c in cells):
        return "right"
    if second == "left" and cells and all(c == 0 for _, c in cells):
        return "left"
    if second == "bottom" and cells and all(r == height - 1 for r, _ in cells):
        return "bottom"
    return "scattered"


def _classify_zone(row: int, col: int, max_row: int, max_col: int) -> str:
    mid_rows = {max_row // 2, (max_row + 1) // 2}
    mid_cols = {max_col // 2, (max_col + 1) // 2}
    if row in mid_rows and col in mid_cols:
        return "center"
    vertical = "top" if row * 2 <= max_row else "bottom"
    horizontal = "left" if col * 2 <= max_col else "right"
    return f"{vertical}_{horizontal}"


def observe_overrides(grid) -> dict[str, object]:
    """Recover every declared axis exactly from a valid returned grid."""
    errors, analysis = _analyze(grid)
    if errors or analysis is None or analysis["transformed"] is None:
        raise ValueError("cannot observe invalid grid: " + "; ".join(errors))
    size_profile = next(
        (name for name, sizes in _SIZE_PROFILES.items() if tuple(analysis["sizes"]) == sizes),
        None,
    )
    if size_profile is None:
        raise ValueError(f"unrecognized size profile {analysis['sizes']}")
    target_r, target_c = analysis["cyan"][0]
    shape_h, shape_w = _dims(analysis["transformed"])
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "rank": analysis["rank"],
        "transform": analysis["transform"],
        "size_profile": size_profile,
        "red_layout": _layout_name(
            analysis["red"], first="top", second="left",
            height=analysis["height"], width=analysis["width"],
        ),
        "green_layout": _layout_name(
            analysis["green"], first="right", second="bottom",
            height=analysis["height"], width=analysis["width"],
        ),
        "target_zone": _classify_zone(
            target_r,
            target_c,
            analysis["height"] - shape_h,
            analysis["width"] - shape_w,
        ),
    }


def rule_mirror(grid):
    """Pure Python rule mirror for tests and rival analysis only."""
    errors, analysis = _analyze(grid)
    if errors or analysis is None or analysis["transformed"] is None:
        raise ValueError("outside rule domain: " + "; ".join(errors))
    output = full_grid(analysis["height"], analysis["width"], 0)
    target_r, target_c = analysis["cyan"][0]
    for dr, dc in analysis["transformed"]:
        output[target_r + dr][target_c + dc] = 7
    return output


def strict_canonical_like(grid) -> list[str]:
    """Recognize the exact canonical-scale branch of the lawful grammar."""
    reasons, analysis = _analyze(grid)
    if reasons or analysis is None:
        return reasons
    if (analysis["height"], analysis["width"]) not in _CANONICAL_DIMS:
        reasons.append(
            f"dimensions {(analysis['height'], analysis['width'])} are outside canonical profiles"
        )
    if analysis["sizes"] != [2, 3, 4]:
        reasons.append(f"canonical blue areas are [2, 3, 4], got {analysis['sizes']}")
    if _layout_name(
        analysis["red"], first="top", second="left",
        height=analysis["height"], width=analysis["width"],
    ) != "top":
        reasons.append("canonical red markers occupy the top row")
    if _layout_name(
        analysis["green"], first="right", second="bottom",
        height=analysis["height"], width=analysis["width"],
    ) != "right":
        reasons.append("canonical green markers occupy the right column")
    return reasons


def _solve_with(grid, *, rank: int | None = None, transform: int | None = None,
                target: tuple[int, int] | None = None, transform_fn: Callable | None = None):
    errors, analysis = _analyze(grid)
    if errors or analysis is None:
        raise ValueError("outside rule domain: " + "; ".join(errors))
    chosen_rank = analysis["rank"] if rank is None else rank
    chosen_code = analysis["transform"] if transform is None else transform
    selected = sorted(analysis["blue"], key=len)[chosen_rank - 1]
    shape = (
        transform_fn(_norm(selected))
        if transform_fn is not None
        else _transform(_norm(selected), chosen_code)
    )
    output = full_grid(analysis["height"], analysis["width"], 0)
    if target is None:
        target = analysis["cyan"][0]
    for dr, dc in shape:
        rr, cc = target[0] + dr, target[1] + dc
        if 0 <= rr < analysis["height"] and 0 <= cc < analysis["width"]:
            output[rr][cc] = 7
    return output


def _rival_always_smallest(grid):
    return _solve_with(grid, rank=1)


def _rival_always_largest(grid):
    errors, analysis = _analyze(grid)
    if errors or analysis is None:
        raise ValueError("outside rule domain")
    return _solve_with(grid, rank=len(analysis["blue"]))


def _rival_ignore_transform(grid):
    return _solve_with(grid, transform=1)


def _rival_always_rotate90(grid):
    return _solve_with(grid, transform=2)


def _rival_code4_is_rot270(grid):
    errors, analysis = _analyze(grid)
    if errors or analysis is None:
        raise ValueError("outside rule domain")
    if analysis["transform"] == 4:
        return _solve_with(grid, transform_fn=_rot270)
    return rule_mirror(grid)


def _rival_ignore_cyan_use_center(grid):
    errors, analysis = _analyze(grid)
    if errors or analysis is None or analysis["transformed"] is None:
        raise ValueError("outside rule domain")
    shape_h, shape_w = _dims(analysis["transformed"])
    target = ((analysis["height"] - shape_h) // 2, (analysis["width"] - shape_w) // 2)
    return _solve_with(grid, target=target)


def _rival_marker_cell_only(grid):
    errors, analysis = _analyze(grid)
    if errors or analysis is None:
        raise ValueError("outside rule domain")
    output = full_grid(analysis["height"], analysis["width"], 0)
    r, c = analysis["cyan"][0]
    output[r][c] = 7
    return output


SEMANTIC_RIVALS = {
    "always_select_smallest": _rival_always_smallest,
    "always_select_largest": _rival_always_largest,
    "ignore_green_transform": _rival_ignore_transform,
    "always_rotate90": _rival_always_rotate90,
    "treat_code4_as_rotate270": _rival_code4_is_rot270,
    "ignore_cyan_use_center": _rival_ignore_cyan_use_center,
    "marker_cell_is_answer": _rival_marker_cell_only,
}
def _command_rival(code: int, variant: int) -> Callable:
    """Change exactly one command-table entry; leave all other entries correct."""
    def rival(grid):
        actual_code = sum(value == 3 for row in grid for value in row)
        if actual_code != code:
            return rule_mirror(grid)
        return _solve_with(grid, transform_fn=lambda cells: _d4(cells, variant))
    return rival


# Testing each one-entry substitution is sufficient for this factorized table:
# if any of 8**4 command tables fits the demos but differs on the query, the
# single changed entry for the query command also survives and differs.
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS.update({
    f"command_{code}_as_{name}": _command_rival(code, variant)
    for code in range(1, 5)
    for variant, name in enumerate(_D4_NAMES)
    if variant != _TRUE_D4[code - 1]
})


def _valid_analysis(grid):
    errors, analysis = _analyze(grid)
    return None if errors else analysis


def _w_rank_not_smallest(grid):
    analysis = _valid_analysis(grid)
    return (
        analysis is not None
        and analysis["rank"] != 1
        and _rival_always_smallest(grid) != rule_mirror(grid)
    )


def _w_rank_not_largest(grid):
    analysis = _valid_analysis(grid)
    return (
        analysis is not None
        and analysis["rank"] != len(analysis["blue"])
        and _rival_always_largest(grid) != rule_mirror(grid)
    )


def _w_transform_changes_shape(grid):
    analysis = _valid_analysis(grid)
    return (
        analysis is not None
        and analysis["selected"] is not None
        and analysis["transformed"] != _norm(analysis["selected"])
    )


def _w_code4_mirror_not_rot270(grid):
    analysis = _valid_analysis(grid)
    if analysis is None or analysis["transform"] != 4 or analysis["selected"] is None:
        return False
    shape = _norm(analysis["selected"])
    return _transform(shape, 4) != _rot270(shape)


def _w_target_not_center(grid):
    analysis = _valid_analysis(grid)
    if analysis is None or analysis["transformed"] is None:
        return False
    shape_h, shape_w = _dims(analysis["transformed"])
    center = ((analysis["height"] - shape_h) // 2, (analysis["width"] - shape_w) // 2)
    return analysis["cyan"][0] != center


def _w_multi_cell_answer(grid):
    analysis = _valid_analysis(grid)
    return analysis is not None and analysis["selected"] is not None and len(analysis["selected"]) > 1


def _w_rank_1_not_largest(grid):
    analysis = _valid_analysis(grid)
    return analysis is not None and analysis["rank"] == 1


def _w_rank_2_not_extremes(grid):
    analysis = _valid_analysis(grid)
    return analysis is not None and analysis["rank"] == 2


def _w_rank_3_not_smallest(grid):
    analysis = _valid_analysis(grid)
    return analysis is not None and analysis["rank"] == 3


def _w_transform_1_not_rotate90(grid):
    analysis = _valid_analysis(grid)
    if analysis is None or analysis["transform"] != 1 or analysis["selected"] is None:
        return False
    shape = _norm(analysis["selected"])
    return shape != _transform(shape, 2)


def _w_transform_2_not_identity(grid):
    analysis = _valid_analysis(grid)
    if analysis is None or analysis["transform"] != 2 or analysis["selected"] is None:
        return False
    shape = _norm(analysis["selected"])
    return _transform(shape, 2) != shape


def _w_transform_3_not_identity(grid):
    analysis = _valid_analysis(grid)
    if analysis is None or analysis["transform"] != 3 or analysis["selected"] is None:
        return False
    shape = _norm(analysis["selected"])
    return _transform(shape, 3) != shape


SEMANTIC_WITNESSES = {
    "rank_1_refutes_always_largest": _w_rank_1_not_largest,
    "rank_2_refutes_extreme_rank_shortcuts": _w_rank_2_not_extremes,
    "rank_3_refutes_always_smallest": _w_rank_3_not_smallest,
    "transform_1_identity_not_rotate90": _w_transform_1_not_rotate90,
    "transform_2_rot90_not_identity": _w_transform_2_not_identity,
    "transform_3_rot180_not_identity": _w_transform_3_not_identity,
    "transform_4_mirror_not_rotate270": _w_code4_mirror_not_rot270,
    "rank_count_not_always_smallest": _w_rank_not_smallest,
    "rank_count_not_always_largest": _w_rank_not_largest,
    "green_count_changes_shape": _w_transform_changes_shape,
    "cyan_target_not_grid_center": _w_target_not_center,
    "answer_is_selected_shape_not_marker": _w_multi_cell_answer,
}
WITNESS_RIVALS = {
    "rank_1_refutes_always_largest": ["always_select_largest"],
    "rank_2_refutes_extreme_rank_shortcuts": ["always_select_smallest", "always_select_largest"],
    "rank_3_refutes_always_smallest": ["always_select_smallest"],
    "transform_1_identity_not_rotate90": ["always_rotate90"],
    "transform_2_rot90_not_identity": ["ignore_green_transform"],
    "transform_3_rot180_not_identity": ["ignore_green_transform"],
    "transform_4_mirror_not_rotate270": ["treat_code4_as_rotate270"],
    "rank_count_not_always_smallest": ["always_select_smallest"],
    "rank_count_not_always_largest": ["always_select_largest"],
    "green_count_changes_shape": ["ignore_green_transform"],
    "cyan_target_not_grid_center": ["ignore_cyan_use_center"],
    "answer_is_selected_shape_not_marker": ["marker_cell_is_answer"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject any lesson where a named plausible wrong rule survives demos."""
    reasons: list[str] = []
    for index, demo in enumerate(demos):
        try:
            expected = rule_mirror(demo["input"])
        except ValueError as exc:
            reasons.append(f"demo {index} is outside the rule grammar: {exc}")
            continue
        if expected != demo["output"]:
            reasons.append(f"demo {index} output disagrees with the pinned rule")
    try:
        query_answer = rule_mirror(query["input"])
    except ValueError as exc:
        reasons.append(f"query is outside the rule grammar: {exc}")
        return reasons
    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(competitor(demo["input"]) == demo["output"] for demo in demos)
        if survives and competitor(query["input"]) != query_answer:
            reasons.append(f"competitor '{name}' fits every demo but changes the query answer")
    return reasons


def _draw_int_axis(ctx, label: str, lo: int, hi: int, default: int | tuple[int, int]) -> int:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    if isinstance(default, tuple):
        return ctx.draw_int(label, default[0], default[1])
    return ctx.draw_int(label, default, default)


def _draw_choice_axis(ctx, label: str, options: Sequence[str], default: str | Sequence[str]) -> str:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_choice(label, options)
    defaults = (default,) if isinstance(default, str) else tuple(default)
    return ctx.draw_choice(label, defaults)


def _grow_polyomino(rng, size: int, *, require_distinct_code: int | None = None,
                     require_asymmetric: bool = False) -> list[tuple[int, int]]:
    """Grow a compact connected shape, preferring one changed by the command.

    Some tiny polyominoes cannot visibly change under particular commands
    (every domino is invariant under a 180-degree rotation up to bbox
    normalization).  Do not waste a large retry budget on an impossible
    preference; the command remains observable through the selected rank and
    the rest of the curriculum.
    """
    if require_asymmetric and size < 4:
        raise ValueError("eight distinguishable orientations require at least four cells")
    if require_distinct_code == 1 or (size <= 2 and require_distinct_code == 3):
        require_distinct_code = None
    fallback = None
    for _ in range(24):
        cells = {(0, 0)}
        while len(cells) < size:
            frontier = []
            for r, c in cells:
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    p = (r + dr, c + dc)
                    if p not in cells:
                        frontier.append(p)
            candidate = rng.choice(frontier)
            tentative = cells | {candidate}
            normed = _norm(tentative)
            h, w = _dims(normed)
            if h <= 5 and w <= 5:
                cells = tentative
        shape = _norm(cells)
        fallback = shape
        if require_asymmetric:
            if _asymmetric(shape):
                return shape
            continue
        if require_distinct_code is None:
            return shape
        if require_distinct_code == 4:
            rotate_270 = _rot90(_rot90(_rot90(shape)))
            if _transform(shape, 4) != rotate_270:
                return shape
        elif _transform(shape, require_distinct_code) != shape:
            return shape
    if require_asymmetric:
        # Bounded fallback, not a silent loss of the teaching invariant.
        # Unequal-arm L shapes of areas 4..8 have all eight D4 orientations.
        height = min(5, size - 1)
        shape = [(r, 0) for r in range(height)]
        shape += [(height - 1, c) for c in range(1, size - height + 1)]
        if not _asymmetric(shape):
            raise ValueError(f"no asymmetric fallback for area {size}")
        return _d4(shape, rng.randrange(8))
    assert fallback is not None
    return fallback


def _zone_cells(zone: str, max_row: int, max_col: int) -> list[tuple[int, int]]:
    return [
        (r, c)
        for r in range(max_row + 1)
        for c in range(max_col + 1)
        if _classify_zone(r, c, max_row, max_col) == zone
    ]


def _marker_candidates(layout: str, *, color: str, height: int, width: int) -> list[tuple[int, int]]:
    if color == "red":
        if layout == "top":
            return [(0, c) for c in range(1, width)]
        if layout == "left":
            return [(r, 0) for r in range(1, height)]
    else:
        if layout == "right":
            return [(r, width - 1) for r in range(height - 1)]
        if layout == "bottom":
            return [(height - 1, c) for c in range(width - 1)]
    return [(r, c) for r in range(1, height - 1) for c in range(1, width - 1)]


def _choose_markers(rng, candidates, count: int, occupied: set[tuple[int, int]], *, scattered: bool):
    available = [p for p in candidates if p not in occupied]
    rng.shuffle(available)
    if len(available) < count:
        raise ValueError("not enough marker positions")
    if not scattered:
        chosen = available[:count]
        return chosen
    chosen: list[tuple[int, int]] = []
    for p in available:
        if all(abs(p[0] - q[0]) + abs(p[1] - q[1]) > 1 for q in chosen):
            chosen.append(p)
            if len(chosen) == count:
                return chosen
    return available[:count]


def _place_shape(grid, shape, rng, occupied: set[tuple[int, int]]) -> bool:
    height, width = len(grid), len(grid[0])
    shape_h, shape_w = _dims(shape)
    anchors = [(r, c) for r in range(height - shape_h + 1) for c in range(width - shape_w + 1)]
    rng.shuffle(anchors)
    for top, left in anchors:
        cells = {(top + r, left + c) for r, c in shape}
        if cells & occupied:
            continue
        if any(
            (rr + dr, cc + dc) in occupied and grid[rr + dr][cc + dc] == 1
            for rr, cc in cells
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
            if 0 <= rr + dr < height and 0 <= cc + dc < width
        ):
            continue
        for r, c in cells:
            grid[r][c] = 1
        occupied.update(cells)
        return True
    return False


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty {difficulty!r}; expected easy, medium, or hard")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = schedule_profile(seed, sample_index, difficulty)
    slot = seed + sample_index
    phase = slot % 5

    if profile == "canonical_anchor":
        default_h, default_w = _CANONICAL_DIMS[ctx.draw_rng("canonical_dims").randrange(len(_CANONICAL_DIMS))]
        default_size = "canonical_234"
        default_red, default_green = "top", "right"
    elif profile == "layout_shift":
        default_h, default_w = (11, 14)
        default_size = "canonical_234"
        default_red = ("left", "scattered")
        default_green = ("bottom", "scattered")
    elif profile == "size_spread":
        default_h = (12, 15)
        default_w = (14, 18)
        default_size = "spread_246"
        default_red = _RED_LAYOUTS
        default_green = _GREEN_LAYOUTS
    else:
        default_h = (13, 16) if difficulty == "hard" else (11, 16)
        default_w = (15, 19) if difficulty == "hard" else (12, 19)
        default_size = "wide_358" if difficulty != "easy" else "spread_246"
        default_red = _RED_LAYOUTS
        default_green = _GREEN_LAYOUTS

    height = _draw_int_axis(ctx, "grid_h", 11, 16, default_h)
    width = _draw_int_axis(ctx, "grid_w", 12, 19, default_w)
    rank = _draw_int_axis(ctx, "rank", 1, 3, slot % 3 + 1)
    # Four non-anchor slots teach all commands. The extra canonical sample
    # preserves small/symmetric source shapes without underdetermining queries.
    default_transform = ((phase - 1 + seed) % 4 + 1) if phase else ((slot // 5 + seed) % 4 + 1)
    transform = _draw_int_axis(ctx, "transform", 1, 4, default_transform)
    if phase:
        default_size = "asymmetric_457" if profile == "layout_shift" else "asymmetric_468"
    size_profile = _draw_choice_axis(ctx, "size_profile", tuple(_SIZE_PROFILES), default_size)
    red_layout = _draw_choice_axis(ctx, "red_layout", _RED_LAYOUTS, default_red)
    green_layout = _draw_choice_axis(ctx, "green_layout", _GREEN_LAYOUTS, default_green)
    target_zone = _draw_choice_axis(
        ctx,
        "target_zone",
        _TARGET_ZONES,
        _TARGET_ZONES[(seed * 5 + sample_index) % len(_TARGET_ZONES)],
    )

    sizes = _SIZE_PROFILES[size_profile]
    shapes = []
    for index, size in enumerate(sizes):
        code = transform if index == rank - 1 else None
        shapes.append(_grow_polyomino(
            ctx.draw_rng(f"shape_{index}"), size,
            require_distinct_code=code,
            # Apply equally to all candidates: asymmetry must not reveal rank.
            require_asymmetric=size_profile.startswith("asymmetric_"),
        ))

    selected_shape = _transform(shapes[rank - 1], transform)
    shape_h, shape_w = _dims(selected_shape)
    max_target_row = height - shape_h
    max_target_col = width - shape_w
    target_options = _zone_cells(target_zone, max_target_row, max_target_col)
    if not target_options:
        raise ValueError(f"target zone {target_zone!r} has no anchor in {height}x{width}")
    target_rng = ctx.draw_rng("target_position")
    target = target_options[target_rng.randrange(len(target_options))]
    stamp_footprint = {(target[0] + r, target[1] + c) for r, c in selected_shape}

    grid = full_grid(height, width, 0)
    occupied = set(stamp_footprint) | {target}
    marker_rng = ctx.draw_rng("marker_positions")
    red = _choose_markers(
        marker_rng,
        _marker_candidates(red_layout, color="red", height=height, width=width),
        rank,
        occupied,
        scattered=red_layout == "scattered",
    )
    occupied.update(red)
    green = _choose_markers(
        marker_rng,
        _marker_candidates(green_layout, color="green", height=height, width=width),
        transform,
        occupied,
        scattered=green_layout == "scattered",
    )
    occupied.update(green)

    for r, c in red:
        grid[r][c] = 2
    for r, c in green:
        grid[r][c] = 3
    grid[target[0]][target[1]] = 8

    # Keep the whole destination footprint empty in the input. This is a
    # curriculum choice, not part of self_check's authority grammar.
    occupied = set(red) | set(green) | stamp_footprint | {target}
    placement_rng = ctx.draw_rng("component_positions")
    placement_order = list(range(3))
    placement_rng.shuffle(placement_order)
    for index in placement_order:
        if not _place_shape(grid, shapes[index], placement_rng, occupied):
            raise ValueError(f"could not place blue component of size {sizes[index]}")

    errors = self_check(grid)
    if errors:
        raise ValueError("internal self_check failed: " + "; ".join(errors))
    return grid
