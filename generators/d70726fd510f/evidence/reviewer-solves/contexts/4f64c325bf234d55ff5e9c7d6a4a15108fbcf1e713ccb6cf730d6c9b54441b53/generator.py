"""Paired-panel occupancy XOR, with explicit truth-table coverage.

The unchanged Racket authority splits on the full color-4 column and returns
2 iff exactly one aligned input cell is nonzero. Foreground color identity is
irrelevant. Ordinary draws demonstrate all four occupancy states. Lawful
constant-output edge cases are opt-in, not mislabeled negative examples.

Textures and densities propose spatial masks; symmetric projection realizes
xor_target exactly and reserves both subcases of each sufficiently large
output class. Densities are NOT promises about the final foreground fraction.
"""
from __future__ import annotations

import math

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "d70726fd510f"
TASK_ID = "d70726fd510f"
VERSION = "2.0.0"
RULE_HASH = "11243a80c7ea"
EXAMPLES_NEEDED = 3
SUMMARY = "Split at the full 4-column; return 2 where aligned zero/nonzero occupancy differs."
INVARIANTS = [
    "rectangular integer-color grid, height 1..18, odd width 3..29",
    "color 4 occurs only in the full middle separator column",
    "each panel has at most one nonzero foreground color; colors may be equal or 2",
    "ordinary unoverridden draws contain 00, 01, 10 and 11 aligned occupancy states",
    "explicit xor_target is an exact count, including lawful constant-output edges",
]
PANEL_PATTERNS = ("random", "blob", "stripes", "checker", "border", "diagonal", "scatter")
HELPFUL_TEXTURES = PANEL_PATTERNS
DEGENERATE_TEXTURES = ("same_panels", "disjoint_panels", "all_zero")
LAWFUL_DEGENERATE_TEXTURES = DEGENERATE_TEXTURES
COLORS = (1, 2, 3, 5, 6, 7, 8, 9)
AXES = {
    "grid_h": {"type": "int", "default": "canonical anchor or difficulty range", "valid": "1..18"},
    "panel_w": {"type": "int", "default": "canonical anchor or difficulty range", "valid": "1..14"},
    "left_color": {"type": "color", "default": "8 on anchors; keyed color elsewhere", "valid": "1|2|3|5|6|7|8|9"},
    "right_color": {"type": "color", "default": "5 on anchors; keyed color elsewhere", "valid": "1|2|3|5|6|7|8|9"},
    "left_density": {"type": "float", "default": "rng 0.25..0.75", "valid": "0..1", "exact": False,
                     "doc": "Proposal probability/fraction, before exact-XOR and coverage projection."},
    "right_density": {"type": "float", "default": "rng 0.25..0.75", "valid": "0..1", "exact": False,
                      "doc": "Proposal probability/fraction, before exact-XOR and coverage projection."},
    "panel_pattern": {"type": "str", "default": "random on anchors; keyed texture elsewhere",
                      "valid": "random|blob|stripes|checker|border|diagonal|scatter"},
    "xor_target": {"type": "int", "default": "rng 2..area-2 for ordinary shapes", "valid": "0..252",
                   "doc": "Exact output-2 count; cannot exceed chosen panel area. Unpinned dimensions may expand."},
    "texture": {"type": "str", "default": "alias for panel_pattern; edge cases explicit only",
                "valid": "random|blob|stripes|checker|border|diagonal|scatter|same_panels|disjoint_panels|all_zero"},
}
# Cross-axis impossibilities carry the particular axis names in the exception.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
SCHEDULE_PROFILES = ("canonical_anchor", "extended_1", "extended_2")
MIN_STRICT_FRAC = 0.25


class IncompatibleOverrides(ValueError):
    def __init__(self, message, axes):
        super().__init__(message)
        self.incompatible_axes = tuple(sorted(axes))


def schedule_profile(seed, sample_index, difficulty=None):
    return SCHEDULE_PROFILES[sample_index % 3]


