"""Semantic generator for ARC task ``26f313fdf812`` (Area Comparison Matrix).

The input contains several single-color 4-connected objects on background 0.
Objects are ordered by their bounding-box top-left coordinate (row, then
column).  The output is an N x N matrix comparing object *cell counts*:
1 for equal area, 2 when the row object is larger, and 3 when it is smaller.

The curriculum deliberately mixes off-diagonal equal-area examples with
all-distinct areas, varies object count, scrambles colors independently of
area/order, and includes shapes whose bounding-box area disagrees with cell
area.  Those controls refute several shortcuts that fit subsets of the public
examples while keeping the selected Racket rule as the sole output authority.
"""
from __future__ import annotations

from collections import deque
from typing import Any, Callable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "26f313fdf812"
TASK_ID = GENERATOR_ID
VERSION = "3.1.0"
RULE_HASH = "80930b679862"

SUMMARY = (
    "Order same-color 4-connected nonzero objects by bounding-box top-left "
    "position. Output an N×N matrix with 1 for equal cell area, 2 when the "
    "row object is larger, and 3 when it is smaller."
)

INVARIANTS = [
    "background is 0 and every nonzero color forms exactly one 4-connected object",
    "objects are ordered by bounding-box top-left row, then column",
    "output dimensions equal the number of input objects",
    "matrix entry (i,j) is 1/2/3 according to area_i ==/>/< area_j",
]

