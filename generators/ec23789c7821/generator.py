"""Generator for ec23789c7821: interior H3 runs become centered V3 runs.

The canonical rule preserves every non-target cell.  Ordinary draws therefore
contain both transformable horizontal triples and preserved distractors; this
prevents the historical target-only reconstruction shortcut.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "ec23789c7821"
VERSION = "2.1.0"
TASK_ID = "ec23789c7821"
RULE_HASH = "281bfb5a3049"
SUMMARY = (
    "Interior horizontal same-color triples are removed and replaced by "
    "vertical triples centered on their middle columns; all other cells remain."
)
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "at least one interior horizontal same-color run of exactly three",
    "every target has vertical room above and below",
    "ordinary draws include preserved non-target colored cells",
]

PALETTE_KINDS = ("default", "sparse", "dense", "varied_palette")
DEGENERATE_TEXTURES = ("no_runs", "run_too_short", "run_too_long")
HELPFUL_TEXTURES = PALETTE_KINDS
_ALLOWED_OVERRIDES = {
    "grid_h", "grid_w", "palette_kind", "n_runs", "palette_size",
    "position_bias", "n_distinct_colors", "run_density", "texture",
}

AXES = {
    "grid_h": {"type": "int", "default": "rng 7..11", "valid": "5..14"},
    "grid_w": {"type": "int", "default": "rng 8..13", "valid": "5..16"},
    "palette_kind": {"type": "str", "default": "rng helpful", "valid": "|".join(PALETTE_KINDS)},
    "n_runs": {"type": "int", "default": "rng feasible 2..7", "valid": "1..8"},
    "palette_size": {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "position_bias": {"type": "str", "default": "spread", "valid": "spread"},
    "n_distinct_colors": {"type": "int", "default": "equals palette_size", "valid": "1..8"},
    "run_density": {"type": "str", "default": "fixed_3", "valid": "fixed_3"},
    "texture": {"type": "str", "default": "alias for palette_kind", "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

# The only intentional refusals are genuinely impossible cross-axis requests.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [
    {"palette_size": None, "n_distinct_colors": None},
    {"grid_h": None, "grid_w": None, "n_runs": None},
]

_MARKER_TO_KIND = {1: "default", 2: "sparse", 3: "dense", 4: "varied_palette"}
_KIND_TO_MARKER = {value: key for key, value in _MARKER_TO_KIND.items()}


class IncompatibleOverrides(ValueError):
    def __init__(self, message: str, axes):
        super().__init__(message)
        self.axes = tuple(axes)


def _draw_dimension(ctx, name: str, lo: int, hi: int, valid_hi: int) -> int:
    if name in ctx.overrides and ctx.overrides[name] is not None:
        return ctx.draw_int_strict(name, 5, valid_hi)
    return ctx.draw_int_strict(name, lo, hi)


def _palette_order(kind: str) -> list[int]:
    marker = _KIND_TO_MARKER[kind]
    priors = {
        "default": [1, 5, 8, 2, 4, 6, 3, 7, 9],
        "sparse": [2, 8, 5, 1, 9, 4, 6, 3, 7],
        "dense": [3, 6, 7, 2, 4, 8, 1, 5, 9],
        "varied_palette": [4, 1, 9, 3, 8, 2, 7, 5, 6],
    }[kind]
    return [marker] + [color for color in priors if color != marker]


def _target_windows(grid):
    h, w = len(grid), len(grid[0])
    result = []
    for r in range(1, h - 1):
        for c in range(w - 2):
            value = grid[r][c]
            if value != 0 and grid[r][c + 1] == value and grid[r][c + 2] == value:
                result.append((r, c, value))
    return result


def _target_capacity(h: int, w: int) -> int:
    return (h - 2) * len(range(0, w - 2, 4))


def _draw_palette_counts(ctx, normalized) -> int:
    requested_palette = normalized.get("palette_size")
    requested_distinct = normalized.get("n_distinct_colors")
    if requested_palette is not None and requested_distinct is not None and requested_palette != requested_distinct:
        raise IncompatibleOverrides(
            "palette_size and n_distinct_colors must agree because every selected color is deliberately shown",
            ("palette_size", "n_distinct_colors"),
        )
    if requested_palette is not None:
        count = ctx.draw_int_strict("palette_size", 1, 8)
        ctx.draw_int_strict("n_distinct_colors", count, count)
        return count
    if requested_distinct is not None:
        count = ctx.draw_int_strict("n_distinct_colors", 1, 8)
        ctx.draw_int_strict("palette_size", count, count)
        return count
    count = ctx.draw_int_strict("palette_size", 2, 4)
    ctx.draw_int_strict("n_distinct_colors", count, count)
    return count


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - _ALLOWED_OVERRIDES)
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, easy, medium, or hard")

    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        if set(overrides) != {"texture"}:
            raise IncompatibleOverrides(
                "degenerate texture is incompatible with other exact axes: " + ", ".join(sorted(overrides)),
                tuple(sorted(overrides)),
            )
        return _draw_from_degenerate(texture)
    if texture is not None and texture not in HELPFUL_TEXTURES:
        raise ValueError("unknown texture")

    normalized = dict(overrides)
    if texture in HELPFUL_TEXTURES:
        if normalized.get("palette_kind") not in (None, texture):
            raise IncompatibleOverrides(
                "palette_kind and texture must agree", ("palette_kind", "texture")
            )
        normalized["palette_kind"] = texture

    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=normalized)
    if difficulty == "easy":
        h = _draw_dimension(ctx, "grid_h", 7, 8, 14)
        w = _draw_dimension(ctx, "grid_w", 8, 10, 16)
        run_band = (2, 3)
    elif difficulty == "hard":
        h = _draw_dimension(ctx, "grid_h", 10, 14, 14)
        w = _draw_dimension(ctx, "grid_w", 12, 16, 16)
        run_band = (4, 7)
    else:
        h = _draw_dimension(ctx, "grid_h", 8, 11, 14)
        w = _draw_dimension(ctx, "grid_w", 9, 13, 16)
        run_band = (3, 5)

    palette_kind = ctx.draw_choice("palette_kind", PALETTE_KINDS)
    ctx.draw_choice("texture", (palette_kind,))
    ctx.draw_choice("position_bias", ("spread",))
    ctx.draw_choice("run_density", ("fixed_3",))
    palette_count = _draw_palette_counts(ctx, normalized)

    capacity = _target_capacity(h, w)
    if "n_runs" in normalized and normalized["n_runs"] is not None:
        n_runs = ctx.draw_int_strict("n_runs", 1, 8)
        if n_runs > capacity:
            raise IncompatibleOverrides(
                f"n_runs={n_runs} cannot fit grid_h={h}, grid_w={w}",
                ("n_runs", "grid_h", "grid_w"),
            )
    else:
        low = min(run_band[0], capacity)
        high = min(run_band[1], capacity)
        if high < 1:
            raise ValueError("grid is too small for one interior horizontal triple")
        n_runs = ctx.draw_int_strict("n_runs", max(1, low), max(1, high))

    rng = ctx.draw_rng("layout")
    palette = _palette_order(palette_kind)
    marker = palette[0]
    remainder = palette[1:]
    rng.shuffle(remainder)
    palette = [marker] + remainder[: palette_count - 1]

    grid = full_grid(h, w, 0)
    # A boundary singleton is both an honest palette-kind cue and a guaranteed
    # preserved non-target cell, directly closing the retained teaching hole.
    grid[0][0] = marker

    slots = [(r, c) for r in range(1, h - 1) for c in range(0, w - 2, 4)]
    rng.shuffle(slots)
    chosen = slots[:n_runs]
    for index, (r, c) in enumerate(chosen):
        color = palette[index % len(palette)]
        grid[r][c:c + 3] = [color, color, color]

    # Show every selected palette color at least once without creating new H3s.
    used_colors = {value for row in grid for value in row if value != 0}
    boundary = (
        [(0, c) for c in range(1, w)]
        + [(h - 1, c) for c in range(w)]
        + [(r, w - 1) for r in range(1, h - 1)]
    )
    cursor = 0
    for color in palette:
        if color in used_colors:
            continue
        while cursor < len(boundary) and grid[boundary[cursor][0]][boundary[cursor][1]] != 0:
            cursor += 1
        if cursor >= len(boundary):
            raise ValueError("cannot expose every palette color on this grid")
        r, c = boundary[cursor]
        grid[r][c] = color
        used_colors.add(color)
        cursor += 1

    # A preserved length-two distractor refutes the stronger target-only rival.
    pair_color = palette[-1]
    placed_pair = False
    for r in (h - 1, 0):
        for c in range(0, w - 1):
            if grid[r][c] == grid[r][c + 1] == 0:
                grid[r][c] = grid[r][c + 1] = pair_color
                placed_pair = True
                break
        if placed_pair:
            break
    if not placed_pair:
        raise ValueError("cannot place preserved two-cell distractor")

    errors = self_check(grid)
    if errors:
        raise ValueError("constructed invalid scene: " + "; ".join(errors))
    return grid


def rule_mirror(grid):
    """Literal Python mirror of the canonical Racket program."""
    h, w = len(grid), len(grid[0])
    windows = _target_windows(grid)
    used = {(r, cc) for r, c, _ in windows for cc in (c, c + 1, c + 2)}
    out = full_grid(h, w, 0)
    for r, c, color in windows:
        center = c + 1
        out[r - 1][center] = color
        out[r][center] = color
        out[r + 1][center] = color
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 0 and (r, c) not in used:
                out[r][c] = grid[r][c]
    return out


def self_check(grid, *, difficulty=None, meta=None):
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        return ["grid is not a non-empty 2D list"]
    h, w = len(grid), len(grid[0])
    errors = []
    if any(type(row) is not list or len(row) != w for row in grid):
        return ["grid is ragged"]
    if not 5 <= h <= 30 or not 5 <= w <= 30:
        errors.append("grid dimensions must stay within ARC bounds and allow the rule")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        errors.append("cells must be exact ARC colors 0..9")
        return errors
    windows = _target_windows(grid)
    if not windows:
        errors.append("ordinary scene needs at least one interior horizontal triple")
    used = {(r, cc) for r, c, _ in windows for cc in (c, c + 1, c + 2)}
    preserved = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
                 if value != 0 and (r, c) not in used]
    if not preserved:
        errors.append("ordinary scene needs a preserved non-target colored cell")
    return errors


def observe_overrides(grid):
    colors = {value for row in grid for value in row if value != 0}
    marker = grid[0][0] if grid and grid[0] else 0
    observed = {
        "n_runs": len(_target_windows(grid)),
        "palette_size": len(colors),
        "n_distinct_colors": len(colors),
        "position_bias": "spread",
        "run_density": "fixed_3",
    }
    if marker in _MARKER_TO_KIND:
        observed["palette_kind"] = _MARKER_TO_KIND[marker]
        observed["texture"] = _MARKER_TO_KIND[marker]
    return observed


def _draw_from_degenerate(name):
    h, w = 9, 11
    grid = full_grid(h, w, 0)
    if name == "no_runs":
        grid[0][0] = 4
        grid[2][3] = 4
        grid[5][7] = 6
    elif name == "run_too_short":
        grid[0][0] = 3
        grid[2][2] = grid[2][3] = 3
        grid[5][6] = grid[5][7] = 5
    elif name == "run_too_long":
        # The canonical rule only turns interior triples; a top-edge long run
        # is a lawful preserved non-target boundary case.
        grid[0][0] = 7
        for c in range(2, 7):
            grid[0][c] = 7
    return grid
