"""Constructive inputs for stacked zero-occupancy XOR (ARC 31d5ba1a).

Racket remains the label authority. Ordinary inputs contain all four occupancy
states; density and texture steer proposals before minimal coverage repairs.
"""
from __future__ import annotations

from collections import Counter
import math

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "af0ae766e671"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "c5ef698a2a19"
SUMMARY = (
    "Stack two equally sized panels with distinct nonzero foreground colors. "
    "Output 6 exactly where one aligned cell is zero and the other is nonzero, "
    "otherwise 0. Every ordinary input covers all four occupancy states. "
    "Three-demo lessons alternate canonical/broad sizes and canonical/varied "
    "palettes; textures and densities are proposals, xor_target is a lower bound."
)
INVARIANTS = [
    "input height 2..30 is even; width 1..30; each half has at least four cells",
    "each half uses zero and one nonzero foreground color; foregrounds differ",
    "all four aligned occupancy states 00, 01, 10, 11 occur",
    "output height is half the input height; XOR-true cells become fixed color 6",
]
PANEL_PATTERNS = ("random", "blob", "stripes", "checker", "border", "diagonal")
HELPFUL_TEXTURES = PANEL_PATTERNS
DEGENERATE_TEXTURES = ("same_halves", "disjoint_halves", "all_filled")
AXES = {
    "half_h": {"type": "int", "default": "3 in core; weighted 1..15 in broad", "valid": "1..15"},
    "grid_w": {"type": "int", "default": "5 in core; weighted 1..30 in broad", "valid": "1..30"},
    "top_color": {"type": "color", "default": "9 or varied 1..8", "valid": "1..9"},
    "bot_color": {"type": "color", "default": "4 or varied; differs from top", "valid": "1..9"},
    "top_density": {"type": "float", "default": "uniform 0.3..0.7 proposal", "valid": "0..1", "exact": False},
    "bot_density": {"type": "float", "default": "uniform 0.3..0.7 proposal", "valid": "0..1", "exact": False},
    "panel_pattern": {"type": "str", "default": "uniform proposal family", "valid": "|".join(PANEL_PATTERNS), "exact": False},
    "texture": {"type": "str", "default": "optional panel_pattern alias", "valid": "|".join(PANEL_PATTERNS), "exact": False},
    "xor_target": {"type": "int", "default": "lower bound 1..half_h", "valid": "1..half_h*grid_w-2", "exact": False},
}
# Only specific impossible requests raise; exceptions carry the actual axes.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 4
SCHEDULE_PROFILES = ("core_canonical", "core_varied", "broad_canonical", "broad_varied")


def schedule_profile(seed, sample_index, difficulty=None):
    """Semantic schedule only; random positions and masks never repeat modulo 4."""
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


def _reject(message, axes):
    error = ValueError(message)
    error.incompatible_axes = tuple(axes)
    raise error


def _validate_request(seed, sample_index, difficulty, overrides):
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative integer, not bool")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer, not bool")
    if difficulty is not None and (type(difficulty) is not str or difficulty not in ("easy", "medium", "hard")):
        raise ValueError("difficulty must be None, easy, medium or hard")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    limits = {"half_h": (1, 15), "grid_w": (1, 30), "top_color": (1, 9),
              "bot_color": (1, 9), "xor_target": (1, 448)}
    for name, (lo, hi) in limits.items():
        value = overrides.get(name)
        if value is not None and (type(value) is not int or not lo <= value <= hi):
            raise ValueError(f"{name} must be an integer in {lo}..{hi}, not bool")
    for name in ("top_density", "bot_density"):
        value = overrides.get(name)
        if value is not None and (type(value) not in (int, float) or not 0 <= value <= 1 or not math.isfinite(value)):
            raise ValueError(f"{name} must be a finite numeric proposal in 0..1")
    for name, options in (("panel_pattern", PANEL_PATTERNS),
                          ("texture", PANEL_PATTERNS + DEGENERATE_TEXTURES)):
        value = overrides.get(name)
        if value is not None and (type(value) is not str or value not in options):
            raise ValueError(f"unknown {name}: {value!r}")
    pattern, texture = overrides.get("panel_pattern"), overrides.get("texture")
    if pattern is not None and texture is not None and pattern != texture:
        _reject("texture and panel_pattern disagree", ("texture", "panel_pattern"))
    if overrides.get("top_color") is not None and overrides.get("top_color") == overrides.get("bot_color"):
        _reject("top_color and bot_color must differ", ("top_color", "bot_color"))


def _choice(ctx, label, allowed, preferred=()):
    allowed = list(allowed)
    favored = [v for v in preferred if v in allowed]
    options = allowed if ctx.overrides.get(label) is not None else (favored or allowed)
    return ctx.draw_choice(label, options)