# Scene profiles are exact because (height, width, object count) is recoverable
# from the returned grid.  Difficulty chooses a deterministic four-slot
# curriculum, while an explicit scene_profile override is legal in every band.
_PROFILE_ROWS = (
    # name,                 h,  w, n, ties?, force same-top-row branch?
    ("c9x9_n3_rank",        9,  9, 3, False, True),
    ("c10x10_n3_tie",      10, 10, 3, True,  False),
    ("c10x12_n3_rank",     10, 12, 3, False, True),
    ("c11x11_n3_tie",      11, 11, 3, True,  False),
    ("c11x11_n4_tie",      11, 11, 4, True,  False),
    ("x13x15_n4_rank",     13, 15, 4, False, True),
    ("x15x17_n5_tie",      15, 17, 5, True,  False),
    ("x17x19_n5_rank",     17, 19, 5, False, True),
)
SCENE_PROFILES = tuple(row[0] for row in _PROFILE_ROWS)
SCHEDULE_PROFILES = SCENE_PROFILES
_PROFILE_BY_NAME = {
    name: {"h": h, "w": w, "n": n, "ties": ties, "same_row": same_row}
    for name, h, w, n, ties, same_row in _PROFILE_ROWS
}
_PROFILE_BY_SIGNATURE = {
    (h, w, n): name for name, h, w, n, _ties, _same_row in _PROFILE_ROWS
}
_PROFILES_BY_BAND = {
    "easy": (
        # Two n=3 and two n=4 slots make every rotated five-pair lesson
        # retain dynamic output-size evidence after any one query holdout.
        # Each count also contributes one tie and one bbox-vs-scan witness.
        "c9x9_n3_rank",
        "c10x10_n3_tie",
        "x13x15_n4_rank",
        "c11x11_n4_tie",
    ),
    "medium": (
        # Six slots intentionally pair tie/rank evidence at n=3/4/5.  The
        # three rank slots are bbox-vs-scan ordering witnesses, so every
        # rotated five-pair lesson retains one after any query holdout.  The
        # default diversity probe also sees all three output sizes.
        "c11x11_n3_tie",
        "c10x12_n3_rank",
        "c11x11_n4_tie",
        "x13x15_n4_rank",
        "x15x17_n5_tie",
        "x17x19_n5_rank",
    ),
    "hard": (
        "c11x11_n4_tie",
        "x13x15_n4_rank",
        "x15x17_n5_tie",
        "x17x19_n5_rank",
    ),
}

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "deterministic four-slot curriculum for the selected difficulty band",
        "valid": "c9x9_n3_rank|c10x10_n3_tie|c10x12_n3_rank|c11x11_n3_tie|c11x11_n4_tie|x13x15_n4_rank|x15x17_n5_tie|x17x19_n5_rank",
    }
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
MIN_STRICT_FRAC = 1.0
EXAMPLES_NEEDED = 4


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return str(difficulty)
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the deterministic four-slot semantic curriculum profile."""
    del seed
    profiles = _PROFILES_BY_BAND[_band(difficulty)]
    return profiles[int(sample_index) % len(profiles)]


def _rectangular_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if not 1 <= len(grid) <= 30 or not 1 <= width <= 30:
        return [f"grid dimensions must be in 1..30, found {len(grid)}x{width}"]
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return ["cells must be literal ARC integers 0..9"]
    return []


def _same_color_components(grid: Sequence[Sequence[int]]) -> list[dict[str, Any]]:
    """Same-color 4-connected components, matching ``(objects g 0)``."""
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    comps: list[dict[str, Any]] = []
    for r0 in range(height):
        for c0 in range(width):
            color = grid[r0][c0]
            if color == 0 or (r0, c0) in seen:
                continue
            queue = deque([(r0, c0)])
            seen.add((r0, c0))
            cells: list[tuple[int, int]] = []
            while queue:
                r, c = queue.popleft()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if not (0 <= nr < height and 0 <= nc < width):
                        continue
                    if (nr, nc) in seen or grid[nr][nc] != color:
                        continue
                    seen.add((nr, nc))
                    queue.append((nr, nc))
            rows = [r for r, _ in cells]
            cols = [c for _, c in cells]
            comps.append(
                {
                    "color": color,
                    "cells": cells,
                    "size": len(cells),
                    "r1": min(rows),
                    "c1": min(cols),
                    "r2": max(rows),
                    "c2": max(cols),
                }
            )
    return sorted(comps, key=lambda obj: (obj["r1"], obj["c1"]))


def _analysis(grid: Any) -> dict[str, Any]:
    errors = _rectangular_errors(grid)
    if errors:
        return {"errors": errors}
    height, width = len(grid), len(grid[0])
    comps = _same_color_components(grid)
    color_to_count: dict[int, int] = {}
    for obj in comps:
        color_to_count[obj["color"]] = color_to_count.get(obj["color"], 0) + 1
    repeated_colors = sorted(color for color, count in color_to_count.items() if count != 1)
    sizes = [obj["size"] for obj in comps]
    signature = (height, width, len(comps))
    return {
        "errors": errors,
        "height": height,
        "width": width,
        "objects": comps,
        "sizes": sizes,
        "colors": [obj["color"] for obj in comps],
        "repeated_colors": repeated_colors,
        "signature": signature,
        "scene_profile": _PROFILE_BY_SIGNATURE.get(signature),
    }


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    return nested if isinstance(nested, dict) else meta


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Accept canonical inputs; reject degenerate or rule-hiding lesson scenes."""
    del difficulty
    analysis = _analysis(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors

    comps = analysis["objects"]
    if len(comps) < 2:
        errors.append(f"expected at least 2 non-background objects, found {len(comps)}")
    if analysis["repeated_colors"]:
        errors.append(
            "each nonzero color must form one connected object; split colors: "
            f"{analysis['repeated_colors']}"
        )
    if any(obj["size"] < 2 for obj in comps):
        errors.append("single-cell objects hide meaningful area comparison structure")
    if len(comps) >= 2 and len(set(analysis["sizes"])) < 2:
        errors.append("all objects have equal area, so the comparison matrix would be all 1s")
    if not any(value == 0 for row in grid for value in row):
        errors.append("background 0 must be visible")

    requested = _meta_overrides(meta)
    if requested:
        observed = observe_overrides(grid)
        for name, value in requested.items():
            if name not in AXES:
                continue
            if observed.get(name) != value:
                errors.append(
                    f"override {name}={value!r} realized as {observed.get(name)!r}"
                )
    return errors


def observe_overrides(grid) -> dict[str, str | None]:
    """Recover the exact declared scene profile from returned dimensions/count."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        return {}
    return {"scene_profile": analysis["scene_profile"]}


def _normalize_shape(cells: Sequence[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return tuple(sorted((r - min_r, c - min_c) for r, c in cells))


def _transform_shape(
    cells: Sequence[tuple[int, int]], rng
) -> tuple[tuple[int, int], ...]:
    transformed = list(cells)
    if rng.randrange(2):
        transformed = [(r, -c) for r, c in transformed]
    for _ in range(rng.randrange(4)):
        transformed = [(c, -r) for r, c in transformed]
    return _normalize_shape(transformed)


_BASE_SHAPES: dict[int, tuple[tuple[int, int], ...]] = {
    2: ((0, 0), (0, 1)),
    3: ((0, 0), (1, 0), (1, 1)),  # bbox area 4
    4: ((0, 0), (0, 1), (1, 0), (1, 1)),  # compact bbox area 4
    5: ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
    6: ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)),
    7: ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 1), (2, 2)),
    8: ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2)),
    9: tuple((r, c) for r in range(3) for c in range(3)),
}
_SPREAD_FOUR = ((0, 0), (0, 1), (0, 2), (1, 1))  # bbox area 6


def _shape_for(size: int, *, spread_four: bool, rng) -> tuple[tuple[int, int], ...]:
    if size == 4 and spread_four:
        base = _SPREAD_FOUR
    else:
        base = _BASE_SHAPES[size]
    return _transform_shape(base, rng)


def _has_rise_and_fall(values: Sequence[int]) -> bool:
    return (
        any(values[i] < values[j] for i in range(len(values)) for j in range(i + 1, len(values)))
        and any(values[i] > values[j] for i in range(len(values)) for j in range(i + 1, len(values)))
    )


def _area_plan(rng, n: int, *, ties: bool) -> list[int]:
    """Return a varied area sequence in top-left object order."""
    if ties:
        extras = rng.sample([2, 3, 5, 6, 7, 8, 9], n - 2)
        values = [4, 4, *extras]
    else:
        extras = rng.sample([2, 5, 6, 7, 8, 9], n - 2)
        values = [3, 4, *extras]
    for _ in range(80):
        rng.shuffle(values)
        if _has_rise_and_fall(values):
            return list(values)
    raise ValueError("could not construct a non-monotone area curriculum")


def _scan_order_area_plan(rng, n: int) -> list[int]:
    """Expose bbox ordering versus row-major first-cell encounter ordering."""
    extras = rng.sample([3, 4, 5, 6, 8, 9], n - 2)
    return [7, 2, *extras]


def _anchors(rng, height: int, width: int, n: int, *, same_row: bool) -> list[tuple[int, int]]:
    """Choose stable placements, including an interleaved ordering witness."""
    top = rng.randint(0, 1)
    left = rng.randint(0, 1)
    right = rng.randint(width - 4, width - 3)
    bottom = rng.randint(height - 4, height - 3)

    if same_row:
        # The first object's bbox begins at ``left`` but its first occupied cell
        # is at ``left + 4``.  The second object's bbox begins at ``left + 2``
        # and its first occupied cell is there.  Thus bbox top-left order is
        # object 0 then 1, while a row-major encounter shortcut reverses them.
        candidates = [(top, left), (top, left + 2)]
        if n == 3:
            candidates.append((bottom, left))
        elif n == 4:
            candidates.extend(((bottom, left), (bottom, right)))
        elif n == 5:
            middle = (height // 2 - 1, width // 2 - 1)
            candidates.extend((middle, (bottom, left), (bottom, right)))
        else:
            raise ValueError(f"unsupported object count: {n}")
        return candidates

    top_right_r = top if same_row else min(top + 1, height - 3)
    bottom_left_r = bottom
    bottom_right_r = bottom if same_row else min(bottom + 1, height - 3)
    candidates = [
        (top, left),
        (top_right_r, right),
        (bottom_left_r, left),
        (bottom_right_r, right),
    ]
    if n == 3:
        candidates = candidates[:3]
    elif n == 5:
        middle = (height // 2 - 1, width // 2 - 1)
        candidates = [candidates[0], candidates[1], middle, candidates[2], candidates[3]]
    elif n != 4:
        raise ValueError(f"unsupported object count: {n}")
    return sorted(candidates)


_SCAN_LATE_SEVEN = (
    (0, 4),
    (1, 4),
    (2, 0),
    (2, 1),
    (2, 2),
    (2, 3),
    (2, 4),
)
_SCAN_EARLY_TWO = ((0, 0), (0, 1))


def _paint_shape(
    grid: list[list[int]], anchor: tuple[int, int], cells: Sequence[tuple[int, int]], color: int
) -> None:
    r0, c0 = anchor
    for dr, dc in cells:
        if grid[r0 + dr][c0 + dc] != 0:
            raise ValueError("internal placement overlap")
        grid[r0 + dr][c0 + dc] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")

    band = _band(difficulty)
    requested = overrides.get("scene_profile")
    if requested is not None and requested not in _PROFILE_BY_NAME:
        raise ValueError(f"unknown scene_profile: {requested!r}")
    scheduled = requested or schedule_profile(seed, sample_index, band)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    profile = ctx.draw_choice("scene_profile", [scheduled])
    spec = _PROFILE_BY_NAME[profile]
    height, width, n = spec["h"], spec["w"], spec["n"]
    rng = ctx.draw_rng("scene")

    areas = (
        _scan_order_area_plan(rng, n)
        if spec["same_row"]
        else _area_plan(rng, n, ties=spec["ties"])
    )
    anchors = _anchors(rng, height, width, n, same_row=spec["same_row"])

    # Assign two equal-area 4-cell objects different bbox areas in tie profiles.
    # In no-tie profiles, the 3-cell L and compact 4-cell square have equal bbox
    # area, so comparing bounding boxes rather than cell counts is also wrong.
    four_seen = 0
    shapes: list[tuple[tuple[int, int], ...]] = []
    for index, area in enumerate(areas):
        if spec["same_row"] and index == 0:
            shapes.append(_SCAN_LATE_SEVEN)
            continue
        if spec["same_row"] and index == 1:
            shapes.append(_SCAN_EARLY_TWO)
            continue
        spread_four = False
        if area == 4 and spec["ties"]:
            spread_four = four_seen == 1
            four_seen += 1
        shapes.append(_shape_for(area, spread_four=spread_four, rng=rng))

    # Color is a distractor, not an ordering or magnitude cue. Retry a handful
    # of deterministic color permutations until both color-value and color-sort
    # rivals are visibly false on the produced scene.
    for _ in range(40):
        colors = rng.sample(range(1, 10), n)
        grid = full_grid(height, width, 0)
        for anchor, shape, color in zip(anchors, shapes, colors):
            _paint_shape(grid, anchor, shape, color)
        official = rule_mirror(grid)
        if _rival_color_value(grid) == official:
            continue
        if _rival_color_order(grid) == official:
            continue
        return grid
    raise ValueError("could not realize color-independent semantic distractors")


def _matrix_from_values(values: Sequence[int]) -> list[list[int]]:
    return [
        [1 if a == b else (2 if a > b else 3) for b in values]
        for a in values
    ]


def rule_mirror(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    """Independent Python mirror for tests; canonical Racket remains authority."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid grid: " + "; ".join(analysis["errors"]))
    return _matrix_from_values(analysis["sizes"])


