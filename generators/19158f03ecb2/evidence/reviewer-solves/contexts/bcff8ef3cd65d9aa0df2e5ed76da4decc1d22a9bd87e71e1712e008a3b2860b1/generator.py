"""Generator for ARC task 6d0aefbc / content hash 19158f03ecb2.

The oracle appends a left-right reflection of the input.  Default five-pair
lessons make sample indices 0..2 asymmetric and indices 3..4 symmetric.
That keeps both the downstream 3-demo/1-query materializer and the standard
4-demo/1-query runner on a symmetric query while retaining asymmetric evidence
that rejects the tempting ``hconcat(g, g)`` shortcut.
"""
from __future__ import annotations

from collections import Counter
from math import ceil
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.textures import (
    apply_bg_density,
    apply_noise_overlay,
    fill_texture,
)


GENERATOR_ID = "19158f03ecb2"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "1bf14d2f29b0"  # normalized canonical program_solution

SUMMARY = (
    "Append a horizontal reflection of the complete input grid: every output "
    "row is the input row followed by that row in reverse order."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "input height and width are each 3..15, so output width is at most 30",
    "the input uses exactly 2..10 ARC colors with nontrivial two-dimensional structure",
    "default sample indices 0..2 modulo 5 are LR-asymmetric demonstrations",
    "default sample indices 3..4 modulo 5 are LR-symmetric so 3+1 and 4+1 lessons end on the held-out branch",
    "the asymmetric demonstrations distinguish reflection from simple horizontal duplication",
]

