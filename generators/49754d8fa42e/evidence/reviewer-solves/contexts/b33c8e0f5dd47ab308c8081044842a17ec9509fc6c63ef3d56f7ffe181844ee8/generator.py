"""Input curriculum for d4469b4b: nonzero mode selects a fixed glyph.

Only inputs are generated here. Canonical Racket remains the label authority.
The five exact controls are recoverable from pixels. The curriculum retains
5x5 binary anchors and adds mixed-color counterexamples to presence/scan cues.
See notes.md for the intentionally narrower-than-Racket counting domain.
"""
from __future__ import annotations

from collections import Counter

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "49754d8fa42e"
TASK_ID = "49754d8fa42e"
RULE_HASH = "a84bb758c578"
VERSION = "3.2.0"
EXPECTED_OUTPUT_CODOMAIN = 3
EXAMPLES_NEEDED = 5
MIN_STRICT_FRAC = 1.0
SUMMARY = (
    "Count nonzero colors; the unique mode 1/2/3 selects the unchanged gray "
    "plus/T/right-L glyph. Each three-input block has independently shuffled "
    "classes and profiles: a 5x5 anchor, early decoy, and late decoy. "
    "Five consecutive default demonstrations contain all three classes and "
    "refute declared scan/extremum/frequency and endpoint selection shortcuts."
)
INVARIANTS = [
    "rectangular integer colors 0..9; both dimensions 3..10",
    "at least five zeros and five cells of the unique nonzero mode 1, 2, or 3",
    "every other nonzero color is strictly less frequent than the mode",
    "palette_size counts all visible colors, including zero, and is 2..6",
    "infeasible exact controls are rejected; counts are never clipped or recolored",
]
AXES = {
    "grid_h": {"type": "int", "default": "5 in anchors; weighted 3..10 otherwise", "valid": "3..10"},
    "grid_w": {"type": "int", "default": "5 in anchors; weighted 3..10 otherwise", "valid": "3..10"},
    "mode_color": {"type": "int", "default": "block-shuffled 1..3", "valid": "1..3"},
    "mode_count": {"type": "int", "default": "feasible 5..95; anchors favor 8..14", "valid": "5..95"},
    "palette_size": {"type": "int", "default": "2 in anchors; feasible 4..6 otherwise", "valid": "2..6"},
}
# Exceptions identify actual caller pins that cannot coexist. This empty
# declaration opts into strict checking; no blanket combination is excused.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
SCHEDULE_PROFILES = ("canonical_anchor", "early_decoy", "late_decoy")
_LAYOUTS = ("scattered", "blob", "diagonal", "row_dominant",
            "col_dominant", "checker", "frame")
_LIMITS = {"grid_h": (3, 10), "grid_w": (3, 10), "mode_color": (1, 3),
           "mode_count": (5, 95), "palette_size": (2, 6)}


def schedule_profile(seed, sample_index, difficulty=None):
    return _block_plan(seed, sample_index)[1][sample_index % 3]


def _block_plan(seed, sample_index):
    # A block shares its permutations; separate blocks vary independently.
    # Profile positions are independent of class labels and of one another.
    block = gen_ctx(seed=seed, sample_index=sample_index // 3,
                    version=VERSION, task_id=TASK_ID)
    colors = [1, 2, 3]
    block.draw_rng("class_permutation").shuffle(colors)
    profiles = list(SCHEDULE_PROFILES)
    block.draw_rng("profile_permutation").shuffle(profiles)
    mode_endpoint_profile = block.draw_choice("mode_endpoint_profile", ("early_decoy", "late_decoy"))
    return colors, profiles, mode_endpoint_profile