def strict_canonical_like(grid) -> list[str]:
    """Task-linked lawful manifold used by the strict semantic census."""
    errors = self_check(grid)
    if errors:
        return errors
    analysis = _analysis(grid)
    if analysis["signature"] not in _PROFILE_BY_SIGNATURE:
        errors.append(
            "shape/object-count signature is outside the canonical-anchored curriculum: "
            f"{analysis['signature']}"
        )
    if not 3 <= len(analysis["objects"]) <= 5:
        errors.append("curriculum requires 3..5 objects")
    if any(not 2 <= size <= 9 for size in analysis["sizes"]):
        errors.append("curriculum object areas must stay in 2..9 cells")
    return errors


def _rival_diagonal_ties_only(grid):
    """Wrong shortcut: color 1 means diagonal, not equality of two areas."""
    analysis = _analysis(grid)
    sizes = analysis["sizes"]
    n = len(sizes)
    return [
        [1 if i == j else (2 if sizes[i] > sizes[j] else 3) for j in range(n)]
        for i in range(n)
    ]


def _rival_position_rank(grid):
    """Wrong shortcut: later top-left objects are assumed to be larger."""
    n = len(_analysis(grid)["objects"])
    return [
        [1 if i == j else (2 if i > j else 3) for j in range(n)]
        for i in range(n)
    ]