def _shape(ctx, core):
    pinned_h, pinned_w = ctx.overrides.get("half_h"), ctx.overrides.get("grid_w")
    minimum = max(4, (ctx.overrides.get("xor_target") or 1) + 2)
    pairs = [(h, w) for h in range(1, 16) for w in range(1, 31)
             if h*w >= minimum and (pinned_h is None or h == pinned_h)
             and (pinned_w is None or w == pinned_w)]
    if not core and not (pinned_h is not None and pinned_w is not None):
        pairs = [(h, w) for h, w in pairs if (h, w) != (3, 5)]
    if not pairs:
        _reject("half_h, grid_w and xor_target cannot fit four occupancy states "
                "and the requested XOR lower bound",
                [k for k in ("half_h", "grid_w", "xor_target") if ctx.overrides.get(k) is not None])
    heights = sorted({h for h, _ in pairs})
    widths = list(range(1, 31))
    if ctx.difficulty == "easy":
        h_favored, w_favored = list(range(1, 6)), list(range(1, 9))
    elif ctx.difficulty == "hard":
        h_favored, w_favored = list(range(8, 16)), list(range(12, 31))
    else:
        h_favored, w_favored = list(range(3, 9)), list(range(4, 16))
    h_preferred = [3] if core else heights + h_favored * 3
    half_h = _choice(ctx, "half_h", heights, h_preferred)
    widths = [w for h, w in pairs if h == half_h]
    w_preferred = [5] if core else widths + w_favored * 3
    width = _choice(ctx, "grid_w", widths, w_preferred)
    return half_h, width


def _palette(ctx, canonical):
    pinned_bot = ctx.overrides.get("bot_color")
    top_allowed = [c for c in range(1, 10) if c != pinned_bot]
    top_preferred = [9] if canonical else [c for c in top_allowed if c != 9]
    top = _choice(ctx, "top_color", top_allowed, top_preferred)
    bot_allowed = [c for c in range(1, 10) if c != top]
    bottom = _choice(ctx, "bot_color", bot_allowed, [4] if canonical else bot_allowed)
    return top, bottom


def _proposal(half_h, width, pattern, density, rng):
    """Rank cells by independently drawn geometry, then take the density quota."""
    cells = [(r, c) for r in range(half_h) for c in range(width)]
    count = round(len(cells) * density)
    center_r, center_c = rng.randrange(half_h), rng.randrange(width)
    horizontal = rng.choice((False, True))
    phase, period = rng.randrange(5), rng.randint(2, 5)
    reflection = rng.choice((-1, 1))
    stretch = rng.uniform(0.5, 2.0)

    def score(point):
        r, c = point
        jitter = rng.random() * 0.1
        if pattern == "blob":
            return (r-center_r)**2 * stretch + (c-center_c)**2 / stretch + jitter
        if pattern == "stripes":
            return ((r if horizontal else c) + phase) % period + jitter
        if pattern == "checker":
            return (r+c+phase) % 2 + jitter
        if pattern == "border":
            return min(r, half_h-1-r, c, width-1-c) + jitter
        if pattern == "diagonal":
            return (r*width/max(half_h, 1) - reflection*c + phase) % width + jitter
        return rng.random()

    cells.sort(key=score)
    return set(cells[:count])


