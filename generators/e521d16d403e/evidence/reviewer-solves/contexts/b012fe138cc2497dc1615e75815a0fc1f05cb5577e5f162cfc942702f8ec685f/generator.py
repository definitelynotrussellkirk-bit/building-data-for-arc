"""Largest eligible left-right symmetric component, with an exact curriculum.

The unchanged Racket authority uses same-color four-connected components,
requires bbox width > 1, compares ALL pixels in the component's bounding box,
and chooses the component with most occupied cells. Generation reserves whole
bounding boxes so another object cannot corrupt an otherwise symmetric crop.

Default lessons cycle through four profiles. Two 10x10 profiles distinguish
occupied size, bbox area and the width-one exclusion. Two broader profiles
repeat the winner's color on a disconnected asymmetric object. Both pairs
reverse which eligible object comes first, and profiles 0 and 2 place a smaller
eligible object lower than the winner. Three demonstrations from any four
consecutive default draws retain a counterexample to every declared rival.
Explicit controls use an exact constructive layout, without that lesson claim.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e521d16d403e"
TASK_ID = "e521d16d403e"
VERSION = "4.1.0"
RULE_HASH = "9d224076bec5"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.40
SUMMARY = (
    "Extract the bbox of the largest eligible left-right symmetric object. "
    "Objects use same-color four-connectivity; eligibility requires width > 1 "
    "and exact color equality of every mirrored bbox pixel. Size counts object "
    "cells, not bbox area. Default four-draw lessons distinguish larger "
    "ineligible objects, varying occupied-size rank, smaller symmetric decoys, scan order, bbox area, "
    "width-one bars and disconnected objects sharing a color. Half the "
    "default profiles use canonical 10x10 grids with three nonzero colors; "
    "two profiles refute the canonical-fitting bottommost-eligible shortcut."
)
INVARIANTS = [
    "background is 0; all pixels are integers 0..9",
    "objects are same-color four-connected components",
    "an eligible bbox has width > 1 and all its raw pixels are LR-symmetric",
    "exactly one eligible object has maximum occupied-cell count",
    "generated object bounding boxes have at least one separating blank row or column",
    "the selected curriculum contains at least one noneligible distractor component",
    "all six advertised controls are observable from the grid and honored jointly",
]

AXES = {
    "grid_h": {"type": "int", "default": "10 on two profiles; rng 14..22 otherwise", "valid": "10..22"},
    "grid_w": {"type": "int", "default": "10 on two profiles; rng 14..22 otherwise", "valid": "10..22"},
    "sym_h": {"type": "int", "default": "2 on two profiles; rng 2..6 otherwise", "valid": "2..6"},
    "sym_w": {"type": "int", "default": "4 on two profiles; rng 2..7 otherwise", "valid": "2..7"},
    "n_asym": {"type": "int", "default": "2 noneligible components", "valid": "1..3"},
    "n_sym_decoy": {"type": "int", "default": "1", "valid": "0..2"},
}
_BOUNDS = {"grid_h": (10, 22), "grid_w": (10, 22), "sym_h": (2, 6),
           "sym_w": (2, 7), "n_asym": (1, 3), "n_sym_decoy": (0, 2)}
SCHEDULE_PROFILES = (0, 1, 2, 3)


def schedule_profile(seed, sample_index, difficulty=None):
    """Seed-offset four-step curriculum; every consecutive window spans it."""
    return (seed + sample_index) % 4


def _objects(grid, *, by_color=False):
    """Pixel-derived objects in the reference's row-major discovery order."""
    h, w = len(grid), len(grid[0])
    seen, result = set(), []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            cells = [(r, c)]
            seen.add((r, c))
            if by_color:
                cells = [(rr, cc) for rr in range(h) for cc in range(w)
                         if grid[rr][cc] == color]
                seen.update(cells)
            else:
                for rr, cc in cells:
                    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                        nr, nc = rr + dr, cc + dc
                        if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                                and grid[nr][nc] == color):
                            seen.add((nr, nc))
                            cells.append((nr, nc))
            r0, r1 = min(p[0] for p in cells), max(p[0] for p in cells)
            c0, c1 = min(p[1] for p in cells), max(p[1] for p in cells)
            crop = [row[c0:c1 + 1] for row in grid[r0:r1 + 1]]
            result.append({"color": color, "size": len(cells), "bbox": (r0, c0, r1, c1),
                           "height": r1 - r0 + 1, "width": c1 - c0 + 1,
                           "area": (r1 - r0 + 1) * (c1 - c0 + 1), "crop": crop,
                           "lr": all(row == row[::-1] for row in crop),
                           "ud": crop == crop[::-1]})
    return result