def _rival_bbox_area(grid):
    """Wrong shortcut: compare bounding-box area instead of occupied cells."""
    analysis = _analysis(grid)
    values = [
        (obj["r2"] - obj["r1"] + 1) * (obj["c2"] - obj["c1"] + 1)
        for obj in analysis["objects"]
    ]
    return _matrix_from_values(values)


def _rival_color_value(grid):
    """Wrong shortcut: compare ARC color numbers instead of object areas."""
    return _matrix_from_values(_analysis(grid)["colors"])


def _rival_color_order(grid):
    """Wrong shortcut: order objects by color number, then compare real areas."""
    comps = sorted(_analysis(grid)["objects"], key=lambda obj: obj["color"])
    return _matrix_from_values([obj["size"] for obj in comps])


def _rival_reverse_same_row(grid):
    """Wrong tie-break: same-top-row objects are ordered right-to-left."""
    comps = sorted(_analysis(grid)["objects"], key=lambda obj: (obj["r1"], -obj["c1"]))
    return _matrix_from_values([obj["size"] for obj in comps])


def _rival_scan_encounter_order(grid):
    """Wrong shortcut: order objects by their first row-major occupied cell."""
    comps = sorted(_analysis(grid)["objects"], key=lambda obj: min(obj["cells"]))
    return _matrix_from_values([obj["size"] for obj in comps])