def _validate_overrides(overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    pins = {key: value for key, value in overrides.items() if value is not None}
    for key, value in pins.items():
        lo, hi = _LIMITS[key]
        if type(value) is not int or not lo <= value <= hi:
            raise ValueError(f"{key} must be an integer in [{lo}, {hi}]")
    return pins


def _reject_capacity(pins):
    axes = tuple(sorted(set(pins) & {"grid_h", "grid_w", "mode_count", "palette_size"}))
    exc = ValueError(
        "incompatible overrides: need h*w >= mode_count + palette_size - 2 + 5 "
        "(one cell per distractor and at least five zero cells); "
        f"pins={{{', '.join(f'{key!r}: {pins[key]!r}' for key in axes)}}}"
    )
    exc.incompatible_axes = axes
    raise exc


def _shape_choices(pins):
    minimum = pins.get("mode_count", 5) + pins.get("palette_size", 2) - 2 + 5
    return [(h, w) for h in range(3, 11) for w in range(3, 11)
            if h == pins.get("grid_h", h) and w == pins.get("grid_w", w)
            and h*w >= minimum]


def _draw_geometry(ctx, pins, anchor, difficulty):
    shapes = _shape_choices(pins)
    if not shapes:
        _reject_capacity(pins)
    preferred = (pins.get("grid_h", 5), pins.get("grid_w", 5))
    if anchor and preferred in shapes:
        chosen = preferred
    else:
        favored = {"easy": (3, 6), "medium": (4, 8), "hard": (6, 10)}.get(difficulty, (4, 8))
        weighted = shapes[:]
        weighted.extend([shape for shape in shapes
                         if all(favored[0] <= side <= favored[1] for side in shape)] * 5)
        chosen = ctx.draw_rng("canvas_geometry").choice(weighted)
    # Public draws record the realized conditioned choices without clipping.
    h = ctx.draw_choice("grid_h", [chosen[0]])
    w = ctx.draw_choice("grid_w", [chosen[1]])
    return h, w


def _draw_palette_and_count(ctx, pins, area, anchor, difficulty):
    palettes = [p for p in range(2, 7) if area >= pins.get("mode_count", 5) + p - 2 + 5]
    if "palette_size" in pins:
        palettes = [p for p in palettes if p == pins["palette_size"]]
    if not palettes:
        _reject_capacity(pins)
    if anchor and "palette_size" not in pins and 2 in palettes:
        palettes = [2]
    elif not anchor and "palette_size" not in pins:
        mixed = [p for p in palettes if p >= 4]
        if mixed:
            palettes = mixed + [4]*8 if 4 in mixed else mixed
    palette = ctx.draw_choice("palette_size", palettes)
    counts = list(range(5, area - (palette - 2) - 5 + 1))
    if anchor:
        favored = [n for n in counts if 8 <= n <= 14]
    else:
        fractions = {"easy": (0.35, 0.65), "medium": (0.25, 0.5),
                     "hard": (0.15, 0.35)}.get(difficulty, (0.25, 0.5))
        favored = [n for n in counts if fractions[0]*area <= n <= fractions[1]*area]
    count = ctx.draw_choice("mode_count", counts + favored*8)
    return palette, count


def _distractors(ctx, color, palette, count, capacity, difficulty):
    how_many = palette - 2
    if not how_many:
        return [], []
    rng = ctx.draw_rng("distractor_palette")
    core = [value for value in (1, 2, 3) if value != color]
    extras = list(range(4, 10))
    rng.shuffle(core)
    rng.shuffle(extras)
    colors = (core + extras)[:how_many]
    counts = []
    rng = ctx.draw_rng("distractor_counts")
    remaining = capacity
    for index in range(how_many):
        maximum = min(count - 1, remaining - (how_many-index-1))
        choices = list(range(1, maximum + 1))
        if difficulty == "hard":
            choices += list(range(max(1, maximum-2), maximum+1))*4
        elif difficulty == "easy":
            choices += list(range(1, min(maximum, max(1, count//3))+1))*4
        amount = rng.choice(choices)
        counts.append(amount)
        remaining -= amount
    return colors, counts


def _layout_cells(layout, h, w, rng):
    cells = [(r, c) for r in range(h) for c in range(w)]
    rng.shuffle(cells)
    if layout == "blob":
        cr, cc = rng.randrange(h), rng.randrange(w)
        cells.sort(key=lambda rc: abs(rc[0]-cr) + abs(rc[1]-cc))
    elif layout == "diagonal":
        cells.sort(key=lambda rc: rc[0] != rc[1])
    elif layout == "row_dominant":
        row = rng.randrange(h)
        cells.sort(key=lambda rc: rc[0] != row)
    elif layout == "col_dominant":
        column = rng.randrange(w)
        cells.sort(key=lambda rc: rc[1] != column)
    elif layout == "checker":
        parity = rng.randrange(2)
        cells.sort(key=lambda rc: (rc[0]+rc[1]) % 2 != parity)
    elif layout == "frame":
        cells.sort(key=lambda rc: rc[0] not in (0, h-1) and rc[1] not in (0, w-1))
    return cells


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if type(seed) is not int or type(sample_index) is not int:
        raise ValueError("seed and sample_index must be integers")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard, or None")
    pins = _validate_overrides(overrides)
    colors_in_block, profiles_in_block, mode_endpoint_profile = _block_plan(seed, sample_index)
    scheduled = colors_in_block[sample_index % 3]
    profile = profiles_in_block[sample_index % 3]
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=pins)
    anchor = profile == "canonical_anchor"
    color = ctx.draw_choice("mode_color", [1, 2, 3] if "mode_color" in pins else [scheduled])
    h, w = _draw_geometry(ctx, pins, anchor, difficulty)
    palette, count = _draw_palette_and_count(ctx, pins, h*w, anchor, difficulty)
    colors, counts = _distractors(ctx, color, palette, count, h*w-count-5, difficulty)
    grid = full_grid(h, w, 0)
    layout = "scattered" if anchor else ctx.draw_choice("layout_style", _LAYOUTS + ("scattered",)*4)
    cells = _layout_cells(layout, h, w, ctx.draw_rng("cell_layout"))[:count+sum(counts)]
    values = [color]*count
    for other, amount in zip(colors, counts):
        values.extend([other]*amount)
    # One contrast includes mode at an endpoint; the other keeps mode wholly
    # inside. The former refutes endpoint-complement, the latter refutes
    # counting only endpoint colors. Neither shortcut explains the full block.
    if colors and not anchor:
        first, last = min(cells), max(cells)
        if profile == mode_endpoint_profile or len(colors) == 1:
            first_color, last_color = (colors[0], color) if profile == "early_decoy" else (color, colors[0])
        else:
            first_color, last_color = colors[0], colors[1]
        grid[first[0]][first[1]] = first_color
        grid[last[0]][last[1]] = last_color
        cells = [cell for cell in cells if cell not in (first, last)]
        values.remove(first_color)
        values.remove(last_color)
    ctx.draw_rng("color_placement").shuffle(values)
    for (r, c), value in zip(cells, values):
        grid[r][c] = value
    return grid


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected nonempty rows"]
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        return ["ragged or malformed rows"]
    if not (3 <= h <= 10 and 3 <= w <= 10):
        return ["curriculum dimensions must be 3..10"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer colors 0..9 (not booleans or floats)"]
    counts = Counter(value for row in grid for value in row)
    errors = []
    if counts.get(0, 0) < 5:
        errors.append("counting curriculum requires at least five zero cells")
    if not 2 <= len(counts) <= 6:
        errors.append("visible palette, including zero, must contain 2..6 colors")
    foreground = sorted(((n, c) for c, n in counts.items() if c), reverse=True)
    if not foreground:
        return errors + ["missing nonzero mode"]
    n, color = foreground[0]
    if color not in (1, 2, 3):
        errors.append("unique nonzero mode must be 1, 2, or 3")
    if n < 5:
        errors.append("counting curriculum requires at least five modal cells")
    if len(foreground) > 1 and foreground[1][0] == n:
        errors.append("nonzero mode must be unique; ties are outside the curriculum")
    return errors


def observe_overrides(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    counts = Counter(value for row in grid for value in row)
    color = max((c for c in counts if c), key=counts.__getitem__)
    return {"grid_h": len(grid), "grid_w": len(grid[0]), "mode_color": color,
            "mode_count": counts[color], "palette_size": len(counts)}


def strict_canonical_like(grid):
    """Declared task-domain validity; canonical profiles have a separate gate."""
    return self_check(grid)


def _rival_emblem(color):
    """Rival-only output dictionary. Never called by generate()."""
    patterns = {
        1: ((0, 5, 0), (5, 5, 5), (0, 5, 0)),
        2: ((5, 5, 5), (0, 5, 0), (0, 5, 0)),
        3: ((0, 0, 5), (0, 0, 5), (5, 5, 5)),
    }
    return [list(row) for row in patterns.get(color, ((0, 0, 0),)*3)]


def _first_nonzero(grid):
    return _rival_emblem(next((v for row in grid for v in row if v), 0))


def _last_nonzero(grid):
    return _rival_emblem(next((v for row in reversed(grid) for v in reversed(row) if v), 0))


def _smallest_nonzero(grid):
    return _rival_emblem(min((v for row in grid for v in row if v), default=0))


def _largest_nonzero(grid):
    return _rival_emblem(max((v for row in grid for v in row if v), default=0))


def _least_frequent_nonzero(grid):
    counts = Counter(v for row in grid for v in row if v)
    color = min(counts, key=lambda c: (counts[c], c)) if counts else 0
    return _rival_emblem(color)


def _endpoint_color(grid):
    values = [v for row in grid for v in row if v]
    if not values:
        return 0
    first, last = values[0], values[-1]
    if first == last:
        return first
    remaining = sorted({1, 2, 3} - {first, last})
    return remaining[0] if remaining else 0


def _endpoint_complement(grid):
    return _rival_emblem(_endpoint_color(grid))


def _endpoint_limited_color(grid):
    values = [v for row in grid for v in row if v]
    if not values:
        return 0
    counts = Counter(values)
    candidates = sorted({values[0], values[-1]})
    return max(candidates, key=counts.__getitem__)


def _endpoint_limited_mode(grid):
    return _rival_emblem(_endpoint_limited_color(grid))


def _first_is_decoy(grid):
    return next(v for row in grid for v in row if v) != observe_overrides(grid)["mode_color"]


def _last_is_decoy(grid):
    return next(v for row in reversed(grid) for v in reversed(row) if v) != observe_overrides(grid)["mode_color"]


def _smaller_decoy(grid):
    return min(v for row in grid for v in row if v) != observe_overrides(grid)["mode_color"]


def _larger_decoy(grid):
    return max(v for row in grid for v in row if v) != observe_overrides(grid)["mode_color"]


def _multiple_foreground_colors(grid):
    return observe_overrides(grid)["palette_size"] > 2


def _endpoint_complement_wrong(grid):
    return _endpoint_color(grid) != observe_overrides(grid)["mode_color"]


def _mode_absent_from_endpoints(grid):
    return _endpoint_limited_color(grid) != observe_overrides(grid)["mode_color"]


SEMANTIC_RIVALS = {
    "first_nonzero": _first_nonzero,
    "last_nonzero": _last_nonzero,
    "smallest_nonzero": _smallest_nonzero,
    "largest_nonzero": _largest_nonzero,
    "least_frequent_nonzero": _least_frequent_nonzero,
    "endpoint_complement": _endpoint_complement,
    "endpoint_limited_mode": _endpoint_limited_mode,
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES = {
    "early_decoy": _first_is_decoy,
    "late_decoy": _last_is_decoy,
    "smaller_decoy": _smaller_decoy,
    "larger_decoy": _larger_decoy,
    "multiple_foreground_colors": _multiple_foreground_colors,
    "endpoint_complement_wrong": _endpoint_complement_wrong,
    "mode_absent_from_endpoints": _mode_absent_from_endpoints,
}
WITNESS_RIVALS = {
    "early_decoy": ["first_nonzero"],
    "late_decoy": ["last_nonzero"],
    "smaller_decoy": ["smallest_nonzero"],
    "larger_decoy": ["largest_nonzero"],
    "multiple_foreground_colors": ["least_frequent_nonzero"],
    "endpoint_complement_wrong": ["endpoint_complement"],
    "mode_absent_from_endpoints": ["endpoint_limited_mode"],
}


def lesson_identifiable(demos, query):
    """Finite rival/class support; not universal induction or hidden-label use.

    Only demonstration outputs are read. The five-draw all-class guarantee
    applies to contiguous unpinned draws; overrides can remove that support.
    """
    query_grid = query["input"] if isinstance(query, dict) else query
    errors = self_check(query_grid)
    if errors:
        return ["query outside curriculum: " + "; ".join(errors)]
    demonstrated = set()
    for demo in demos:
        errors = self_check(demo["input"])
        if errors:
            return ["demonstration outside curriculum: " + "; ".join(errors)]
        demonstrated.add(observe_overrides(demo["input"])["mode_color"])
    color = observe_overrides(query_grid)["mode_color"]
    reasons = [] if color in demonstrated else [f"query mode {color} has no demonstrated glyph"]
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(demo["input"]) == demo["output"] for demo in demos):
            reasons.append(f"rival {name} survives every demonstration")
    return reasons
