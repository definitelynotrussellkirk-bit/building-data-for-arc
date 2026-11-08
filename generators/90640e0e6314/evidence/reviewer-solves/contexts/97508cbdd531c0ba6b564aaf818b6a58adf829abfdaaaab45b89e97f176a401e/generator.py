"""Generator for ARC task 833dafe3 / content hash 90640e0e6314.

The input is an asymmetric square bitmap.  The Racket oracle tiles it into a
2n x 2n kaleidoscope whose quadrants are, in reading order, rot180, flip-v,
flip-h, and identity.

Every fourth default sample is drawn from the strict public-example profile:
size 3, 4, or 8; exactly four colors; canonical foreground density; and high
row/column texture diversity.  The other samples broaden size, palette, and
texture while preserving four distinguishable transform branches.
"""
from __future__ import annotations

from collections import Counter
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.textures import (
    apply_bg_density,
    apply_noise_overlay,
    fill_texture,
)


GENERATOR_ID = "90640e0e6314"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"  # canonical-profile prior + honest axes + structural self-check
RULE_HASH = "370706e398d4"  # sha256[:12] of normalized canonical program_solution

SUMMARY = (
    "Given an asymmetric n x n color bitmap, output a 2n x 2n tiling with "
    "TL=180-degree rotation, TR=vertical flip, BL=horizontal flip, and "
    "BR=the original bitmap."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "input is a square ARC grid with side length 3..8",
    "at least three colors and five non-modal cells make the transform visible",
    "identity, vertical flip, horizontal flip, and 180-degree rotation are distinct",
    "the output oracle is the sole authority for the 2x2 transformed tiling",
]

CANONICAL_TEXTURE = "canonical_strokes"
GENERAL_TEXTURES = (
    "noise",
    "sparse",
    "blob",
    "stripes",
    "gradient",
    "checkerboard",
    "frame",
    "ring",
    "plus",
)
HELPFUL_TEXTURES = (CANONICAL_TEXTURE, *GENERAL_TEXTURES)

AXES = {
    "grid_n": {
        "type": "int",
        "default": "25% canonical sizes; otherwise difficulty-weighted 3..8",
        "valid": "3..8",
    },
    "palette_size": {
        "type": "int",
        "default": "25% canonical four colors; otherwise difficulty-weighted 3..7",
        "valid": "3..7",
    },
    "texture": {
        "type": "str",
        "default": "25% canonical_strokes; otherwise difficulty-weighted texture",
        "valid": "canonical_strokes|noise|sparse|blob|stripes|gradient|checkerboard|frame|ring|plus",
    },
    "bg_density": {
        "type": "float",
        "default": "difficulty-aware 0..0.55 on generalized samples",
        "valid": "0..0.7",
    },
    "noise_overlay": {
        "type": "float",
        "default": "difficulty-aware 0..0.12 on generalized samples",
        "valid": "0..0.2",
    },
}

