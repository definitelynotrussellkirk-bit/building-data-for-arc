"""Input sampler for 34b99a2b: occupancy XOR across a color-4 divider.

Racket remains the label authority. Ordinary inputs expose all four occupancy
states. Three consecutive indices cover canonical, guaranteed transfer, and
broad profiles. Overrides can request lawful, less informative edge inputs.
Textures and densities are proposals modified by exact XOR projection.
"""
from __future__ import annotations

import math
from functools import partial

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "d70726fd510f"
TASK_ID = GENERATOR_ID
RULE_HASH = "11243a80c7ea"
VERSION = "2.1.0"
SUMMARY = "Equal panels split by color 4; paint 2 iff exactly one aligned cell is nonzero."
INVARIANTS = [
    "rectangular integer ARC grid with one full color-4 middle divider",
    "equal-width panels, each empty or monochrome apart from zero",
    "ordinary unforced inputs expose occupancy states 00, 01, 10, and 11",
    "xor_target is an exact count; accepted color controls are visible",
    "constant outputs are lawful explicit edges, not default lessons",
]
COLORS = (1, 2, 3, 5, 6, 7, 8, 9)
PANEL_PATTERNS = ("random", "blob", "stripes", "checker", "border", "diagonal", "scatter")
HELPFUL_TEXTURES = PANEL_PATTERNS
DEGENERATE_TEXTURES = ("same_panels", "disjoint_panels", "all_zero")
LAWFUL_DEGENERATE_TEXTURES = DEGENERATE_TEXTURES
SCHEDULE_PROFILES = ("core", "transfer", "broad")
AXES = {
    "grid_h": {"type": "int", "default": "profile/band draw; core=5", "valid": "1..18"},
    "panel_w": {"type": "int", "default": "profile/band draw; core=4", "valid": "1..14"},
    "left_color": {"type": "color", "default": "profile draw; core=8", "valid": "1..9 (≠4)"},
    "right_color": {"type": "color", "default": "profile draw; core=5", "valid": "1..9 (≠4)"},
    "left_density": {"type": "float", "default": "proposal RNG 0.3..0.7", "valid": "0..1", "exact": False},
    "right_density": {"type": "float", "default": "proposal RNG 0.3..0.7", "valid": "0..1", "exact": False},
    "panel_pattern": {"type": "str", "default": "profile proposal", "valid": "|".join(PANEL_PATTERNS)},
    "xor_target": {"type": "int", "default": "2..area-2 when area>=4", "valid": "0..252"},
    "texture": {"type": "str", "default": "alias or lawful edge", "valid": "|".join(PANEL_PATTERNS + DEGENERATE_TEXTURES)},
}
# Dynamic impossibilities name participating axes on the raised ValueError.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []


def schedule_profile(seed, sample_index, difficulty=None):
    """Every cyclic three-index run contains a guaranteed transfer profile."""
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _incompatible(message, *axes):
    error = ValueError(message)
    error.incompatible_axes = tuple(axes)
    raise error


