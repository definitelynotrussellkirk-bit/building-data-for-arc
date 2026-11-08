"""Generator for arc_puzzle_bank_twentysecond21:E148.

Rule: every non-zero marker in the first row emits a same-colour diagonal ray
that moves one row down and one column right per step, stopping at the first
grid edge.  All non-ray cells are background 0.

The teaching distribution deliberately puts at least one marker whose ray
reaches the bottom row and one whose ray is clipped by the right edge before
reaching the bottom.  This blocks fixed-length and one-edge shortcut
interpretations while remaining faithful to all canonical train/test inputs.
"""
from __future__ import annotations

from collections.abc import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "82a4545adba4"
TASK_ID = "82a4545adba4"
VERSION = "2.1.0"  # reject corner-tie scenes that hide strict right clipping
RULE_HASH = "be4eaba83110"

SUMMARY = (
    "A 0-background grid has 2-5 distinct-colour markers only in row 0. "
    "Each marker emits its colour down-right to the first grid edge. "
    "Ordinary lessons include both a bottom-reaching ray and a strictly "
    "right-clipped ray."
)

INVARIANTS = [
    "background is 0",
    "2-5 non-zero markers occupy distinct columns in row 0",
    "marker colours are distinct",
    "all rows below row 0 are blank",
    "no marker is in the final column",
    "width is at least height so a bottom-reaching ray is possible",
    "at least one marker reaches the bottom row and one is strictly "
    "right-clipped",
]

HELPFUL_TEXTURES = ("canonical", "sparse", "dense", "varied_palette")
DEGENERATE_TEXTURES: tuple[str, ...] = ()

_H_LO, _H_HI = 4, 10
_W_LO, _W_HI = 5, 12
_N_LO, _N_HI = 2, 5
_CANONICAL_PROFILES = ((5, 7), (6, 6), (5, 8))
_CANONICAL_PRIOR_P = 0.45

AXES = {
    "grid_h": {
        "type": "int",
        "default": "band rng 4..6 easy, 5..8 medium, 7..10 hard; canonical prior",
        "valid": "4..10",
    },
    "grid_w": {
        "type": "int",
        "default": "band rng 6..8 easy, 7..10 medium, 9..12 hard; adjusted to fit h and markers",
        "valid": "5..12",
    },
    "n_markers": {
        "type": "int",
        "default": "band rng 2..3 easy, 2..4 medium, 3..5 hard; canonical prior uses 2",
        "valid": "2..5",
    },
    "texture": {
        "type": "str",
        "default": "rng helpful",
        "valid": "|".join(HELPFUL_TEXTURES),
    },
}

EXAMPLES_NEEDED = 2
MIN_STRICT_FRAC = 0.30


def _is_arc_grid(grid) -> bool:
    return bool(
        isinstance(grid, list)
        and grid
        and isinstance(grid[0], list)
        and grid[0]
        and all(isinstance(row, list) and len(row) == len(grid[0]) for row in grid)
        and all(
            isinstance(value, int)
            and not isinstance(value, bool)
            and 0 <= value <= 9
            for row in grid
            for value in row
        )
    )


def _marker_cells(grid) -> list[tuple[int, int]]:
    if not _is_arc_grid(grid):
        return []
    return [(c, value) for c, value in enumerate(grid[0]) if value != 0]


def _ray_reaches_bottom(h: int, w: int, c: int) -> bool:
    return c + h - 1 <= w - 1