def _validate_overrides(overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")
    opts = {key: value for key, value in overrides.items() if value is not None}
    for name, lo, hi in (("grid_h", 1, 18), ("panel_w", 1, 14), ("xor_target", 0, 252)):
        if name in opts and (type(opts[name]) is not int or not lo <= opts[name] <= hi):
            raise ValueError(f"{name} must be an integer in {lo}..{hi}")
    for name in ("left_color", "right_color"):
        if name in opts and (type(opts[name]) is not int or opts[name] not in COLORS):
            raise ValueError(f"{name} must be one of {COLORS}")
    for name in ("left_density", "right_density"):
        if name in opts:
            value = opts[name]
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= 1:
                raise ValueError(f"{name} must be finite and in 0..1")
    for name, choices in (("panel_pattern", PANEL_PATTERNS), ("texture", PANEL_PATTERNS + DEGENERATE_TEXTURES)):
        if name in opts and opts[name] not in choices:
            raise ValueError(f"{name} must be one of {choices}")
    if "texture" in opts and "panel_pattern" in opts and opts["texture"] != opts["panel_pattern"]:
        raise IncompatibleOverrides("texture and panel_pattern cannot disagree", ("texture", "panel_pattern"))
    edge = opts.get("texture")
    if edge in DEGENERATE_TEXTURES:
        for name in ("left_density", "right_density"):
            if name in opts:
                raise IncompatibleOverrides("density proposals are not defined for boundary textures", ("texture", name))
        if edge == "all_zero":
            for name in ("left_color", "right_color"):
                if name in opts:
                    raise IncompatibleOverrides("all_zero has no observable foreground color", ("texture", name))
    return opts


def _dimensions(ctx, band, anchor, opts):
    h_lo, h_hi, w_lo, w_hi = {
        "easy": (4, 7, 3, 5), "medium": (4, 12, 3, 8), "hard": (8, 18, 5, 14)
    }[band]
    target = opts.get("xor_target", 0)
    min_h = max(1, math.ceil(target / opts.get("panel_w", 14)))
    h_options = [h for h in ([5] if anchor else range(h_lo, h_hi + 1)) if h >= min_h]
    if not h_options:
        h_options = list(range(min_h, 19))
    if not h_options or ("grid_h" in opts and opts["grid_h"] < min_h):
        raise IncompatibleOverrides("xor_target exceeds the available panel area", set(opts) & {"grid_h", "panel_w", "xor_target"})
    h = ctx.draw_int("grid_h", 1, 18) if "grid_h" in opts else ctx.draw_choice("grid_h", h_options)
    min_w = max(1, math.ceil(target / h))
    w_options = [w for w in ([4] if anchor else range(w_lo, w_hi + 1)) if w >= min_w]
    if not w_options:
        w_options = list(range(min_w, 15))
    if not w_options or ("panel_w" in opts and opts["panel_w"] < min_w):
        raise IncompatibleOverrides("xor_target exceeds the available panel area", set(opts) & {"grid_h", "panel_w", "xor_target"})
    pw = ctx.draw_int("panel_w", 1, 14) if "panel_w" in opts else ctx.draw_choice("panel_w", w_options)
    return h, pw


def _mask(h, pw, pattern, density, rng):
    """Independent texture proposal: no shared panel phase or origin."""
    n = h * pw
    if pattern == "random":
        return [int(rng.random() < density) for _ in range(n)]
    count = int(n * density + 0.5)
    origin_r, origin_c = rng.randrange(h), rng.randrange(pw)
    phase, vertical, slope = rng.randrange(2), rng.randrange(2), rng.choice((-1, 1))
    scores = []
    for index in range(n):
        r, c = divmod(index, pw)
        if pattern == "blob":
            priority = -((r - origin_r) ** 2 + (c - origin_c) ** 2)
        elif pattern == "stripes":
            priority = ((c if vertical else r) + phase) % 2
        elif pattern == "checker":
            priority = (r + c + phase) % 2
        elif pattern == "border":
            priority = -min(r, c, h - 1 - r, pw - 1 - c)
        elif pattern == "diagonal":
            priority = -abs((c - origin_c) - slope * (r - origin_r))
        else:  # scatter: fixed-size random subset, unlike Bernoulli random.
            priority = 0
        scores.append((priority, rng.random(), index))
    chosen = {item[2] for item in sorted(scores, reverse=True)[:count]}
    return [int(index in chosen) for index in range(n)]


def _project(states, target, rng):
    """Exact XOR cardinality, then symmetric within-class branch repair."""
    active = [i for i, value in enumerate(states) if value in (1, 2)]
    if len(active) > target:
        rng.shuffle(active)
        for index in active[:len(active) - target]:
            states[index] = rng.choice((0, 3))
    elif len(active) < target:
        equal = [i for i, value in enumerate(states) if value in (0, 3)]
        rng.shuffle(equal)
        for index in equal[:target - len(active)]:
            states[index] = rng.choice((1, 2))
    for a, b in ((0, 3), (1, 2)):
        indexes = [i for i, value in enumerate(states) if value in (a, b)]
        if len(indexes) >= 2:
            for desired in (a, b):
                if not any(states[i] == desired for i in indexes):
                    states[rng.choice(indexes)] = desired
        elif indexes and a == 0:
            # On tiny explicit shapes preserve observable foreground colors.
            states[indexes[0]] = 3


def _render(states, h, pw, left_color, right_color):
    grid = []
    for row in range(h):
        values = states[row * pw:(row + 1) * pw]
        grid.append([left_color if v & 2 else 0 for v in values] + [4] +
                    [right_color if v & 1 else 0 for v in values])
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    band = "medium" if difficulty is None else difficulty
    if band not in ("easy", "medium", "hard"):
        raise ValueError("difficulty must be None, easy, medium or hard")
    opts = _validate_overrides(overrides)
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=opts)
    anchor = schedule_profile(seed, sample_index, difficulty) == "canonical_anchor"
    h, pw = _dimensions(ctx, band, anchor, opts)
    n = h * pw
    left = ctx.draw_choice("left_color", COLORS if "left_color" in opts or not anchor else (8,))
    right = ctx.draw_choice("right_color", COLORS if "right_color" in opts or not anchor else (5,))
    pattern = opts.get("texture") or opts.get("panel_pattern")
    if pattern is None:
        pattern = ctx.draw_choice("panel_pattern", ("random",) if anchor else PANEL_PATTERNS)
    elif pattern in PANEL_PATTERNS:
        # Record alias resolution, but do not silently override a conflict.
        ctx.draw_choice("panel_pattern", (pattern,))
    ctx.draw_choice("texture", (pattern,))
    rng = ctx.draw_rng("joint_projection:" + band)
    if pattern in DEGENERATE_TEXTURES:
        target = n if pattern == "disjoint_panels" else 0
        if "xor_target" in opts and opts["xor_target"] != target:
            raise IncompatibleOverrides("boundary texture fixes xor_target", ("texture", "xor_target"))
        ctx.draw_choice("xor_target", (target,))
        states = [0] * n if pattern == "all_zero" else [rng.choice((0, 3) if target == 0 else (1, 2)) for _ in range(n)]
        if pattern != "all_zero":
            _project(states, target, rng)
    else:
        ld = opts.get("left_density", ctx.draw_rng("left_density:" + band).uniform(0.25, 0.75))
        rd = opts.get("right_density", ctx.draw_rng("right_density:" + band).uniform(0.25, 0.75))
        lm = _mask(h, pw, pattern, ld, ctx.draw_rng("left_panel:" + band))
        rm = _mask(h, pw, pattern, rd, ctx.draw_rng("right_panel:" + band))
        states = [2 * a + b for a, b in zip(lm, rm)]
        if "xor_target" in opts:
            target = ctx.draw_int("xor_target", 0, n)
        elif n >= 4:
            target = ctx.draw_int("xor_target", 2, n - 2)
        else:
            target = ctx.draw_choice("xor_target", (0,) if n == 1 else (1,))
        _project(states, target, rng)
    grid = _render(states, h, pw, left, right)
    for name, bit in (("left_color", 2), ("right_color", 1)):
        if name in opts and not any(value & bit for value in states):
            raise IncompatibleOverrides("requested foreground color cannot appear in this boundary case", set(opts) & {"texture", "xor_target", "grid_h", "panel_w", name})
    return grid