def _validate_overrides(overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    clean = {key: value for key, value in overrides.items() if value is not None}
    for name, value in clean.items():
        if AXES[name]["type"] in ("int", "color") and type(value) is not int:
            raise ValueError(f"{name} must be an integer")
        if name in ("left_color", "right_color") and value not in COLORS:
            raise ValueError(f"{name} must be a nonzero ARC color other than 4")
        if name in ("grid_h", "panel_w", "xor_target"):
            lo, hi = {"grid_h": (1, 18), "panel_w": (1, 14), "xor_target": (0, 252)}[name]
            if not lo <= value <= hi:
                raise ValueError(f"{name} must be in {lo}..{hi}")
        if name in ("left_density", "right_density"):
            if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 1:
                raise ValueError(f"{name} must be finite and in 0..1")
        if name == "panel_pattern" and value not in PANEL_PATTERNS:
            raise ValueError("unknown panel_pattern")
        if name == "texture" and value not in PANEL_PATTERNS + DEGENERATE_TEXTURES:
            raise ValueError("unknown texture")
    if "texture" in clean and "panel_pattern" in clean and clean["texture"] != clean["panel_pattern"]:
        _incompatible("texture and panel_pattern request different proposals", "texture", "panel_pattern")
    return clean


def _dimension_options(profile, band):
    if profile == "core":
        return [5], [4]
    if band == "easy":
        heights, widths = list(range(4, 9)), list(range(3, 7))
    elif band == "hard":
        heights, widths = list(range(10, 19)), list(range(6, 15))
    else:
        heights, widths = list(range(4, 19)), list(range(3, 15))
    if profile == "transfer":
        heights = [h for h in heights if h != 5]
        widths = [w for w in widths if w != 4]
    return heights, widths


def _dimensions(ctx, profile, band, overrides):
    geometry_profile = profile
    if profile == "broad" and ctx.draw_choice("broad_geometry", ("canonical_shape", "free")) == "canonical_shape":
        # Canonical geometry with a broad palette also decouples shape and color.
        geometry_profile = "core"
    hs, ws = _dimension_options(geometry_profile, band)
    target = overrides.get("xor_target", 0)
    feasible_h = [overrides["grid_h"]] if "grid_h" in overrides else list(range(1, 19))
    feasible_w = [overrides["panel_w"]] if "panel_w" in overrides else list(range(1, 15))
    feasible_h = [h for h in feasible_h if any(h * w >= target for w in feasible_w)]
    if not feasible_h:
        axes = [name for name in ("grid_h", "panel_w", "xor_target") if name in overrides]
        _incompatible("xor_target exceeds area permitted by pinned dimensions", *axes)
    preferred_h = [h for h in hs if h in feasible_h]
    h = ctx.draw_choice("grid_h", feasible_h if "grid_h" in overrides else (preferred_h or feasible_h))
    feasible_w = [w for w in feasible_w if h * w >= target]
    preferred_w = [w for w in ws if w in feasible_w]
    pw = ctx.draw_choice("panel_w", feasible_w if "panel_w" in overrides else (preferred_w or feasible_w))
    return h, pw


def _proposal(h, pw, pattern, density, rng):
    if density == 0:
        return [False] * (h * pw)
    if density == 1:
        return [True] * (h * pw)
    if pattern in ("random", "scatter"):
        probability = density * (0.5 if pattern == "scatter" else 1)
        return [rng.random() < probability for _ in range(h * pw)]
    if pattern == "blob":
        bh, bw = max(1, round(h * density)), max(1, round(pw * density))
        top, left = rng.randrange(h - bh + 1), rng.randrange(pw - bw + 1)
        return [top <= r < top + bh and left <= c < left + bw for r in range(h) for c in range(pw)]
    phase = rng.randrange(2)
    if pattern == "stripes":
        horizontal = rng.randrange(2)
        return [((r if horizontal else c) + phase) % 2 == 0 for r in range(h) for c in range(pw)]
    if pattern == "checker":
        return [(r + c + phase) % 2 == 0 for r in range(h) for c in range(pw)]
    if pattern == "border":
        inset = rng.randrange(1 + min(1, (h - 1) // 2, (pw - 1) // 2))
        return [inset <= r < h - inset and inset <= c < pw - inset and
                (r in (inset, h - inset - 1) or c in (inset, pw - inset - 1))
                for r in range(h) for c in range(pw)]
    offset = rng.randrange(pw)
    return [c == ((r if phase else -r) + offset) % pw for r in range(h) for c in range(pw)]


def _cover_pair(values, positions, alternatives, rng):
    if len(positions) < 2:
        return
    present = {values[i] for i in positions}
    for state in alternatives:
        if state not in present:
            chosen = rng.choice([i for i in positions if values[i] != state])
            values[chosen] = state
            present.add(state)


def _project(left, right, target, rng, overrides):
    values = [2 * a + b for a, b in zip(left, right)]
    different = [i for i, value in enumerate(values) if value in (1, 2)]
    equal = [i for i, value in enumerate(values) if value in (0, 3)]
    if len(different) > target:
        for i in rng.sample(different, len(different) - target):
            values[i] = rng.choice((0, 3))
    elif len(different) < target:
        for i in rng.sample(equal, target - len(different)):
            values[i] = rng.choice((1, 2))
    different = [i for i, value in enumerate(values) if value in (1, 2)]
    equal = [i for i, value in enumerate(values) if value in (0, 3)]
    _cover_pair(values, different, (1, 2), rng)
    _cover_pair(values, equal, (0, 3), rng)
    if len(equal) == 1:
        values[equal[0]] = 3  # Keep both foreground roles visible when possible.
    if len(values) == 1 and target == 1:
        if "left_color" in overrides and "right_color" in overrides:
            _incompatible("one differing cell cannot display both requested foregrounds",
                          "grid_h", "panel_w", "xor_target", "left_color", "right_color")
        if "left_color" in overrides:
            values[0] = 2
        elif "right_color" in overrides:
            values[0] = 1
    return values


def generate(seed, sample_index, *, difficulty=None, **overrides):
    overrides = _validate_overrides(overrides)
    band = "medium" if difficulty is None else difficulty
    if band not in ("easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard, or None")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=band, overrides=overrides)
    profile = schedule_profile(seed, sample_index, band)
    h, pw = _dimensions(ctx, profile, band, overrides)
    area = h * pw
    texture = overrides.get("texture")
    choices = ("random",) if profile == "core" else PANEL_PATTERNS
    pattern = texture if texture in PANEL_PATTERNS else ctx.draw_choice(
        "panel_pattern", PANEL_PATTERNS if "panel_pattern" in overrides else choices)
    transfer_colors = tuple(c for c in COLORS if c not in (8, 5))
    left_options = (8,) if profile == "core" else (transfer_colors if profile == "transfer" else COLORS)
    right_options = (5,) if profile == "core" else (transfer_colors if profile == "transfer" else COLORS)
    left_c = ctx.draw_choice("left_color", COLORS if "left_color" in overrides else left_options)
    right_c = ctx.draw_choice("right_color", COLORS if "right_color" in overrides else right_options)
    ld = overrides["left_density"] if "left_density" in overrides else ctx.draw_rng(f"{band}:left_density").uniform(0.3, 0.7)
    rd = overrides["right_density"] if "right_density" in overrides else ctx.draw_rng(f"{band}:right_density").uniform(0.3, 0.7)
    forced_target = 0 if texture in ("same_panels", "all_zero") else (area if texture == "disjoint_panels" else None)
    if forced_target is not None:
        if "xor_target" in overrides and overrides["xor_target"] != forced_target:
            _incompatible("texture and xor_target require different XOR counts", "texture", "xor_target")
        target = ctx.draw_choice("xor_target", (forced_target,))
    elif "xor_target" in overrides:
        target = ctx.draw_int("xor_target", 0, area)
    else:
        target = ctx.draw_int("xor_target", 2 if area >= 4 else 0, area - 2 if area >= 4 else area)
    if texture == "all_zero":
        invisible = [key for key in ("left_color", "right_color", "left_density", "right_density") if key in overrides]
        if invisible:
            _incompatible("all_zero cannot honor foreground or density controls", "texture", *invisible)
        values = [0] * area
    else:
        left = _proposal(h, pw, pattern, ld, ctx.draw_rng(f"{band}:left_proposal"))
        right = _proposal(h, pw, pattern, rd, ctx.draw_rng(f"{band}:right_proposal"))
        values = _project(left, right, target, ctx.draw_rng(f"{band}:xor_projection"), overrides)
    grid = full_grid(h, 2 * pw + 1, 0)
    for r in range(h):
        grid[r][pw] = 4
        for c in range(pw):
            state = values[r * pw + c]
            grid[r][c] = left_c if state & 2 else 0
            grid[r][pw + 1 + c] = right_c if state & 1 else 0
    return grid


def self_check(grid, *, difficulty=None, meta=None):
    """Validate lawful sampler inputs; teaching completeness is separate."""
    if not isinstance(grid, list) or not grid or not all(isinstance(row, list) and row for row in grid):
        return ["grid must be a nonempty list of nonempty rows"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer ARC colors 0..9; booleans are not colors"]
    h, pw = len(grid), width // 2
    if not 1 <= h <= 18 or width % 2 != 1 or not 1 <= pw <= 14:
        return ["supported height is 1..18 and width is 2*panel_w+1 with panel_w 1..14"]
    if any(row[pw] != 4 for row in grid):
        return ["middle column must be a full color-4 divider"]
    if any(value == 4 for row in grid for c, value in enumerate(row) if c != pw):
        return ["color 4 is reserved for the unique divider"]
    for label, start in (("left", 0), ("right", pw + 1)):
        colors = {row[c] for row in grid for c in range(start, start + pw)} - {0}
        if len(colors) > 1:
            return [f"{label} panel must be empty or monochrome apart from zero"]
    return []


def strict_canonical_like(grid):
    return self_check(grid)


def _states(grid):
    pw = len(grid[0]) // 2
    return [[2 * (row[c] != 0) + (row[pw + 1 + c] != 0) for c in range(pw)] for row in grid]


def observe_overrides(grid):
    h, pw = len(grid), len(grid[0]) // 2
    observed = {"grid_h": h, "panel_w": pw,
                "xor_target": sum(state in (1, 2) for row in _states(grid) for state in row)}
    for label, start in (("left_color", 0), ("right_color", pw + 1)):
        colors = {row[c] for row in grid for c in range(start, start + pw)} - {0}
        if len(colors) == 1:
            observed[label] = next(iter(colors))
    return observed


def _boolean_rule(grid, table):
    """Finite diagnostic hypothesis, never a replacement for Racket labels."""
    return [[2 * ((table >> state) & 1) for state in row] for row in _states(grid)]


def _fixed_palette_xor(grid):
    pw = len(grid[0]) // 2
    return [[2 * ((row[c] == 8) != (row[pw + 1 + c] == 5)) for c in range(pw)] for row in grid]


def _fixed_shape_xor(grid):
    out = _boolean_rule(grid, 6)
    return [[out[r][c] if r < len(out) and c < len(out[0]) else 0 for c in range(4)] for r in range(5)]


def _fixed_separator_xor(grid):
    def nonzero(r, c):
        return c < len(grid[r]) and grid[r][c] != 0
    return [[2 * (nonzero(r, c) != nonzero(r, 5 + c)) for c in range(4)] for r in range(len(grid))]


CANONICAL_SHORTCUTS = {
    "fixed_palette_xor": _fixed_palette_xor,
    "fixed_shape_xor": _fixed_shape_xor,
    "fixed_separator_xor": _fixed_separator_xor,
}
LESSON_COMPETITORS = {f"boolean_{table}": partial(_boolean_rule, table=table) for table in range(16) if table != 6}
LESSON_COMPETITORS.update(CANONICAL_SHORTCUTS)
SEMANTIC_RIVALS = dict(LESSON_COMPETITORS)


def _has_state(grid, state):
    return any(state in row for row in _states(grid))


def _refutes(grid, rival):
    return rival(grid) != _boolean_rule(grid, 6)


SEMANTIC_WITNESSES = {
    "empty_pair": partial(_has_state, state=0),
    "right_only": partial(_has_state, state=1),
    "left_only": partial(_has_state, state=2),
    "occupied_overlap": partial(_has_state, state=3),
    "palette_transfer": partial(_refutes, rival=_fixed_palette_xor),
    "shape_transfer": partial(_refutes, rival=_fixed_shape_xor),
    "separator_transfer": partial(_refutes, rival=_fixed_separator_xor),
}
WITNESS_RIVALS = {
    "empty_pair": ["boolean_7"], "right_only": ["boolean_4"],
    "left_only": ["boolean_2"], "occupied_overlap": ["boolean_14"],
    "palette_transfer": ["fixed_palette_xor"], "shape_transfer": ["fixed_shape_xor"],
    "separator_transfer": ["fixed_separator_xor"],
}


def lesson_identifiable(demos, query):
    """Visible-demo-consistent finite hypotheses must agree on the query.

    The query's output member is never read. This is not universal induction.
    """
    if not isinstance(demos, (list, tuple)) or not demos:
        return ["at least one visible demonstration is required"]
    query_input = query.get("input") if isinstance(query, dict) else query
    problems = self_check(query_input)
    if problems:
        return ["query: " + issue for issue in problems]
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            return [f"demo {index}: input and visible output are required"]
        issues = self_check(demo["input"])
        if issues:
            return [f"demo {index}: {issue}" for issue in issues]
        out, grid = demo["output"], demo["input"]
        if (not isinstance(out, list) or len(out) != len(grid) or
                any(not isinstance(row, list) or len(row) != len(grid[0]) // 2 for row in out) or
                any(type(value) is not int or value not in (0, 2) for row in out for value in row)):
            return [f"demo {index}: output must have panel dimensions and colors 0/2"]
    hypotheses = {"occupancy_xor": partial(_boolean_rule, table=6), **LESSON_COMPETITORS}
    survivors = {name: fn for name, fn in hypotheses.items()
                 if all(fn(demo["input"]) == demo["output"] for demo in demos)}
    if "occupancy_xor" not in survivors:
        return ["visible demonstration labels contradict occupancy XOR"]
    prediction = survivors["occupancy_xor"](query_input)
    disagreement = [name for name, fn in survivors.items() if fn(query_input) != prediction]
    return ["visible examples leave conflicting query predictions: " + ", ".join(disagreement)] if disagreement else []