def _ray_is_strictly_right_clipped(h: int, w: int, c: int) -> bool:
    return c + h - 1 > w - 1


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the complete lawful input grammar, not merely shape/palette."""
    del difficulty, meta
    if not _is_arc_grid(grid):
        return ["grid must be a nonempty rectangular ARC grid"]

    h, w = len(grid), len(grid[0])
    errors: list[str] = []
    if not (_H_LO <= h <= _H_HI and _W_LO <= w <= _W_HI):
        errors.append(
            f"dimensions {h}x{w} outside {_H_LO}..{_H_HI} by {_W_LO}..{_W_HI}"
        )
    if w < h:
        errors.append("width must be at least height")

    markers = _marker_cells(grid)
    if not (_N_LO <= len(markers) <= _N_HI):
        errors.append(f"expected {_N_LO}-{_N_HI} row-0 markers, found {len(markers)}")
    colors = [color for _, color in markers]
    if len(colors) != len(set(colors)):
        errors.append("marker colours must be distinct")
    if any(c == w - 1 for c, _ in markers):
        errors.append("marker in final column yields a degenerate length-1 ray")
    if any(value != 0 for row in grid[1:] for value in row):
        errors.append("rows below row 0 must be blank")

    if markers and not any(_ray_reaches_bottom(h, w, c) for c, _ in markers):
        errors.append("no marker ray reaches the bottom row")
    if markers and not any(
        _ray_is_strictly_right_clipped(h, w, c) for c, _ in markers
    ):
        errors.append("no marker ray is strictly clipped by the right edge")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Task-linked canonical manifold used by the semantic gate."""
    errors = self_check(grid)
    if errors:
        return errors
    h, w = len(grid), len(grid[0])
    reasons: list[str] = []
    if (h, w) not in _CANONICAL_PROFILES:
        reasons.append(
            f"dimensions {h}x{w} not in canonical profiles {_CANONICAL_PROFILES}"
        )
    if len(_marker_cells(grid)) != 2:
        reasons.append("canonical examples contain exactly two row-0 markers")
    return reasons


def observe_overrides(grid) -> dict[str, int]:
    """Recover exact semantic axis values from the returned grid."""
    return {"n_markers": len(_marker_cells(grid))}


def _draw_int_full_if_overridden(ctx, overrides, label, lo, hi, valid_lo, valid_hi):
    if overrides.get(label) is not None:
        return ctx.draw_int(label, valid_lo, valid_hi)
    return ctx.draw_int(label, lo, hi)


def _validate_override_keys(overrides: dict) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")


def _coerce_declared_int(overrides: dict, label: str, lo: int, hi: int):
    value = overrides.get(label)
    if value is None:
        return None
    value = int(value)
    if not lo <= value <= hi:
        raise ValueError(f"{label} override {value} outside declared {lo}..{hi}")
    return value


def _spread_columns(w: int, n: int) -> list[int]:
    chosen = [0, w - 2]
    candidates = set(range(1, w - 2))
    while len(chosen) < n:
        candidate = max(
            candidates,
            key=lambda c: (min(abs(c - x) for x in chosen), -c),
        )
        chosen.append(candidate)
        candidates.remove(candidate)
    return sorted(chosen[:n])


def _dense_columns(w: int, h: int, n: int) -> list[int]:
    boundary = w - h
    chosen = {boundary, boundary + 1}
    candidates = [c for c in range(w - 1) if c not in chosen]
    center = boundary + 0.5
    candidates.sort(key=lambda c: (abs(c - center), c))
    for c in candidates:
        if len(chosen) >= n:
            break
        chosen.add(c)
    return sorted(chosen)


def _random_branch_complete_columns(w: int, h: int, n: int, rng) -> list[int]:
    boundary = w - h
    bottom_zone = list(range(0, boundary + 1))
    right_zone = list(range(boundary + 1, w - 1))
    chosen = {rng.choice(bottom_zone), rng.choice(right_zone)}
    remaining = [c for c in range(w - 1) if c not in chosen]
    rng.shuffle(remaining)
    chosen.update(remaining[: n - len(chosen)])
    return sorted(chosen)


def _columns_for_texture(texture: str, w: int, h: int, n: int, rng) -> list[int]:
    if texture == "sparse":
        return _spread_columns(w, n)
    if texture == "dense":
        return _dense_columns(w, h, n)
    if texture == "canonical":
        boundary = w - h
        bottom_zone = list(range(0, boundary + 1))
        right_zone = list(range(boundary + 1, w - 1))
        left = rng.choice(bottom_zone)
        # Prefer a clearly clipped ray, but retain positional variation.
        right_candidates = sorted(right_zone, key=lambda c: (abs(c - (left + 3)), c))
        chosen = {left, right_candidates[rng.randrange(min(2, len(right_candidates)))]}
        remaining = [c for c in range(w - 1) if c not in chosen]
        rng.shuffle(remaining)
        chosen.update(remaining[: n - len(chosen)])
        return sorted(chosen)
    return _random_branch_complete_columns(w, h, n, rng)