_CANONICAL_FOREGROUND_CELLS = {3: 6, 4: 10, 8: 28}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return a deterministic, non-degenerate teaching input."""
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    canonical_prior = (
        sample_index % 4 == 0
        and not any(
            name in overrides
            for name in (
                "grid_n",
                "palette_size",
                "texture",
                "bg_density",
                "noise_overlay",
            )
        )
    )

    n = _draw_grid_n(ctx, difficulty, canonical_prior)
    palette_size = _draw_palette_size(ctx, difficulty, canonical_prior)
    texture = _draw_texture(ctx, difficulty, canonical_prior)
    bg_density = _draw_float_axis(
        ctx,
        "bg_density",
        0.0,
        0.7,
        0.0 if canonical_prior else _default_bg_density(ctx, difficulty),
    )
    noise_overlay = _draw_float_axis(
        ctx,
        "noise_overlay",
        0.0,
        0.2,
        0.0 if canonical_prior else _default_noise_overlay(ctx, difficulty),
    )

    palette = _draw_palette(ctx, palette_size, canonical_prior)
    rng = ctx.draw_rng("layout")

    for _ in range(256):
        if texture == CANONICAL_TEXTURE:
            grid = _canonical_strokes(n, palette, rng, strict=canonical_prior)
        else:
            grid = fill_texture(texture, n, n, palette, rng)

        if bg_density > 0.0:
            grid = apply_bg_density(grid, palette, rng, bg_density)
        if noise_overlay > 0.0:
            grid = apply_noise_overlay(grid, palette, rng, noise_overlay)

        _ensure_palette_coverage(grid, palette, rng)
        _break_transform_aliases(grid, palette, rng)
        _ensure_palette_coverage(grid, palette, rng)
        _break_transform_aliases(grid, palette, rng)

        if not self_check(
            grid,
            difficulty=difficulty,
            meta={"grid_n": n, "palette_size": palette_size},
        ):
            return [row[:] for row in grid]

    raise ValueError(
        "unable to construct a transform-distinguishing square bitmap after 256 attempts"
    )


def _draw_grid_n(ctx, difficulty, canonical_prior: bool) -> int:
    if "grid_n" in ctx.overrides:
        options = tuple(range(3, 9))
    elif canonical_prior:
        options = {
            "easy": (3, 3, 4, 4),
            "hard": (8, 8, 8, 8),
        }.get(difficulty, (3, 4, 4, 8))
    else:
        options = {
            "easy": (3, 3, 4, 4, 5, 6, 7, 8),
            "hard": (3, 4, 5, 6, 6, 7, 7, 8, 8, 8),
        }.get(difficulty, (3, 4, 4, 5, 5, 6, 7, 8))
    return int(ctx.draw_choice("grid_n", options))


def _draw_palette_size(ctx, difficulty, canonical_prior: bool) -> int:
    if "palette_size" in ctx.overrides:
        options = tuple(range(3, 8))
    elif canonical_prior:
        options = (4,)
    else:
        options = {
            "easy": (3, 3, 4, 4, 5, 6, 7),
            "hard": (3, 4, 5, 5, 6, 6, 7, 7),
        }.get(difficulty, (3, 4, 4, 5, 5, 6, 7))
    return int(ctx.draw_choice("palette_size", options))


def _draw_texture(ctx, difficulty, canonical_prior: bool) -> str:
    if "texture" in ctx.overrides:
        options = HELPFUL_TEXTURES
    elif canonical_prior:
        options = (CANONICAL_TEXTURE,)
    elif difficulty == "easy":
        options = (
            "sparse",
            "blob",
            "plus",
            "gradient",
            "noise",
            "stripes",
            "checkerboard",
            "frame",
            "ring",
            CANONICAL_TEXTURE,
        )
    elif difficulty == "hard":
        options = (
            "noise",
            "noise",
            "gradient",
            "stripes",
            "checkerboard",
            "frame",
            "ring",
            "plus",
            "blob",
            "sparse",
            CANONICAL_TEXTURE,
        )
    else:
        options = HELPFUL_TEXTURES
    return str(ctx.draw_choice("texture", options))


def _draw_palette(ctx, palette_size: int, canonical_prior: bool) -> list[int]:
    if canonical_prior:
        foreground = list(
            ctx.draw_distinct_colors(
                "foreground_palette", n=palette_size - 1, exclude={0}
            )
        )
        return [0, *foreground]
    background = int(ctx.draw_color("background"))
    foreground = list(
        ctx.draw_distinct_colors(
            "foreground_palette", n=palette_size - 1, exclude={background}
        )
    )
    return [background, *foreground]


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
    hi = {"easy": 0.28, "hard": 0.55}.get(difficulty, 0.42)
    return ctx.draw_rng("bg_density_value").uniform(0.0, hi)


def _default_noise_overlay(ctx, difficulty) -> float:
    hi = {"easy": 0.035, "hard": 0.12}.get(difficulty, 0.075)
    return ctx.draw_rng("noise_overlay_value").uniform(0.0, hi)


def _canonical_strokes(
    n: int, palette: list[int], rng, *, strict: bool = False
) -> list[list[int]]:
    """Draw a sparse multicolor bitmap; optionally match the public profile."""
    target_fg = _CANONICAL_FOREGROUND_CELLS.get(
        n, max(5, min(n * n - 1, round(n * n * 0.52)))
    )
    target_fg = max(target_fg, len(palette) - 1)
    target_fg = min(target_fg, n * n - 1)
    all_cells = [(r, c) for r in range(n) for c in range(n)]

    for _ in range(128):
        chosen = rng.sample(all_cells, target_fg)
        rng.shuffle(chosen)
        grid = full_grid(n, n, palette[0])
        foreground = palette[1:]
        for index, (r, c) in enumerate(chosen):
            grid[r][c] = foreground[index % len(foreground)]
        # Random recoloring creates runs and uneven swatches without changing
        # the exact foreground count or palette support.
        for r, c in chosen[len(foreground):]:
            if rng.random() < 0.55:
                neighbors = [
                    (rr, cc)
                    for rr, cc in (
                        (r - 1, c),
                        (r + 1, c),
                        (r, c - 1),
                        (r, c + 1),
                    )
                    if 0 <= rr < n and 0 <= cc < n and grid[rr][cc] != palette[0]
                ]
                if neighbors:
                    rr, cc = rng.choice(neighbors)
                    grid[r][c] = grid[rr][cc]
        _ensure_palette_coverage(grid, palette, rng, allowed_cells=chosen)
        quality_ok = (
            len(_variant_signatures(grid)) == 4
            and len({tuple(row) for row in grid}) >= n - 1
            and len({tuple(grid[r][c] for r in range(n)) for c in range(n)}) >= n - 1
            and len({value for row in grid for value in row}) == len(palette)
        )
        if quality_ok and (not strict or _strict_profile_shape(grid)):
            return grid

    raise ValueError(f"unable to draw canonical_strokes texture for n={n}")


def _ensure_palette_coverage(
    grid: list[list[int]],
    palette: list[int],
    rng,
    *,
    allowed_cells: list[tuple[int, int]] | None = None,
) -> None:
    cells = list(allowed_cells or [(r, c) for r in range(len(grid)) for c in range(len(grid[0]))])
    rng.shuffle(cells)
    present = Counter(value for row in grid for value in row)
    used_cells: set[tuple[int, int]] = set()
    for color in palette:
        if present[color] > 0:
            continue
        candidates = [cell for cell in cells if cell not in used_cells]
        if not candidates:
            raise ValueError("not enough cells to realize requested palette")
        r, c = candidates[0]
        old = grid[r][c]
        grid[r][c] = color
        present[old] -= 1
        present[color] += 1
        used_cells.add((r, c))


def _variant_signatures(grid: list[list[int]]) -> set[tuple[tuple[int, ...], ...]]:
    variants = (grid, _flip_v(grid), _flip_h(grid), _rot180(grid))
    return {tuple(tuple(row) for row in variant) for variant in variants}


def _break_transform_aliases(grid: list[list[int]], palette: list[int], rng) -> None:
    if len(_variant_signatures(grid)) == 4:
        return
    n = len(grid)
    orbits: list[list[tuple[int, int]]] = []
    for r in range(n):
        for c in range(n):
            orbit = sorted({
                (r, c),
                (n - 1 - r, c),
                (r, n - 1 - c),
                (n - 1 - r, n - 1 - c),
            })
            if len(orbit) == 4 and orbit not in orbits:
                orbits.append(orbit)
    rng.shuffle(orbits)
    for orbit in orbits:
        original = [grid[r][c] for r, c in orbit]
        for _ in range(32):
            values = [rng.choice(palette) for _ in orbit]
            if len(set(values)) < 3:
                continue
            for (r, c), value in zip(orbit, values):
                grid[r][c] = value
            if len(_variant_signatures(grid)) == 4:
                return
        for (r, c), value in zip(orbit, original):
            grid[r][c] = value
    raise ValueError("could not make all four quadrant transforms distinct")


def _flip_v(grid: list[list[int]]) -> list[list[int]]:
    return [row[:] for row in reversed(grid)]


def _flip_h(grid: list[list[int]]) -> list[list[int]]:
    return [list(reversed(row)) for row in grid]


def _rot180(grid: list[list[int]]) -> list[list[int]]:
    return _flip_v(_flip_h(grid))


def _strict_profile_shape(grid: list[list[int]]) -> bool:
    n = len(grid)
    counts = Counter(value for row in grid for value in row)
    modal_fraction = max(counts.values()) / (n * n)
    unique_rows = len({tuple(row) for row in grid})
    unique_cols = len({tuple(grid[r][c] for r in range(n)) for c in range(n)})
    return (
        n in _CANONICAL_FOREGROUND_CELLS
        and len(counts) == 4
        and 1 / 3 <= modal_fraction <= 9 / 16
        and unique_rows >= n - 1
        and unique_cols >= n - 1
        and len(_variant_signatures(grid)) == 4
    )


def observe_overrides(grid) -> dict[str, int]:
    """Recover the two exact semantic axes from a returned grid."""
    return {
        "grid_n": len(grid),
        "palette_size": len({value for row in grid for value in row}),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject low-information or branch-hiding lessons; accept canonical inputs."""
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

    n = len(grid)
    if n != width:
        errors.append(f"expected square input, got {n}x{width}")
    if not 3 <= n <= 8:
        errors.append(f"expected side length in [3,8], got {n}")

    counts = Counter(value for row in grid for value in row)
    if not 3 <= len(counts) <= 7:
        errors.append(f"expected 3..7 distinct colors, got {len(counts)}")
    if counts:
        non_modal = n * width - max(counts.values())
        if non_modal < 5:
            errors.append(
                f"expected at least five non-modal cells, got {non_modal}"
            )

    if n == width and len(_variant_signatures(grid)) < 4:
        errors.append(
            "identity/vertical/horizontal/180-degree variants must all differ"
        )

    requested: dict[str, Any] = {}
    if isinstance(meta, dict):
        requested.update(meta.get("overrides") or {})
        for key in ("grid_n", "palette_size"):
            if key in meta:
                requested[key] = meta[key]
    observed = observe_overrides(grid)
    for key in ("grid_n", "palette_size"):
        if key in requested and int(requested[key]) != observed[key]:
            errors.append(
                f"{key} requested {int(requested[key])}, observed {observed[key]}"
            )
    return errors
