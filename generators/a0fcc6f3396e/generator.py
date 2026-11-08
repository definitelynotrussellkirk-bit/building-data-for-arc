"""Canonical corner rectangles with observable controls and teaching coverage.

The Racket authority is unchanged: close each panel across rows then columns,
select the unique normalized shape, crop it, and recolor it to 8. Only inputs
are generated here. Nine consecutive default draws cover height, width and
area ties at all three odd-panel positions; eight demonstrations retain a
refutation of every declared rival after any single-pair query holdout.
"""
from __future__ import annotations

from functools import lru_cache

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "a0fcc6f3396e"
TASK_ID = GENERATOR_ID
RULE_HASH = "aadcb1545847"
VERSION = "2.1.0"
SUMMARY = "Three corner-rectangle panels; return the unique completed shape in color 8."
INVARIANTS = [
    "6x20 input; separator columns 6 and 13 are full color 9",
    "each 6x6 panel has exactly four color-2 rectangle corners on color 0",
    "two normalized rectangles match and one differs",
    "rectangle heights are 2..5 and widths 2..6; every exact joint control is constructive",
    "default nine-draw windows teach shape equality beyond height, width, area and position",
]
AXES = {
    "odd_panel": {"type": "int", "default": "seeded three-position schedule", "valid": "0..2"},
    "rect_h": {"type": "int", "default": "scheduled odd rectangle height", "valid": "2..5"},
    "rect_w": {"type": "int", "default": "scheduled odd rectangle width", "valid": "2..6"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
EXAMPLES_NEEDED = 8
LESSON_SCHEDULE_PERIOD = 9
MIN_STRICT_FRAC = 1.0
# On the declared four-corner 2..5 by 2..6 input family, the unchanged rule
# produces exactly one solid-8 grid for each (height, width): 4 * 5 = 20.
# This is a family-bound codomain, not the range of Racket on arbitrary grids.
# The retained Racket diversity probe and size-coverage regression exercise all 20.
EXPECTED_OUTPUT_CODOMAIN = 20
SCHEDULE_PROFILES = (
    "same_height_smaller", "same_width_larger", "equal_area_0",
    "same_height_larger", "same_width_smaller", "equal_area_1",
    "same_height_either", "same_width_either", "equal_area_2",
)
_PANEL_STARTS = (0, 7, 14)
_RECTANGLES = tuple((h, w) for h in range(2, 6) for w in range(2, 7))


def _validate_arguments(seed, sample_index, difficulty):
    if type(seed) is not int:
        raise ValueError("seed must be an integer, not bool, float or string")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer")
    if difficulty is not None and difficulty not in ("easy", "medium", "hard"):
        raise ValueError("difficulty must be None, easy, medium or hard")


def _schedule(seed, sample_index, difficulty):
    _validate_arguments(seed, sample_index, difficulty)
    # Only the episode seed and band select the phase/permutation. A keyed
    # sample_index=0 context makes this plan stable across consecutive draws.
    plan = gen_ctx(seed=seed, sample_index=0, version=VERSION, task_id=TASK_ID,
                   difficulty=difficulty).draw_rng(f"lesson_plan:{difficulty}")
    phase = (sample_index + plan.randrange(LESSON_SCHEDULE_PERIOD)) % LESSON_SCHEDULE_PERIOD
    panels = [0, 1, 2]
    plan.shuffle(panels)
    return phase, panels[phase // 3]


def schedule_profile(seed, sample_index, difficulty=None):
    return SCHEDULE_PROFILES[_schedule(seed, sample_index, difficulty)[0]]


def _matches_profile(base, odd, phase):
    bh, bw = base
    oh, ow = odd
    if phase % 3 == 2:
        return min(bh, bw, oh, ow) >= 3 and bh * bw == oh * ow and base != odd
    if phase % 3 == 0:
        return bh == oh and (ow < bw if phase == 0 else ow > bw if phase == 3 else ow != bw)
    return bw == ow and (oh > bh if phase == 1 else oh < bh if phase == 4 else oh != bh)


@lru_cache(maxsize=270)
def _pair_choices(phase, height, width):
    all_pairs = tuple((base, odd) for base in _RECTANGLES for odd in _RECTANGLES
                      if base != odd and (height is None or odd[0] == height)
                      and (width is None or odd[1] == width))
    scheduled = tuple(pair for pair in all_pairs if _matches_profile(*pair, phase))
    # An exact size request can conflict with a default teaching branch (e.g.
    # height 2 in an equal-area branch). Preserve the exact requested size and
    # lawful domain; only unoverridden lessons claim the schedule guarantee.
    return scheduled or all_pairs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_arguments(seed, sample_index, difficulty)
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    bounds = {"odd_panel": (0, 2), "rect_h": (2, 5), "rect_w": (2, 6)}
    for name, value in overrides.items():
        if value is not None and (type(value) is not int or not bounds[name][0] <= value <= bounds[name][1]):
            raise ValueError(f"{name} must be an integer in {bounds[name]}")
    phase, default_panel = _schedule(seed, sample_index, difficulty)
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    requested = {name: ctx.draw_int_strict(name, *bounds[name])
                 for name, value in overrides.items() if value is not None}
    rng = ctx.draw_rng(f"layout:{difficulty}")
    base, odd = rng.choice(_pair_choices(phase, requested.get("rect_h"), requested.get("rect_w")))
    # The conditional sampler has already chosen lawful values. Public keyed
    # singleton draws record those realized values on BOTH default and override
    # paths, while observe_overrides independently recovers them from pixels.
    odd = (ctx.draw_choice("rect_h", (odd[0],)), ctx.draw_choice("rect_w", (odd[1],)))
    odd_panel = ctx.draw_choice("odd_panel", (requested.get("odd_panel", default_panel),))
    grid = full_grid(6, 20, 0)
    for row in grid:
        row[6] = row[13] = 9
    for panel, start in enumerate(_PANEL_STARTS):
        height, width = odd if panel == odd_panel else base
        top, left = rng.randrange(7 - height), rng.randrange(7 - width)
        for r, c in ((top, left), (top, left + width - 1),
                     (top + height - 1, left), (top + height - 1, left + width - 1)):
            grid[r][start + c] = 2
    return grid


def _panel_cells(grid, panel):
    start = _PANEL_STARTS[panel]
    return [(r, c - start) for r in range(6) for c in range(start, start + 6) if grid[r][c] == 2]


def _dimensions(cells):
    return (max(r for r, _ in cells) - min(r for r, _ in cells) + 1,
            max(c for _, c in cells) - min(c for _, c in cells) + 1)


def _panel_shapes(grid):
    return [_dimensions(_panel_cells(grid, panel)) for panel in range(3)]


def _odd_index(shapes):
    indices = [i for i, shape in enumerate(shapes) if shapes.count(shape) == 1]
    if len(indices) != 1:
        raise ValueError("expected two matching rectangles and one odd rectangle")
    return indices[0]


def observe_overrides(grid):
    shapes = _panel_shapes(grid)
    panel = _odd_index(shapes)
    height, width = shapes[panel]
    return {"odd_panel": panel, "rect_h": height, "rect_w": width}


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, (list, tuple)) or len(grid) != 6:
        return ["expected six rows"]
    if any(not isinstance(row, (list, tuple)) or len(row) != 20 for row in grid):
        return ["expected a rectangular 6x20 grid"]
    if any(type(v) is not int or v not in (0, 2, 9) for row in grid for v in row):
        return ["cells must be integer colors 0, 2 or 9"]
    if any(grid[r][c] != 9 for r in range(6) for c in (6, 13)):
        return ["separator columns 6 and 13 must be full color 9"]
    if any(grid[r][c] == 9 for r in range(6) for c in range(20) if c not in (6, 13)):
        return ["color 9 is forbidden inside panels"]
    shapes = []
    for panel in range(3):
        cells = _panel_cells(grid, panel)
        if len(cells) != 4:
            return ["each panel must contain exactly four rectangle corners"]
        height, width = _dimensions(cells)
        if (height, width) not in _RECTANGLES:
            return ["rectangle dimensions must be 2..5 by 2..6"]
        top, left = min(r for r, _ in cells), min(c for _, c in cells)
        corners = {(top, left), (top, left + width - 1),
                   (top + height - 1, left), (top + height - 1, left + width - 1)}
        if set(cells) != corners:
            return ["markers must be the four bounding rectangle corners"]
        shapes.append((height, width))
    try:
        _odd_index(shapes)
    except ValueError as exc:
        return [str(exc)]
    return []


def strict_canonical_like(grid):
    return self_check(grid)


def _solid(shape):
    return [[8] * shape[1] for _ in range(shape[0])]


def _fixed_panel_rival(panel):
    def predict(grid):
        return _solid(_panel_shapes(grid)[panel])
    return predict


def _scalar_rival(axis, fallback):
    def predict(grid):
        shapes = _panel_shapes(grid)
        values = [h * w if axis == "area" else h if axis == "height" else w for h, w in shapes]
        unique = [i for i, value in enumerate(values) if values.count(value) == 1]
        return _solid(shapes[unique[0] if len(unique) == 1 else fallback])
    return predict


def _extreme_rival(largest):
    def predict(grid):
        shapes = _panel_shapes(grid)
        select = max if largest else min
        return _solid(select(shapes, key=lambda shape: shape[0] * shape[1]))
    return predict


def _incomplete_closure_rival(mode):
    def predict(grid):
        shapes = _panel_shapes(grid)
        h, w = shapes[_odd_index(shapes)]
        return [[8 if ((r in (0, h - 1)) if mode == "row" else
                       (c in (0, w - 1)) if mode == "column" else
                       (r in (0, h - 1) and c in (0, w - 1))) else 0
                 for c in range(w)] for r in range(h)]
    return predict


def _transpose_rival(grid):
    shapes = _panel_shapes(grid)
    h, w = shapes[_odd_index(shapes)]
    return _solid((w, h))


LESSON_COMPETITORS = {f"always_panel_{p}": _fixed_panel_rival(p) for p in range(3)}
LESSON_COMPETITORS.update({f"{axis}_else_panel_{p}": _scalar_rival(axis, p)
                          for axis in ("height", "width", "area") for p in range(3)})
LESSON_COMPETITORS.update({
    "largest_area": _extreme_rival(True), "smallest_area": _extreme_rival(False),
    "corners_only": _incomplete_closure_rival("corners"),
    "row_closure_only": _incomplete_closure_rival("row"),
    "column_closure_only": _incomplete_closure_rival("column"),
    "transpose_output": _transpose_rival,
})
SEMANTIC_RIVALS = dict(LESSON_COMPETITORS)
CANONICAL_SHORTCUTS = {name: LESSON_COMPETITORS[name] for name in (
    "always_panel_2", "height_else_panel_0", "height_else_panel_1", "height_else_panel_2",
    "area_else_panel_0", "area_else_panel_1", "area_else_panel_2", "width_else_panel_2",
)}


def _tie_witness(axis):
    def witness(grid):
        shapes = _panel_shapes(grid)
        values = [h * w if axis == "area" else h if axis == "height" else w for h, w in shapes]
        return len(set(values)) == 1 and len(set(shapes)) == 2
    return witness


def _position_witness(panel):
    def witness(grid):
        return _odd_index(_panel_shapes(grid)) == panel
    return witness


SEMANTIC_WITNESSES = {f"equal_{axis}_different_shape": _tie_witness(axis)
                      for axis in ("height", "width", "area")}
SEMANTIC_WITNESSES.update({f"odd_panel_{p}": _position_witness(p) for p in range(3)})
WITNESS_RIVALS = {f"equal_{axis}_different_shape": [f"{axis}_else_panel_{p}" for p in range(3)]
                  for axis in ("height", "width", "area")}
WITNESS_RIVALS.update({"odd_panel_0": ["always_panel_2"],
                      "odd_panel_1": ["always_panel_2"]})
BRANCH_WITNESSES = ["odd_panel_2"]


def lesson_identifiable(demos, query):
    """Finite declared-rival check; no claim of uniqueness among all rules."""
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query["output"]:
                reasons.append(f"{name} fits the demonstrations but changes the query")
    return reasons