def _rival_fixed_three(grid):
    """Wrong shortcut: always emit the leading 3x3 comparison submatrix."""
    official = rule_mirror(grid)
    if len(official) <= 3:
        return official
    return [row[:3] for row in official[:3]]


SEMANTIC_RIVALS: dict[str, Callable[[Any], Any]] = {
    "diagonal_one_only": _rival_diagonal_ties_only,
    "position_rank_not_area": _rival_position_rank,
    "bbox_area_not_cell_area": _rival_bbox_area,
    "color_value_not_area": _rival_color_value,
    "color_order_not_top_left": _rival_color_order,
    "reverse_column_tiebreak": _rival_reverse_same_row,
    "scan_order_not_bbox_top_left": _rival_scan_encounter_order,
    "fixed_three_objects": _rival_fixed_three,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _off_diagonal_tie(grid) -> bool:
    sizes = _analysis(grid)["sizes"]
    return len(set(sizes)) < len(sizes)


def _same_row_tiebreak(grid) -> bool:
    analysis = _analysis(grid)
    comps = analysis["objects"]
    has_same_row = any(
        comps[i]["r1"] == comps[j]["r1"]
        for i in range(len(comps))
        for j in range(i + 1, len(comps))
    )
    return has_same_row and _rival_reverse_same_row(grid) != rule_mirror(grid)


def _n_at_least_four(grid) -> bool:
    return len(_analysis(grid)["objects"]) >= 4


def _scan_order_tiebreak(grid) -> bool:
    return _rival_scan_encounter_order(grid) != rule_mirror(grid)


SEMANTIC_WITNESSES = {
    "off_diagonal_area_tie": _off_diagonal_tie,
    "position_rank_disagrees": lambda grid: _rival_position_rank(grid) != rule_mirror(grid),
    "bbox_area_disagrees": lambda grid: _rival_bbox_area(grid) != rule_mirror(grid),
    "color_value_disagrees": lambda grid: _rival_color_value(grid) != rule_mirror(grid),
    "color_order_disagrees": lambda grid: _rival_color_order(grid) != rule_mirror(grid),
    "same_row_column_tiebreak": _same_row_tiebreak,
    "bbox_top_left_not_scan_order": _scan_order_tiebreak,
    "dynamic_object_count": _n_at_least_four,
}
WITNESS_RIVALS = {
    "off_diagonal_area_tie": ["diagonal_one_only"],
    "position_rank_disagrees": ["position_rank_not_area"],
    "bbox_area_disagrees": ["bbox_area_not_cell_area"],
    "color_value_disagrees": ["color_value_not_area"],
    "color_order_disagrees": ["color_order_not_top_left"],
    "same_row_column_tiebreak": ["reverse_column_tiebreak"],
    "bbox_top_left_not_scan_order": ["scan_order_not_bbox_top_left"],
    "dynamic_object_count": ["fixed_three_objects"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject any lesson whose demonstrations leave a named rival alive."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and oracle output"]

    reasons: list[str] = []
    object_counts: set[int] = set()
    tie_seen = False
    same_row_seen = False
    scan_order_seen = False
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output")
            continue
        try:
            expected = rule_mirror(pair["input"])
        except Exception as exc:
            reasons.append(f"demo {index} input is invalid: {exc}")
            continue
        if expected != pair["output"]:
            reasons.append(f"demo {index} disagrees with the area-comparison rule")
        object_counts.add(len(expected))
        tie_seen = tie_seen or _off_diagonal_tie(pair["input"])
        same_row_seen = same_row_seen or _same_row_tiebreak(pair["input"])
        scan_order_seen = scan_order_seen or _scan_order_tiebreak(pair["input"])

    try:
        query_expected = rule_mirror(query["input"])
    except Exception as exc:
        reasons.append(f"query input is invalid: {exc}")
        query_expected = None
    if query_expected is not None and query_expected != query["output"]:
        reasons.append("query disagrees with the area-comparison rule")

    if len(object_counts) < 2:
        reasons.append("demonstrations must vary object count to identify dynamic output size")
    if not tie_seen:
        reasons.append("demonstrations must include an off-diagonal equal-area pair")
    if not same_row_seen:
        reasons.append("demonstrations must expose the same-row column tie-break")
    if not scan_order_seen:
        reasons.append("demonstrations must distinguish bbox order from scan encounter order")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(competitor(pair["input"]) == pair["output"] for pair in demos)
        if survives and competitor(query["input"]) != query["output"]:
            reasons.append(f"demonstrations do not falsify rival: {name}")
    return reasons