def _colors_for_texture(texture: str, n: int, rng) -> list[int]:
    pools = {
        "canonical": (2, 3, 4, 5, 6, 7),
        "sparse": (1, 2, 3, 4, 5, 6),
        "dense": (4, 5, 6, 7, 8, 9),
        "varied_palette": (1, 2, 3, 4, 5, 6, 7, 8, 9),
    }
    return rng.sample(list(pools[texture]), n)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_override_keys(overrides)
    raw_h = _coerce_declared_int(overrides, "grid_h", _H_LO, _H_HI)
    raw_w = _coerce_declared_int(overrides, "grid_w", _W_LO, _W_HI)
    raw_n = _coerce_declared_int(overrides, "n_markers", _N_LO, _N_HI)
    if raw_h is not None and raw_w is not None and raw_w < raw_h:
        raise ValueError("grid_w must be >= grid_h")
    if raw_w is not None and raw_n is not None and raw_n > raw_w - 1:
        raise ValueError("n_markers must fit in non-final top-row columns")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    texture = ctx.draw_choice("texture", HELPFUL_TEXTURES)
    prior_rng = ctx.draw_rng("canonical_prior")
    numeric_override = any(raw is not None for raw in (raw_h, raw_w, raw_n))
    canonical_draw = not numeric_override and (
        texture == "canonical" or prior_rng.random() < _CANONICAL_PRIOR_P
    )

    if canonical_draw:
        profile_rng = ctx.draw_rng("canonical_profile")
        h, w = profile_rng.choice(_CANONICAL_PROFILES)
        h = ctx.draw_int("grid_h", h, h)
        w = ctx.draw_int("grid_w", w, w)
        n = ctx.draw_int("n_markers", 2, 2)
    else:
        band = difficulty or "medium"
        if band == "easy":
            h_lo, h_hi, w_lo, w_hi, n_lo, n_hi = 4, 6, 6, 8, 2, 3
        elif band == "hard":
            h_lo, h_hi, w_lo, w_hi, n_lo, n_hi = 7, 10, 9, 12, 3, 5
        else:
            h_lo, h_hi, w_lo, w_hi, n_lo, n_hi = 5, 8, 7, 10, 2, 4

        if raw_w is not None:
            h_lo, h_hi = _H_LO, min(_H_HI, raw_w)
            n_lo, n_hi = _N_LO, min(_N_HI, raw_w - 1)
        h = _draw_int_full_if_overridden(
            ctx, overrides, "grid_h", h_lo, h_hi, _H_LO, _H_HI
        )
        n = _draw_int_full_if_overridden(
            ctx, overrides, "n_markers", n_lo, n_hi, _N_LO, _N_HI
        )

        min_w = max(_W_LO, h, n + 1)
        if raw_w is None:
            w_lo = max(w_lo, min_w)
            w_hi = max(w_hi, w_lo)
        w = _draw_int_full_if_overridden(
            ctx, overrides, "grid_w", w_lo, w_hi, _W_LO, _W_HI
        )
        if w < h:
            raise ValueError("grid_w must be >= grid_h")
        if n > w - 1:
            raise ValueError("n_markers must fit in non-final top-row columns")

    layout_rng = ctx.draw_rng("layout")
    color_rng = ctx.draw_rng("colors")
    columns = _columns_for_texture(texture, w, h, n, layout_rng)
    colors = _colors_for_texture(texture, n, color_rng)
    grid = full_grid(h, w, 0)
    for column, color in zip(columns, colors):
        grid[0][column] = color
    return grid