def _complete_states(states, target, rng):
    """Edit random surplus cells, retaining at least one of each truth-table row."""
    counts = Counter(states)
    missing = [state for state in range(4) if not counts[state]]
    rng.shuffle(missing)
    for wanted in missing:
        candidates = [i for i, state in enumerate(states) if counts[state] > 1]
        chosen = rng.choice(candidates)
        counts[states[chosen]] -= 1
        states[chosen] = wanted
        counts[wanted] += 1
    have = counts[1] + counts[2]
    while have < target:
        candidates = [i for i, state in enumerate(states)
                      if state in (0, 3) and counts[state] > 1]
        chosen = rng.choice(candidates)
        wanted = rng.choice((1, 2))
        counts[states[chosen]] -= 1
        states[chosen] = wanted
        counts[wanted] += 1
        have += 1
    return states


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_request(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    phase = sample_index % LESSON_SCHEDULE_PERIOD
    half_h, width = _shape(ctx, core=phase < 2)
    top_color, bot_color = _palette(ctx, canonical=phase % 2 == 0)
    count = half_h * width
    target_hi = count - 2 if overrides.get("xor_target") is not None else min(half_h, count-2)
    target = ctx.draw_int_strict("xor_target", 1, target_hi)
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        rng = ctx.draw_rng("negative_fixture")
        options = {"same_halves": (0, 3), "disjoint_halves": (1, 2), "all_filled": (3,)}
        states = [rng.choice(options[texture]) for _ in range(count)]
    else:
        pattern = texture or ctx.draw_choice("panel_pattern", PANEL_PATTERNS)
        densities = [overrides.get(name) if overrides.get(name) is not None
                     else ctx.draw_rng(name).uniform(0.3, 0.7)
                     for name in ("top_density", "bot_density")]
        top = _proposal(half_h, width, pattern, densities[0], ctx.draw_rng("top_proposal"))
        bottom = _proposal(half_h, width, pattern, densities[1], ctx.draw_rng("bot_proposal"))
        states = [2*int((r, c) in top) + int((r, c) in bottom)
                  for r in range(half_h) for c in range(width)]
        states = _complete_states(states, max(2, target), ctx.draw_rng("occupancy_repair"))
    grid = full_grid(2*half_h, width, 0)
    for i, state in enumerate(states):
        r, c = divmod(i, width)
        grid[r][c] = top_color if state & 2 else 0
        grid[half_h+r][c] = bot_color if state & 1 else 0
    return grid


def _states(grid):
    half_h = len(grid) // 2
    return [2*int(top != 0) + int(bottom != 0)
            for upper, lower in zip(grid[:half_h], grid[half_h:])
            for top, bottom in zip(upper, lower)]


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, (list, tuple)) or not grid or not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    height, width = len(grid), len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["ragged grid"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer ARC colors 0..9, not bool"]
    if height % 2 or not 2 <= height <= 30 or not 1 <= width <= 30:
        return ["height must be even in 2..30; width must be in 1..30"]
    half_h = height // 2
    if half_h*width < 4:
        return ["each panel needs at least four cells to teach all occupancy states"]
    top = {v for row in grid[:half_h] for v in row if v != 0}
    bottom = {v for row in grid[half_h:] for v in row if v != 0}
    errors = []
    if len(top) != 1 or len(bottom) != 1 or top == bottom:
        errors.append("each half needs one distinct nonzero foreground color")
    missing = set(range(4)) - set(_states(grid))
    if missing:
        errors.append("missing occupancy states: " + ", ".join(f"{s:02b}" for s in sorted(missing)))
    return errors


def strict_canonical_like(grid):
    """Canonical task manifold, including novel sizes and nonzero role colors."""
    return self_check(grid)


def observe_overrides(grid):
    half_h = len(grid) // 2
    top = {v for row in grid[:half_h] for v in row if v != 0}
    bottom = {v for row in grid[half_h:] for v in row if v != 0}
    if len(top) != 1 or len(bottom) != 1:
        raise ValueError("foreground colors are not uniquely observable")
    return {"half_h": half_h, "grid_w": len(grid[0]),
            "top_color": next(iter(top)), "bot_color": next(iter(bottom))}


def _boolean_rival(table):
    def rival(grid):
        width = len(grid[0])
        values = [6 if (table >> state) & 1 else 0 for state in _states(grid)]
        return [values[i:i+width] for i in range(0, len(values), width)]
    return rival


def _fixed_9_4(grid):
    half_h = len(grid) // 2
    return [[6 if (top == 9) != (bottom == 4) else 0
             for top, bottom in zip(upper, lower)]
            for upper, lower in zip(grid[:half_h], grid[half_h:])]


def _fixed_3x5(grid):
    half_h, width = len(grid) // 2, len(grid[0])
    return [[6 if r < half_h and c < width and
             ((grid[r][c] == 0) != (grid[half_h+r][c] == 0)) else 0
             for c in range(5)] for r in range(3)]


def _state_witness(state):
    def witness(grid):
        return state in _states(grid)
    return witness


def _varied_palette(grid):
    obs = observe_overrides(grid)
    return (obs["top_color"], obs["bot_color"]) != (9, 4)


def _varied_shape(grid):
    return (len(grid), len(grid[0])) != (6, 5)


SEMANTIC_RIVALS = {f"boolean_{table:04b}": _boolean_rival(table)
                   for table in range(16) if table != 6}
SEMANTIC_RIVALS.update({"fixed_9_4": _fixed_9_4, "fixed_3x5": _fixed_3x5})
SEMANTIC_WITNESSES = {f"state_{state:02b}": _state_witness(state) for state in range(4)}
SEMANTIC_WITNESSES.update({"varied_palette": _varied_palette, "varied_shape": _varied_shape})
WITNESS_RIVALS = {f"state_{state:02b}": [f"boolean_{6 ^ (1 << state):04b}"] for state in range(4)}
WITNESS_RIVALS.update({"varied_palette": ["fixed_9_4"], "varied_shape": ["fixed_3x5"]})
CANONICAL_SHORTCUTS = {"fixed_9_4": _fixed_9_4, "fixed_3x5": _fixed_3x5}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