def self_check(grid, *, difficulty=None, meta=None):
    """Structural/semantic domain, NOT a test that every answer is nonconstant."""
    if not isinstance(grid, list) or not grid or not all(isinstance(row, list) and row for row in grid):
        return ["grid must be a nonempty list of nonempty row lists"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["grid must be rectangular"]
    if not 1 <= h <= 18 or not 3 <= w <= 29 or w % 2 != 1:
        return ["height must be 1..18 and width odd in 3..29"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer ARC colors 0..9, not booleans or floats"]
    pw = w // 2
    if any(row[pw] != 4 for row in grid) or any(value == 4 for row in grid for c, value in enumerate(row) if c != pw):
        return ["4 must occur only in the full middle separator column"]
    for start, stop in ((0, pw), (pw + 1, w)):
        if len({row[c] for row in grid for c in range(start, stop)} - {0}) > 1:
            return ["each panel must have at most one nonzero foreground color"]
    return []


def _states(grid):
    pw = len(grid[0]) // 2
    return [2 * int(row[c] != 0) + int(row[pw + 1 + c] != 0) for row in grid for c in range(pw)]


def rule_mirror(grid):
    """Diagnostic Python mirror; exported training labels still come from Racket."""
    errors = self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    pw = len(grid[0]) // 2
    return [[2 if (row[c] != 0) != (row[pw + 1 + c] != 0) else 0 for c in range(pw)] for row in grid]


def observe_overrides(grid):
    pw = len(grid[0]) // 2
    observed = {"grid_h": len(grid), "panel_w": pw,
                "xor_target": sum(value in (1, 2) for value in _states(grid))}
    for name, start, stop in (("left_color", 0, pw), ("right_color", pw + 1, 2 * pw + 1)):
        colors = {row[c] for row in grid for c in range(start, stop)} - {0}
        if len(colors) == 1:
            observed[name] = next(iter(colors))
    return observed


def strict_canonical_like(grid):
    errors = self_check(grid)
    if errors:
        return errors
    obs = observe_overrides(grid)
    if (obs["grid_h"], obs["panel_w"], obs.get("left_color"), obs.get("right_color")) != (5, 4, 8, 5):
        return ["canonical profile is height 5, panel width 4, left 8, right 5"]
    return [] if set(_states(grid)) == {0, 1, 2, 3} else ["canonical pairs demonstrate all four occupancy states"]


def _boolean_rival(table):
    def apply(grid):
        pw = len(grid[0]) // 2
        values = [2 * ((table >> state) & 1) for state in _states(grid)]
        return [values[r * pw:(r + 1) * pw] for r in range(len(grid))]
    return apply


def _color_inequality(grid):
    pw = len(grid[0]) // 2
    return [[2 * (row[c] != row[pw + 1 + c]) for c in range(pw)] for row in grid]


def _mirrored_right(grid):
    pw = len(grid[0]) // 2
    return [[2 * ((row[c] != 0) != (row[-1 - c] != 0)) for c in range(pw)] for row in grid]


# The complete 16-function Boolean family, excluding XOR's table 0b0110.
SEMANTIC_RIVALS = {f"boolean_{table:04b}": _boolean_rival(table) for table in range(16) if table != 6}
SEMANTIC_RIVALS.update({"color_inequality": _color_inequality, "mirrored_right": _mirrored_right})
LESSON_COMPETITORS = SEMANTIC_RIVALS
SEMANTIC_WITNESSES = {
    "both_zero": lambda grid: 0 in _states(grid),
    "right_only": lambda grid: 1 in _states(grid),
    "left_only": lambda grid: 2 in _states(grid),
    "both_nonzero": lambda grid: 3 in _states(grid),
}
WITNESS_RIVALS = {
    "both_zero": ["boolean_0111"], "right_only": ["boolean_0100"],
    "left_only": ["boolean_0010"], "both_nonzero": ["boolean_1110"],
}


def lesson_identifiable(demos, query):
    """Check the declared rival family, not uniqueness among arbitrary programs."""
    if not demos:
        return ["need at least one visible demonstration"]
    for index, pair in enumerate(demos):
        errors = self_check(pair["input"])
        if errors:
            return [f"demo {index}: {errors}"]
        if pair.get("output") != rule_mirror(pair["input"]):
            return [f"demo {index}: output disagrees with occupancy XOR"]
    if self_check(query["input"]):
        return ["query is outside the declared panel domain"]
    expected = rule_mirror(query["input"])
    reasons = []
    if query.get("output") is not None and query["output"] != expected:
        reasons.append("query output disagrees with occupancy XOR")
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos) and rival(query["input"]) != expected:
            reasons.append(f"surviving rival changes query answer: {name}")
    return reasons


def mutation_fixtures():
    grid = generate(19, 0)
    wrong_separator = [row[:] for row in grid]
    wrong_separator[0][4] = 0
    extra_separator = [row[:] for row in grid]
    extra_separator[0][0] = 4
    bad_color = [row[:] for row in grid]
    bad_color[0][0] = 10
    return [("broken_separator", wrong_separator), ("stray_separator_color", extra_separator),
            ("out_of_range_color", bad_color), ("ragged", [grid[0][:-1]] + grid[1:])]