def rule_mirror(grid) -> list[list[int]]:
    """Pure Python mirror used only for tests and lesson diagnostics."""
    if not _is_arc_grid(grid):
        raise ValueError("not an ARC grid")
    h, w = len(grid), len(grid[0])
    out = full_grid(h, w, 0)
    for c, color in _marker_cells(grid):
        k = 0
        while k < h and c + k < w:
            out[k][c + k] = color
            k += 1
    return out


def _vertical_competitor(grid) -> list[list[int]]:
    h, w = len(grid), len(grid[0])
    out = full_grid(h, w, 0)
    for c, color in _marker_cells(grid):
        for r in range(h):
            out[r][c] = color
    return out


def _down_left_competitor(grid) -> list[list[int]]:
    h, w = len(grid), len(grid[0])
    out = full_grid(h, w, 0)
    for c, color in _marker_cells(grid):
        k = 0
        while k < h and c - k >= 0:
            out[k][c - k] = color
            k += 1
    return out


def _first_marker_only_competitor(grid) -> list[list[int]]:
    h, w = len(grid), len(grid[0])
    out = full_grid(h, w, 0)
    markers = _marker_cells(grid)
    if not markers:
        return out
    c, color = markers[0]
    for k in range(min(h, w - c)):
        out[k][c + k] = color
    return out


def _monochrome_competitor(grid) -> list[list[int]]:
    markers = _marker_cells(grid)
    if not markers:
        return rule_mirror(grid)
    color = markers[0][1]
    recolored = [row[:] for row in grid]
    for c, _ in markers:
        recolored[0][c] = color
    return rule_mirror(recolored)


def _bottom_complete_only_competitor(grid) -> list[list[int]]:
    """Extend only markers whose full diagonal reaches the bottom row."""
    h, w = len(grid), len(grid[0])
    out = full_grid(h, w, 0)
    for c, color in _marker_cells(grid):
        out[0][c] = color
        if _ray_reaches_bottom(h, w, c):
            for k in range(1, h):
                out[k][c + k] = color
    return out


_LESSON_COMPETITORS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "copy the input without extending markers": lambda grid: [row[:] for row in grid],
    "paint vertical rays": _vertical_competitor,
    "paint down-left rays": _down_left_competitor,
    "extend only the leftmost marker": _first_marker_only_competitor,
    "extend only rays that reach the bottom": _bottom_complete_only_competitor,
    "recolour every ray with the first marker colour": _monochrome_competitor,
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons where a simple competing rule survives all demos."""
    reasons: list[str] = []
    for index, item in enumerate([*demos, query]):
        label = f"demo {index}" if index < len(demos) else "query"
        input_grid = item.get("input")
        output_grid = item.get("output")
        errors = self_check(input_grid)
        if errors:
            reasons.append(f"{label} input is outside the teaching grammar: {errors}")
            continue
        if rule_mirror(input_grid) != output_grid:
            reasons.append(f"{label} output does not match down-right emission")
    if reasons:
        return reasons

    for name, competitor in _LESSON_COMPETITORS.items():
        survives = all(competitor(demo["input"]) == demo["output"] for demo in demos)
        if survives and competitor(query["input"]) != query["output"]:
            reasons.append(
                f"competing rule '{name}' fits every demo but changes the query answer"
            )
    return reasons


def _witness_bottom_reaching(grid) -> bool:
    if self_check(grid):
        return False
    h, w = len(grid), len(grid[0])
    return any(_ray_reaches_bottom(h, w, c) for c, _ in _marker_cells(grid))


def _witness_right_clipped(grid) -> bool:
    if self_check(grid):
        return False
    h, w = len(grid), len(grid[0])
    return any(
        _ray_is_strictly_right_clipped(h, w, c) for c, _ in _marker_cells(grid)
    )


def _witness_canonical_profile(grid) -> bool:
    return not strict_canonical_like(grid)


SEMANTIC_WITNESSES = {
    "bottom_reaching_ray": _witness_bottom_reaching,
    "right_clipped_ray": _witness_right_clipped,
    "canonical_two_marker_profile": _witness_canonical_profile,
}