CANONICAL_TEXTURE = "canonical_mosaic"
HELPFUL_TEXTURES = (
    CANONICAL_TEXTURE,
    "noise",
    "sparse",
    "checkerboard",
    "frame",
    "plus",
)
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "40% canonical 3; otherwise difficulty-weighted 3..15",
        "valid": "3..15",
    },
    "grid_w": {
        "type": "int",
        "default": "40% canonical 3; otherwise difficulty-weighted 3..15",
        "valid": "3..15",
    },
    "palette_size": {
        "type": "int",
        "default": "40% canonical 2 or 3; otherwise difficulty-weighted 2..8",
        "valid": "2..10",
    },
    "texture": {
        "type": "str",
        "default": "40% canonical_mosaic; otherwise difficulty-weighted texture",
        "valid": "canonical_mosaic|noise|sparse|checkerboard|frame|plus",
    },
    "bg_density": {
        "type": "float",
        "default": "0 on canonical-profile draws; otherwise difficulty-aware 0..0.55",
        "valid": "0..0.7",
    },
    "noise_overlay": {
        "type": "float",
        "default": "0 on canonical-profile draws; otherwise difficulty-aware 0..0.15",
        "valid": "0..0.25",
    },
    "lr_asymmetric": {
        "type": "bool",
        "default": "true for indices 0..2 modulo 5; false for indices 3..4",
        "valid": "true|false",
    },
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic input from the lesson-aware distribution."""
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    canonical_profile = (
        sample_index % 5 in (0, 4)
        and not any(
            name in overrides
            for name in (
                "grid_h",
                "grid_w",
                "palette_size",
                "texture",
                "bg_density",
                "noise_overlay",
            )
        )
    )

    lr_asymmetric = bool(
        ctx.draw_choice(
            "lr_asymmetric",
            (False, True) if "lr_asymmetric" in overrides else (sample_index % 5 < 3,),
        )
    )
    palette_size = _draw_palette_size(ctx, difficulty, canonical_profile)
    h, w = _draw_dimensions(ctx, difficulty, canonical_profile, palette_size, lr_asymmetric)
    texture = _draw_texture(ctx, difficulty, canonical_profile)
    bg_density = _draw_float_axis(
        ctx,
        "bg_density",
        0.0,
        0.7,
        0.0 if canonical_profile else _default_bg_density(ctx, difficulty),
    )
    noise_overlay = _draw_float_axis(
        ctx,
        "noise_overlay",
        0.0,
        0.25,
        0.0 if canonical_profile else _default_noise_overlay(ctx, difficulty),
    )

    palette = list(ctx.draw_distinct_colors("palette", n=palette_size))
    rng = ctx.draw_rng("layout")

    for _ in range(256):
        if texture == CANONICAL_TEXTURE:
            grid = _canonical_mosaic(h, w, palette, rng)
        else:
            grid = fill_texture(texture, h, w, palette, rng)
        if bg_density > 0.0:
            grid = apply_bg_density(grid, palette, rng, bg_density)
        if noise_overlay > 0.0:
            grid = apply_noise_overlay(grid, palette, rng, noise_overlay)

        if lr_asymmetric:
            _stamp_palette_asymmetric(grid, palette, rng)
            _ensure_lr_asymmetric(grid, palette, rng)
        else:
            _make_lr_symmetric(grid)
            _stamp_palette_symmetric(grid, palette, rng)

        meta = {
            "grid_h": h,
            "grid_w": w,
            "palette_size": palette_size,
            "lr_asymmetric": lr_asymmetric,
        }
        if not self_check(grid, difficulty=difficulty, meta=meta):
            return [row[:] for row in grid]

    raise ValueError("unable to construct a non-degenerate mirror lesson after 256 attempts")


def _draw_palette_size(ctx, difficulty, canonical_profile: bool) -> int:
    if "palette_size" in ctx.overrides:
        options = tuple(range(2, 11))
    elif canonical_profile:
        options = (2, 3, 3)
    elif difficulty == "easy":
        options = (2, 2, 3, 3, 4)
    elif difficulty == "hard":
        options = (3, 4, 5, 6, 7, 8)
    else:
        options = (2, 3, 3, 4, 5, 6)
    return int(ctx.draw_choice("palette_size", options))


def _draw_dimensions(ctx, difficulty, canonical_profile, palette_size, lr_asymmetric):
    if "grid_h" in ctx.overrides:
        h_options = tuple(range(3, 16))
    elif canonical_profile:
        h_options = (3,)
    elif difficulty == "easy":
        h_options = (3, 3, 4, 4, 5, 6)
    elif difficulty == "hard":
        h_options = (6, 8, 10, 12, 14, 15)
    else:
        h_options = tuple(range(3, 13))

    if "grid_w" in ctx.overrides:
        w_options = tuple(range(3, 16))
    elif canonical_profile:
        w_options = (3,)
    elif difficulty == "easy":
        w_options = (3, 3, 4, 4, 5, 6)
    elif difficulty == "hard":
        w_options = (6, 8, 10, 12, 14, 15)
    else:
        w_options = tuple(range(3, 13))

    requested_h = _optional_int_override(ctx, "grid_h")
    requested_w = _optional_int_override(ctx, "grid_w")
    if (
        requested_h is not None
        and requested_w is not None
        and _palette_capacity(requested_h, requested_w, lr_asymmetric) < palette_size
    ):
        raise ValueError("requested dimensions cannot realize the requested palette/symmetry")
    if requested_w is not None:
        h_options = tuple(
            h for h in h_options
            if _palette_capacity(h, requested_w, lr_asymmetric) >= palette_size
        )
    if requested_h is not None:
        w_options = tuple(
            w for w in w_options
            if _palette_capacity(requested_h, w, lr_asymmetric) >= palette_size
        )
    h_options = tuple(
        h for h in h_options
        if any(_palette_capacity(h, w, lr_asymmetric) >= palette_size for w in w_options)
    )
    if not h_options or not w_options:
        raise ValueError("requested dimensions cannot realize the requested palette/symmetry")

    h = int(ctx.draw_choice("grid_h", h_options))
    w_options = tuple(
        w for w in w_options
        if _palette_capacity(h, w, lr_asymmetric) >= palette_size
    )
    if not w_options:
        raise ValueError("requested width cannot realize the requested palette/symmetry")
    w = int(ctx.draw_choice("grid_w", w_options))
    return h, w


def _optional_int_override(ctx, label: str) -> int | None:
    value = ctx.overrides.get(label)
    return None if value is None else int(value)


def _palette_capacity(h: int, w: int, lr_asymmetric: bool) -> int:
    return h * w if lr_asymmetric else h * ceil(w / 2)


def _draw_texture(ctx, difficulty, canonical_profile: bool) -> str:
    if "texture" in ctx.overrides:
        options = HELPFUL_TEXTURES
    elif canonical_profile:
        options = (CANONICAL_TEXTURE,)
    elif difficulty == "easy":
        options = (CANONICAL_TEXTURE, "sparse", "plus", "frame", "checkerboard", "noise")
    elif difficulty == "hard":
        options = ("noise", "checkerboard", "frame", "plus", "sparse", CANONICAL_TEXTURE)
    else:
        options = HELPFUL_TEXTURES
    return str(ctx.draw_choice("texture", options))


def _draw_float_axis(ctx, label: str, lo: float, hi: float, default: float) -> float:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        value = float(ctx.overrides[label])
        if not lo <= value <= hi:
            raise ValueError(f"{label} override {value} outside [{lo}, {hi}]")
        ctx._record(label, value, from_override=True)
        return value
    value = float(default)
    ctx._record(label, value, from_override=False)
    return value


def _default_bg_density(ctx, difficulty) -> float:
    hi = {"easy": 0.25, "hard": 0.55}.get(difficulty, 0.4)
    return ctx.draw_rng("bg_density_value").uniform(0.0, hi)


def _default_noise_overlay(ctx, difficulty) -> float:
    hi = {"easy": 0.04, "hard": 0.15}.get(difficulty, 0.09)
    return ctx.draw_rng("noise_overlay_value").uniform(0.0, hi)


def _canonical_mosaic(h: int, w: int, palette: list[int], rng) -> list[list[int]]:
    """Dense small-grid-like texture with both row and column evidence."""
    grid = full_grid(h, w, palette[0])
    for r in range(h):
        for c in range(w):
            # Uneven arithmetic phase avoids checkerboard/stripe shortcuts.
            idx = (r * (c + 2) + c * c + rng.randrange(len(palette))) % len(palette)
            grid[r][c] = palette[idx]
    return grid


def _make_lr_symmetric(grid: list[list[int]]) -> None:
    w = len(grid[0])
    for row in grid:
        for c in range(w // 2):
            row[w - 1 - c] = row[c]


def _stamp_palette_symmetric(grid, palette, rng) -> None:
    h, w = len(grid), len(grid[0])
    reps = [(r, c) for r in range(h) for c in range((w + 1) // 2)]
    if len(reps) < len(palette):
        raise ValueError("symmetric grid has insufficient independent cells for palette")
    rng.shuffle(reps)
    for color, (r, c) in zip(palette, reps):
        grid[r][c] = color
        grid[r][w - 1 - c] = color


def _stamp_palette_asymmetric(grid, palette, rng) -> None:
    cells = [(r, c) for r in range(len(grid)) for c in range(len(grid[0]))]
    if len(cells) < len(palette):
        raise ValueError("grid has insufficient cells for palette")
    rng.shuffle(cells)
    for color, (r, c) in zip(palette, cells):
        grid[r][c] = color


def _ensure_lr_asymmetric(grid, palette, rng) -> None:
    if not _is_lr_symmetric(grid):
        return
    h, w = len(grid), len(grid[0])
    counts = Counter(value for row in grid for value in row)
    candidates = [
        (r, c)
        for r in range(h)
        for c in range(w // 2)
        if counts[grid[r][w - 1 - c]] > 1
    ]
    rng.shuffle(candidates)
    for r, c in candidates:
        mirror = w - 1 - c
        old = grid[r][mirror]
        choices = [color for color in palette if color != grid[r][c] and color != old]
        if not choices:
            choices = [color for color in palette if color != grid[r][c]]
        if choices:
            grid[r][mirror] = rng.choice(choices)
            return
    raise ValueError("could not create an LR-asymmetric witness without losing palette support")


def _is_lr_symmetric(grid) -> bool:
    return all(row == list(reversed(row)) for row in grid)


def _nonmodal_cells(grid) -> tuple[int, list[tuple[int, int]]]:
    counts = Counter(value for row in grid for value in row)
    modal = min(counts, key=lambda value: (-counts[value], value))
    cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != modal
    ]
    return modal, cells


def observe_overrides(grid) -> dict[str, Any]:
    """Recover every exact per-instance semantic axis from the returned grid."""
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "palette_size": len({value for row in grid for value in row}),
        "lr_asymmetric": not _is_lr_symmetric(grid),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed or shortcut-only scenes while accepting official inputs."""
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid must be a nonempty list of rows"]
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid must be rectangular and nonempty"]
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["grid values must be ARC colors 0..9"]

    h, w = len(grid), width
    if not (3 <= h <= 15 and 3 <= w <= 15):
        errors.append(f"input dimensions must be within 3..15, got {h}x{w}")

    colors = {value for row in grid for value in row}
    if not (2 <= len(colors) <= 10):
        errors.append(f"input must contain 2..10 colors, got {len(colors)}")

    if len(colors) >= 2:
        _, nonmodal = _nonmodal_cells(grid)
        rows = {r for r, _ in nonmodal}
        cols = {c for _, c in nonmodal}
        if len(nonmodal) < 3:
            errors.append("non-modal structure needs at least three cells")
        if len(rows) < 2 or len(cols) < 2:
            errors.append("non-modal structure must span at least two rows and columns")
        if nonmodal:
            r0, r1 = min(rows), max(rows)
            c0, c1 = min(cols), max(cols)
            if len(nonmodal) == (r1 - r0 + 1) * (c1 - c0 + 1):
                errors.append("non-modal structure may not be a single filled rectangle")

    if meta:
        expected_h = meta.get("grid_h")
        expected_w = meta.get("grid_w")
        expected_palette = meta.get("palette_size")
        expected_asymmetry = meta.get("lr_asymmetric")
        if expected_h is not None and h != expected_h:
            errors.append(f"grid_h mismatch: expected {expected_h}, got {h}")
        if expected_w is not None and w != expected_w:
            errors.append(f"grid_w mismatch: expected {expected_w}, got {w}")
        if expected_palette is not None and len(colors) != expected_palette:
            errors.append(
                f"palette_size mismatch: expected {expected_palette}, got {len(colors)}"
            )
        if expected_asymmetry is not None and (not _is_lr_symmetric(grid)) != bool(expected_asymmetry):
            errors.append(
                f"lr_asymmetric mismatch: expected {bool(expected_asymmetry)}, "
                f"got {not _is_lr_symmetric(grid)}"
            )
    return errors


def mutation_fixtures():
    """Task-local must-reject shortcut scenes for the strict defect lint."""
    return [
        ("monochrome", [[0] * 5 for _ in range(5)]),
        ("singleton", [[9 if (r, c) == (2, 2) else 0 for c in range(5)] for r in range(5)]),
        ("single_row_line", [[9 if r == 2 and 1 <= c <= 3 else 0 for c in range(5)] for r in range(5)]),
        ("solid_rectangle", [[9 if r < 2 and c < 2 else 0 for c in range(5)] for r in range(5)]),
    ]