def _eligible(components):
    return [obj for obj in components if obj["width"] > 1 and obj["lr"]]


def _winner(components):
    candidates = _eligible(components)
    return max(candidates, key=lambda obj: obj["size"]) if candidates else None


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Curriculum domain: valid pixels and a unique eligible maximum.

    The reference's first-object fallback and stable tied maxima are executable,
    but are deliberately excluded from generation. The selected curriculum also
    requires at least one noneligible distractor; touching different colors and
    disconnected or width-one fragments remain lawful ways to supply it.
    """
    if (not isinstance(grid, list) or not grid or not isinstance(grid[0], list)
            or not grid[0] or any(not isinstance(row, list) or len(row) != len(grid[0]) for row in grid)):
        return ["grid must be a non-empty rectangular list of rows"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["grid pixels must be integers 0..9 (not bools or coerced values)"]
    components = _objects(grid)
    candidates = _eligible(components)
    if not candidates:
        return ["expected an LR-symmetric raw bbox of width greater than one"]
    if len(candidates) == len(components):
        return ["expected at least one noneligible distractor component"]
    largest = max(obj["size"] for obj in candidates)
    if sum(obj["size"] == largest for obj in candidates) != 1:
        return ["largest eligible object must be unique by occupied-cell count"]
    return []


def observe_overrides(grid):
    """Measure exact controls from fresh pixels, with no generation metadata."""
    components = _objects(grid)
    candidates = _eligible(components)
    winner = _winner(components)
    if winner is None:
        raise ValueError("cannot observe answer dimensions without an eligible object")
    return {"grid_h": len(grid), "grid_w": len(grid[0]),
            "sym_h": winner["height"], "sym_w": winner["width"],
            "n_asym": len(components) - len(candidates), "n_sym_decoy": len(candidates) - 1}


def strict_canonical_like(grid):
    reasons = self_check(grid)
    if reasons:
        return reasons
    if len(grid) != 10 or len(grid[0]) != 10:
        reasons.append("canonical profile uses a 10x10 board")
    if len({value for row in grid for value in row}) != 4 or not any(0 in row for row in grid):
        reasons.append("canonical profile uses background 0 and three nonzero colors")
    return reasons


def _draw_axis(ctx, name, default):
    # Record a curriculum-selected default as a true default, not a fabricated
    # caller override. Explicit controls always use their full declared range.
    lo, hi = _BOUNDS[name] if name in ctx.overrides else (default, default)
    return ctx.draw_int(name, lo, hi)


def _symmetric_shape(rng, height, width):
    """Three connected shape families with exact bounds, including even widths."""
    shape = [[0] * width for _ in range(height)]
    family = rng.randrange(3)
    if family == 0:
        # Nested centered row intervals, connected by a one/two-cell spine.
        bridge = rng.randrange(height)
        for r in range(height):
            extent = width // 2 if r == bridge else rng.randint(0 if width % 2 else 1, width // 2)
            left = width // 2 - extent
            right = width // 2 + extent + (width % 2)
            for c in range(left, right):
                shape[r][c] = 1
    elif family == 1:
        # Edge-connected U/comb shapes; a complete row joins the two sides.
        bridge = rng.randrange(height)
        for r in range(height):
            shape[r][0] = shape[r][-1] = 1
            if r == bridge or rng.random() < 0.35:
                shape[r] = [1] * width
    else:
        # Hollow frames with optional mirrored interior fill.
        for r in range(height):
            for c in range(width):
                if r in (0, height - 1) or c in (0, width - 1):
                    shape[r][c] = 1
        for r in range(1, height - 1):
            for c in range(1, (width + 1) // 2):
                if rng.random() < 0.35:
                    # Add full mirrored inward runs so no island is created.
                    for cc in range(1, c + 1):
                        shape[r][cc] = shape[r][width - 1 - cc] = 1
    if rng.randrange(2):
        shape.reverse()
    return shape


def _small_asymmetric(rng):
    shape = [[1, 1], [1, 1]]
    shape[rng.randrange(2)][rng.randrange(2)] = 0
    return shape


def _paint(grid, shape, row, col, color):
    for r, values in enumerate(shape):
        for c, value in enumerate(values):
            if value:
                grid[row + r][col + c] = color


def _render(ctx, height, width, placements, *, allow_vertical_flip=False):
    """Translate and reflect an already separated bbox layout; never retry."""
    rng = ctx.draw_rng("placement")
    used_h = max(r + len(shape) for shape, r, _c, _color in placements)
    used_w = max(c + len(shape[0]) for shape, _r, c, _color in placements)
    row_shift = rng.randint(0, height - used_h)
    col_shift = rng.randint(0, width - used_w)
    grid = full_grid(height, width, 0)
    for shape, r, c, color in placements:
        _paint(grid, shape, r + row_shift, c + col_shift, color)
    if rng.randrange(2):
        grid = [row[::-1] for row in grid]
    if allow_vertical_flip and rng.randrange(2):
        grid.reverse()
    return grid


def _exact_layout(ctx, values, colors):
    """A 10x10 core proves every advertised joint override is constructible."""
    rng = ctx.draw_rng("shape")
    target = _symmetric_shape(rng, values["sym_h"], values["sym_w"])
    placements = [(target, 0, 0, colors[0])]
    for i in range(values["n_asym"]):
        placements.append((_small_asymmetric(rng), 7, 3 * i, colors[1]))
    for i in range(values["n_sym_decoy"]):
        placements.append(([[1, 1]], 2 * i, values["sym_w"] + 1, colors[2]))
    return _render(ctx, values["grid_h"], values["grid_w"], placements, allow_vertical_flip=True)


def _core_layout(ctx, phase, colors):
    """Size-six answer, area-nine size-five cross, and two larger ineligible components."""
    rng = ctx.draw_rng("shape")
    target = rng.choice(([[1, 1, 1, 1], [0, 1, 1, 0]],
                         [[1, 0, 0, 1], [1, 1, 1, 1]]))
    target = [list(row) for row in target]
    if rng.randrange(2):
        target.reverse()
    cross = [[0, 1, 0], [1, 1, 1], [0, 1, 0]]
    bar = [[1] for _ in range(rng.randint(7, 9))]
    large_asym = [[1] * 3 for _ in range(3)]
    large_asym[rng.choice((0, 2))][rng.choice((0, 2))] = 0
    shapes = [target, cross, bar]
    column_order = list(range(3))
    rng.shuffle(column_order)
    columns, col = {}, 0
    for index in column_order:
        columns[index] = col
        col += len(shapes[index][0]) + 1
    if phase == 0:
        target_row = rng.randint(0, 2)
        cross_row = rng.randint(target_row + 1, 7)
    else:
        cross_row = rng.randint(0, 2)
        target_row = rng.randint(cross_row + 1, 4)
    placements = [(target, target_row, columns[0], colors[0]),
                  (cross, cross_row, columns[1], colors[2]),
                  (bar, rng.randint(0, 10 - len(bar)), columns[2], colors[1]),
                  (large_asym, target_row + 3, columns[0] + rng.randrange(2), colors[1])]
    return _render(ctx, 10, 10, placements)


def _broad_layout(ctx, phase, values, colors):
    rng = ctx.draw_rng("shape")
    height, width = values["sym_h"], values["sym_w"]
    target = _symmetric_shape(rng, height, width)
    size = sum(map(sum, target))
    # Even a completely solid target loses the unfiltered size contest.
    large_asym = [[1] * (width + 1) for _ in range(height)]
    large_asym[rng.choice((0, height - 1))][rng.choice((0, width))] = 0
    decoys = ([[1, 1]], [[1, 1, 1]], [[1, 1], [1, 1]],
              [[1, 1, 1], [0, 1, 0]], [[0, 1, 0], [1, 1, 1], [0, 1, 0]],
              [[1, 0, 0, 1], [1, 1, 1, 1]])
    decoy = rng.choice([shape for shape in decoys if sum(map(sum, shape)) < size])
    decoy = [list(row) for row in decoy]
    if rng.randrange(2):
        decoy.reverse()
    # Profile 2 keeps the winner first in scan order but puts the smaller
    # eligible decoy strictly lower. Together with compact profile 0 this gives
    # every three-demo rotation a witness against the canonical-fitting
    # "choose the bottommost eligible component" shortcut.
    target_row = 0 if phase == 2 else 1
    decoy_row = target_row + height + 1 if phase == 2 else 0
    side_col = width + 2
    placements = [(target, target_row, 0, colors[0]),
                  (large_asym, target_row + height + 1, 0, colors[1]),
                  (decoy, decoy_row, side_col, colors[2]),
                  (_small_asymmetric(rng), decoy_row + len(decoy) + 1, side_col, colors[0])]
    return _render(ctx, values["grid_h"], values["grid_w"], placements)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if type(seed) is not int:
        raise TypeError(f"seed must be an integer, got {type(seed).__name__}")
    if type(sample_index) is not int:
        raise TypeError(
            f"sample_index must be an integer, got {type(sample_index).__name__}")
    if sample_index < 0:
        raise ValueError(f"sample_index must be nonnegative, got {sample_index}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown or unsupported override(s): {', '.join(unknown)}")
    for name, value in overrides.items():
        if type(value) is not int:
            raise TypeError(f"{name} must be an integer, got {type(value).__name__}")
        lo, hi = _BOUNDS[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name} must be in {lo}..{hi}, got {value}")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard or None")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    phase = schedule_profile(seed, sample_index, difficulty)
    defaults_rng = ctx.draw_rng("curriculum_defaults")
    if phase < 2:
        defaults = {"grid_h": 10, "grid_w": 10, "sym_h": 2, "sym_w": 4,
                    "n_asym": 2, "n_sym_decoy": 1}
    else:
        lo, hi = {"easy": (14, 16), "medium": (16, 20), "hard": (18, 22)}.get(difficulty, (16, 20))
        defaults = {"grid_h": defaults_rng.randint(lo, hi), "grid_w": defaults_rng.randint(lo, hi),
                    "sym_h": defaults_rng.randint(2, 6), "sym_w": defaults_rng.randint(2, 7),
                    "n_asym": 2, "n_sym_decoy": 1}
    values = {name: _draw_axis(ctx, name, defaults[name]) for name in AXES}
    colors = ctx.draw_distinct_colors("palette", n=3, exclude={0})
    if overrides:
        return _exact_layout(ctx, values, colors)
    if phase < 2:
        return _core_layout(ctx, phase, colors)
    return _broad_layout(ctx, phase, values, colors)


def _predict(grid, mode="reference"):
    components = _objects(grid, by_color=mode == "group_by_color")
    if not components:
        return None
    if mode == "second_largest_object":
        ranked = sorted(components, key=lambda obj: obj["size"], reverse=True)
        return ranked[min(1, len(ranked) - 1)]["crop"]
    if mode == "largest_object":
        candidates = components
    elif mode == "width_one_allowed":
        candidates = [obj for obj in components if obj["lr"]]
    elif mode == "either_axis":
        candidates = [obj for obj in components if (obj["lr"] and obj["width"] > 1)
                      or (obj["ud"] and obj["height"] > 1)]
    else:
        candidates = _eligible(components)
    if not candidates:
        return components[0]["crop"]
    if mode == "first_lr":
        selected = candidates[0]
    elif mode == "last_lr":
        selected = candidates[-1]
    elif mode == "smallest_lr":
        selected = min(candidates, key=lambda obj: obj["size"])
    elif mode == "bottommost_lr":
        selected = max(candidates, key=lambda obj: (obj["bbox"][2], obj["bbox"][0]))
    else:
        selected = max(candidates, key=lambda obj: obj["area"] if mode == "largest_bbox_lr" else obj["size"])
    return selected["crop"]


def _largest_object(grid):
    return _predict(grid, "largest_object")


def _second_largest_object(grid):
    return _predict(grid, "second_largest_object")


def _first_lr(grid):
    return _predict(grid, "first_lr")


def _last_lr(grid):
    return _predict(grid, "last_lr")


def _smallest_lr(grid):
    return _predict(grid, "smallest_lr")


def _largest_bbox_lr(grid):
    return _predict(grid, "largest_bbox_lr")


def _bottommost_lr(grid):
    return _predict(grid, "bottommost_lr")


def _width_one_allowed(grid):
    return _predict(grid, "width_one_allowed")


def _either_axis(grid):
    return _predict(grid, "either_axis")


def _group_by_color(grid):
    return _predict(grid, "group_by_color")


SEMANTIC_RIVALS = {"largest_object": _largest_object, "first_lr": _first_lr, "last_lr": _last_lr,
                   "smallest_lr": _smallest_lr, "largest_bbox_lr": _largest_bbox_lr,
                   "bottommost_lr": _bottommost_lr, "width_one_allowed": _width_one_allowed,
                   "either_axis": _either_axis, "group_by_color": _group_by_color,
                   "second_largest_object": _second_largest_object}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {name: rule for name, rule in SEMANTIC_RIVALS.items()
                       if name not in ("largest_object", "second_largest_object")}


def _counterexample(grid, rival):
    return bool(_winner(_objects(grid)) is not None and _predict(grid) != rival(grid))


def _larger_ineligible(grid):
    return _counterexample(grid, _largest_object)


def _answer_not_second_largest(grid):
    return _counterexample(grid, _second_largest_object)


def _winner_after_decoy(grid):
    return _counterexample(grid, _first_lr)


def _winner_before_decoy(grid):
    return _counterexample(grid, _last_lr)


def _smaller_eligible(grid):
    return _counterexample(grid, _smallest_lr)


def _cell_count_not_bbox(grid):
    return _counterexample(grid, _largest_bbox_lr)


def _answer_not_bottommost(grid):
    return _counterexample(grid, _bottommost_lr)


def _width_one_excluded(grid):
    return _counterexample(grid, _width_one_allowed)


def _left_right_not_either_axis(grid):
    return _counterexample(grid, _either_axis)


def _component_not_color(grid):
    return _counterexample(grid, _group_by_color)


SEMANTIC_WITNESSES = {"larger_ineligible": _larger_ineligible,
                       "answer_not_second_largest": _answer_not_second_largest,
                       "winner_after_decoy": _winner_after_decoy,
                       "winner_before_decoy": _winner_before_decoy,
                       "smaller_eligible": _smaller_eligible,
                       "cell_count_not_bbox": _cell_count_not_bbox,
                       "answer_not_bottommost": _answer_not_bottommost,
                       "width_one_excluded": _width_one_excluded,
                       "left_right_not_either_axis": _left_right_not_either_axis,
                       "component_not_color": _component_not_color}
WITNESS_RIVALS = {"larger_ineligible": ["largest_object"], "winner_after_decoy": ["first_lr"],
                 "answer_not_second_largest": ["second_largest_object"],
                 "winner_before_decoy": ["last_lr"], "smaller_eligible": ["smallest_lr"],
                 "cell_count_not_bbox": ["largest_bbox_lr"],
                 "answer_not_bottommost": ["bottommost_lr"],
                 "width_one_excluded": ["width_one_allowed"],
                 "left_right_not_either_axis": ["either_axis"], "component_not_color": ["group_by_color"]}


def lesson_identifiable(demos, query):
    """Finite declared-rival check; this does not claim universal induction."""
    return [f"{name} fits every demonstration but disagrees on the query"
            for name, rival in LESSON_COMPETITORS.items()
            if all(rival(pair["input"]) == pair["output"] for pair in demos)
            and rival(query["input"]) != query["output"]]
