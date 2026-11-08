"""Inputs for symmetry completion inside a geometric frame (S3_H4).

The unchanged Racket authority selects the largest monochrome rectangular
outline, then reflects its contents about the frame's vertical axis. This
sampler constructs conflict-free odd-width instances; it never supplies labels.
Python completions below are explicitly diagnostic rivals/witnesses only.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.objects import find_objects

GENERATOR_ID = "9126300ec565"
TASK_ID = GENERATOR_ID
RULE_HASH = "3b7f62466c00"
VERSION = "2.0.0"
SUMMARY = "Complete multicolor reflection about the axis of a movable rectangular frame."
INVARIANTS = [
    "background is 0; the unique largest monochrome rectangular outline is the frame",
    "the selected frame has odd width; frame color is a geometric role, not a literal",
    "interior content excludes the frame color and has no conflicting reflection partners",
    "ordinary draws contain 3..6 distinct off-axis reflection orbits and are never identity",
    "axis cells and exterior distractors remain unchanged under the selected Racket rule",
]
AXES = {
    "grid_h": {"type": "int", "default": "canonical anchors or 7..24", "valid": "7..24"},
    "grid_w": {"type": "int", "default": "canonical anchors or 9..25", "valid": "9..25"},
    "frame_h": {"type": "int", "default": "canonical anchors or fitting 5..11", "valid": "5..11"},
    "frame_w": {"type": "int", "default": "canonical anchors or fitting odd width", "valid": "7|9|11|13"},
    "frame_color": {"type": "int", "default": "alternating canonical and other color roles", "valid": "1..9"},
    "n_marks": {"type": "int", "default": "band-weighted 4..6 at anchors; broad 3..6", "valid": "3..6"},
    "n_colors": {"type": "int", "default": "2 or 3 at anchors, otherwise 1..3", "valid": "1..3"},
    "n_axis": {"type": "int", "default": "0..2", "valid": "0..2"},
    "n_distractors": {"type": "int", "default": "two absent, two present, one free teaching phase", "valid": "0..3"},
    "content_side": {"type": "str", "default": "right,mixed,right,mixed,free teaching phases", "valid": "left|right|mixed"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [
    ("grid_h", "frame_h"),
    ("grid_w", "frame_w"),
    ("grid_h", "grid_w", "frame_h", "frame_w", "n_distractors"),
]
EXAMPLES_NEEDED = 4
# Five teaching phases, four morphology phases and two color-role phases have
# combined period 20 at a fixed seed. Pixel draws still use the full keyed index.
LESSON_SCHEDULE_PERIOD = 20
_ANCHORS = ((11, 13, 7, 9, 3), (12, 14, 8, 9, 2), (13, 15, 9, 11, 3))
_DOMAINS = {
    "grid_h": tuple(range(7, 25)), "grid_w": tuple(range(9, 26)),
    "frame_h": tuple(range(5, 12)), "frame_w": (7, 9, 11, 13),
    "frame_color": tuple(range(1, 10)), "n_marks": (3, 4, 5, 6),
    "n_colors": (1, 2, 3), "n_axis": (0, 1, 2),
    "n_distractors": (0, 1, 2, 3), "content_side": ("left", "right", "mixed"),
}


def _choice(ctx, name, values, preferred=None):
    """Exact overrides use the feasible domain, never a difficulty subrange."""
    if not values:
        raise ValueError(f"no feasible values for {name}")
    options = values
    if ctx.overrides.get(name) is None and preferred is not None:
        options = [value for value in preferred if value in values] or values
    return ctx.draw_choice(name, options)


def _draw_frame(grid, top, left, bottom, right, color):
    for column in range(left, right + 1):
        grid[top][column] = grid[bottom][column] = color
    for row in range(top, bottom + 1):
        grid[row][left] = grid[row][right] = color


def _put_distractors(grid, bounds, count, colors, rng):
    if not count:
        return
    top, left, bottom, right = bounds
    outside = [(r, c) for r in range(len(grid)) for c in range(len(grid[0]))
               if not (top <= r <= bottom and left <= c <= right)]
    if len(outside) < count:
        raise ValueError("grid_h/grid_w and frame_h/frame_w leave insufficient space for n_distractors")
    # On ordinary draws, an exterior row exists. Reserve a blank partner for
    # one distractor so a 'mirror the whole grid' rival really changes a cell.
    witness = [(r, c) for r, c in outside
               if (r < top or r > bottom) and left < c < right and 2*c != left+right]
    selected = []
    if witness:
        first = rng.choice(witness)
        reserved = (first[0], left + right - first[1])
        selected.append(first)
        outside = [point for point in outside if point not in (first, reserved)]
    selected.extend(rng.sample(outside, count - len(selected)))
    for r, c in selected:
        grid[r][c] = rng.choice(colors)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is None:
            continue
        if name != "content_side" and type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
        if value not in _DOMAINS[name]:
            raise ValueError(f"{name}={value!r} outside its declared domain")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard or None")
    for canvas, frame in (("grid_h", "frame_h"), ("grid_w", "frame_w")):
        if overrides.get(canvas) is not None and overrides.get(frame) is not None:
            if overrides[frame] > overrides[canvas]:
                raise ValueError(f"{frame} cannot exceed {canvas}")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    anchor = _ANCHORS[sample_index % 4] if sample_index % 4 < 3 else None
    phase = (sample_index + seed % 5) % 5
    min_h = max(7, (overrides.get("frame_h") or 5) + 1)
    min_w = max(9, (overrides.get("frame_w") or 7) + 1)
    hs = _DOMAINS["grid_h"] if overrides.get("grid_h") is not None else list(range(min_h, 25))
    ws = _DOMAINS["grid_w"] if overrides.get("grid_w") is not None else list(range(min_w, 26))
    h = _choice(ctx, "grid_h", hs, [anchor[0]] if anchor else None)
    w = _choice(ctx, "grid_w", ws, [anchor[1]] if anchor else None)
    max_fh = min(11, h if overrides.get("frame_h") is not None else h-1)
    max_fw = w if overrides.get("frame_w") is not None else w-1
    fh = _choice(ctx, "frame_h", list(range(5, max_fh+1)), [anchor[2]] if anchor else None)
    fw = _choice(ctx, "frame_w", [v for v in _DOMAINS["frame_w"] if v <= max_fw],
                 [anchor[3]] if anchor else None)
    canonical_color_phase = (sample_index + (seed // 4) % 2) % 2 == 0
    pool = (4, 6, 8) if canonical_color_phase else (1, 2, 3, 5, 7, 9)
    frame_color = _choice(ctx, "frame_color", _DOMAINS["frame_color"], pool)
    # Higher bands add unfinished reflection orbits. All exact controls keep
    # their full domain; every band retains sparse four-mark canonical support.
    favored_marks = {"easy": (4, 4, 4, 5, 6),
                     "medium": (4, 5, 5, 5, 6),
                     "hard": (4, 5, 6, 6, 6)}.get(difficulty, (4, 5, 6))
    n_marks = _choice(ctx, "n_marks", _DOMAINS["n_marks"],
                      favored_marks if anchor else (3, *favored_marks))
    n_colors = _choice(ctx, "n_colors", _DOMAINS["n_colors"], [anchor[4]] if anchor else None)
    n_axis = _choice(ctx, "n_axis", _DOMAINS["n_axis"])
    # Two zero-noise right/mixed inputs refute noise-gated symmetry. Two
    # positive-noise inputs refute mirroring exterior cells. A free fifth phase
    # restores every side/noise combination. Any single holdout leaves a witness
    # of both conditions; ordinary lessons therefore use four demonstrations.
    noise_plan = (0, 0, 1 + seed % 3, 1 + (seed // 3) % 3, seed % 4)
    side_plan = ("right", "mixed", "right", "mixed", ("left", "right", "mixed")[(seed // 4) % 3])
    capacity = h*w - fh*fw
    n_noise = _choice(ctx, "n_distractors", [n for n in _DOMAINS["n_distractors"] if n <= capacity],
                      [noise_plan[phase]])
    side = _choice(ctx, "content_side", _DOMAINS["content_side"], [side_plan[phase]])
    rng = ctx.draw_rng("placement")
    top = rng.randrange(h - fh + 1)
    positions = list(range(w - fw + 1))
    if phase != 4:
        positions = [left for left in positions if 2*left + fw != w] or positions
    left = rng.choice(positions)
    bottom, right = top + fh - 1, left + fw - 1
    axis = (left + right) // 2
    grid = full_grid(h, w, 0)
    _draw_frame(grid, top, left, bottom, right, frame_color)
    palette_rng = ctx.draw_rng("content_palette")
    colors = palette_rng.sample([c for c in range(1, 10) if c != frame_color], n_colors)
    orbits = [(r, c) for r in range(top+1, bottom) for c in range(left+1, axis)]
    slots = ctx.draw_rng("content_orbits").sample(orbits, n_marks)
    if side == "mixed":
        sides = ["left" if i % 2 == 0 else "right" for i in range(n_marks)]
        rng.shuffle(sides)
    else:
        sides = [side] * n_marks
    for i, ((r, c), selected_side) in enumerate(zip(slots, sides)):
        column = c if selected_side == "left" else left + right - c
        grid[r][column] = colors[i % n_colors]
    for r in ctx.draw_rng("axis_rows").sample(list(range(top+1, bottom)), n_axis):
        grid[r][axis] = palette_rng.choice(colors)
    _put_distractors(grid, (top, left, bottom, right), n_noise, colors,
                     ctx.draw_rng("exterior_content"))
    return grid


def _frame(grid):
    candidates = []
    for obj in find_objects(grid, univalued=True, diagonal=False, without_bg=True, bg=0):
        cells = {point for _, point in obj}
        top, bottom = min(r for r, _ in cells), max(r for r, _ in cells)
        left, right = min(c for _, c in cells), max(c for _, c in cells)
        if bottom-top < 2 or right-left < 2:
            continue
        expected = {(r, c) for r in range(top, bottom+1) for c in range(left, right+1)
                    if r in (top, bottom) or c in (left, right)}
        if cells == expected:
            color = next(iter(obj))[0]
            candidates.append((len(cells), top, left, bottom, right, color))
    if not candidates:
        raise ValueError("no monochrome rectangular outline frame")
    candidates.sort(reverse=True)
    if len(candidates) > 1 and candidates[0][0] == candidates[1][0]:
        raise ValueError("largest rectangular frame is tied")
    return candidates[0][1:]


def self_check(grid, *, difficulty=None, meta=None):
    """Validate pixels and the documented domain; metadata never bypasses it."""
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected nonempty rows"]
    if any(not isinstance(row, (list, tuple)) or len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer colors 0..9, excluding booleans"]
    try:
        top, left, bottom, right, color = _frame(grid)
    except ValueError as exc:
        return [str(exc)]
    errors = []
    if (right-left+1) % 2 == 0:
        errors.append("frame width must be odd for the documented integer-axis domain")
    axis = (left+right) // 2
    marks = []
    for r in range(top+1, bottom):
        for c in range(left+1, right):
            value = grid[r][c]
            if value == color:
                errors.append("interior frame-color content is outside the declared domain")
            elif value and c != axis:
                marks.append((r, c))
                partner = grid[r][left+right-c]
                if partner not in (0, value):
                    errors.append("opposing cells contain conflicting colors")
    if not marks:
        errors.append("no off-axis interior content to complete")
    return sorted(set(errors))


def observe_overrides(grid):
    """Recover all exact controls from input pixels, including actual mark counts."""
    top, left, bottom, right, color = _frame(grid)
    axis = (left+right) // 2
    content = [(r, c, grid[r][c]) for r in range(top+1, bottom)
               for c in range(left+1, right) if grid[r][c] not in (0, color)]
    sides = {"left" if c < axis else "right" for _, c, _ in content if c != axis}
    return {
        "grid_h": len(grid), "grid_w": len(grid[0]),
        "frame_h": bottom-top+1, "frame_w": right-left+1, "frame_color": color,
        "n_marks": sum(c != axis for _, c, _ in content),
        "n_colors": len({value for _, _, value in content}),
        "n_axis": sum(c == axis for _, c, _ in content),
        "n_distractors": sum(value != 0 for r, row in enumerate(grid) for c, value in enumerate(row)
                             if not (top <= r <= bottom and left <= c <= right)),
        "content_side": "mixed" if len(sides) > 1 else next(iter(sides), "none"),
    }


def strict_canonical_like(grid):
    return self_check(grid)


def _diagnostic_completion(grid, *, canvas_axis=False, only_left=False,
                           whole_grid=False, first_color_only=False):
    """Python diagnostic, never used to generate or certify reference labels."""
    top, left, bottom, right, color = _frame(grid)
    out = [list(row) for row in grid]
    axis_sum = len(grid[0])-1 if canvas_axis else left+right
    rows = range(len(grid)) if whole_grid else range(top+1, bottom)
    columns = range(len(grid[0])) if whole_grid else range(left+1, right)
    seen = set()
    for r in rows:
        for c in columns:
            value = grid[r][c]
            if value in (0, color) or (only_left and 2*c >= left+right):
                continue
            if first_color_only and value in seen:
                continue
            seen.add(value)
            mirror = axis_sum-c
            allowed = 0 <= mirror < len(grid[0]) if whole_grid else left < mirror < right
            if allowed:
                out[r][mirror] = value
    return out


def _identity(grid):
    return [list(row) for row in grid]


def _yellow_only(grid):
    return _diagnostic_completion(grid) if _frame(grid)[4] == 4 else _identity(grid)


def _known_frame_colors(grid):
    return _diagnostic_completion(grid) if _frame(grid)[4] in (4, 6, 8) else _identity(grid)


def _canvas_axis(grid):
    return _diagnostic_completion(grid, canvas_axis=True)


def _left_only(grid):
    return _diagnostic_completion(grid, only_left=True)


def _whole_grid(grid):
    return _diagnostic_completion(grid, whole_grid=True)


def _first_color_only(grid):
    return _diagnostic_completion(grid, first_color_only=True)


def _left_without_noise(grid):
    if observe_overrides(grid)["n_distractors"] == 0:
        return _left_only(grid)
    return _diagnostic_completion(grid)


SEMANTIC_RIVALS = {
    "identity": _identity, "yellow_frame_only": _yellow_only,
    "canonical_frame_colors_only": _known_frame_colors, "canvas_axis": _canvas_axis,
    "left_content_only": _left_only, "mirror_exterior_too": _whole_grid,
    "first_cell_per_color": _first_color_only,
    "left_only_without_exterior_noise": _left_without_noise,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "canonical_frame_colors_only": _known_frame_colors,
    "left_content_only": _left_only, "mirror_exterior_too": _whole_grid,
    "left_only_without_exterior_noise": _left_without_noise,
}


def _refutes(grid, rival):
    return rival(grid) != _diagnostic_completion(grid)


SEMANTIC_WITNESSES = {
    "actual_completion": lambda grid: _refutes(grid, _identity),
    "non_yellow_frame": lambda grid: _refutes(grid, _yellow_only),
    "new_frame_color_role": lambda grid: _refutes(grid, _known_frame_colors),
    "frame_relative_axis": lambda grid: _refutes(grid, _canvas_axis),
    "right_side_content": lambda grid: _refutes(grid, _left_only),
    "exterior_is_unchanged": lambda grid: _refutes(grid, _whole_grid),
    "repeated_color_content": lambda grid: _refutes(grid, _first_color_only),
    "noise_does_not_gate_symmetry": lambda grid: _refutes(grid, _left_without_noise),
}
WITNESS_RIVALS = {
    "actual_completion": ["identity"], "non_yellow_frame": ["yellow_frame_only"],
    "new_frame_color_role": ["canonical_frame_colors_only"],
    "frame_relative_axis": ["canvas_axis"], "right_side_content": ["left_content_only"],
    "exterior_is_unchanged": ["mirror_exterior_too"],
    "repeated_color_content": ["first_cell_per_color"],
    "noise_does_not_gate_symmetry": ["left_only_without_exterior_noise"],
}


def lesson_identifiable(demos, query=None):
    """Finite declared-rival check; this is not a uniqueness proof over all rules."""
    if len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    return [f"demonstrations do not refute {name}" for name, rival in LESSON_COMPETITORS.items()
            if all(rival(pair["input"]) == pair["output"] for pair in demos)]
