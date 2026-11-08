"""Generator for ARC task 58c02a16 / content hash 87c05932431e.

The input stores one binary mask twice in the top-left corner:

* the ``mask_h x mask_w`` interior uses background/foreground colors;
* a separator-colored bottom row and right column delimit that interior.

The Racket rule uses the same binary mask at two scales.  A cell whose local
mask bit is zero stays background.  For a local one-bit, the corresponding
macro mask bit chooses foreground (macro one) or separator (macro zero).
"""
from __future__ import annotations

from functools import lru_cache
from itertools import product
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "87c05932431e"
TASK_ID = "87c05932431e"
VERSION = "2.0.0"
RULE_HASH = "4abe1e3192b7"

SUMMARY = (
    "A top-left binary mask is delimited by a separator-colored bottom row "
    "and right column. The output repeats the mask locally and uses that same "
    "mask as a macro pattern: local zeroes are background, local ones under "
    "macro one-bits are foreground, and local ones under macro zero-bits are "
    "separator-colored."
)

INVARIANTS = [
    "the grid is 7..18 rows by 7..18 columns and contains exactly three colors",
    "the unique modal color is the background",
    "a separator-colored L at row mask_h and column mask_w delimits the top-left mask",
    "the mask is 2..4 by 2..4, contains both foreground and background, and has at least two of each",
    "all cells outside the delimited top-left block are background",
    "the mask exposes both macro branches, so the oracle output contains background, foreground, and separator",
]

AXES = {
    "grid_h": {"type": "int", "default": "difficulty-linked schedule", "valid": "7..18"},
    "grid_w": {"type": "int", "default": "difficulty-linked schedule", "valid": "7..18"},
    "mask_h": {"type": "int", "default": "difficulty-linked schedule", "valid": "2..4"},
    "mask_w": {"type": "int", "default": "difficulty-linked schedule", "valid": "2..4"},
    "mask_variant": {"type": "int", "default": "sample_index schedule", "valid": "0..5"},
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

# Each band cycles all six profiles.  Easy has smaller masks/canvases, medium
# combines the canonical 9x9 and 12x8 scales with larger masks, and hard uses
# the canonical 16x16 scale plus 3x4/4x3/4x4 compositions.
_PROFILES = {
    "easy": (
        (7, 7, 2, 2, 0),
        (8, 9, 2, 3, 1),
        (9, 8, 3, 2, 2),
        (9, 9, 3, 3, 3),
        (8, 10, 2, 4, 4),
        (10, 8, 4, 2, 5),
    ),
    "medium": (
        (9, 9, 3, 3, 0),
        (12, 8, 3, 2, 1),
        (10, 13, 2, 3, 2),
        (13, 10, 3, 2, 3),
        (12, 12, 3, 4, 4),
        (11, 14, 4, 3, 5),
    ),
    "hard": (
        (16, 16, 3, 3, 0),
        (14, 17, 4, 3, 1),
        (17, 14, 3, 4, 2),
        (18, 18, 4, 4, 3),
        (15, 18, 4, 3, 4),
        (18, 15, 3, 4, 5),
    ),
}
SCHEDULE_PROFILES = tuple(range(6))


def schedule_profile(seed, sample_index, difficulty=None):
    del seed, difficulty
    return sample_index % len(SCHEDULE_PROFILES)


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> str:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown!r}")
    for key, value in overrides.items():
        if value is not None and type(value) is not int:
            raise ValueError(f"{key} must be an integer")
    return "medium" if difficulty is None else difficulty


def _draw_scheduled_int(ctx, overrides, label: str, lo: int, hi: int, default: int) -> int:
    if overrides.get(label) is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, default, default)


def _bits_to_mask(bits: tuple[int, ...], h: int, w: int) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(bits[r * w : (r + 1) * w]) for r in range(h))


def _catalog_candidate(bits: tuple[int, ...], h: int, w: int) -> bool:
    ones = sum(bits)
    n = h * w
    if not 2 <= ones <= n - 2:
        return False
    mask = _bits_to_mask(bits, h, w)
    # Both macro truth values must be reachable even on the 7x7 boundary case.
    corner = (mask[0][0], mask[0][1], mask[1][0], mask[1][1])
    if all(corner) or not any(corner):
        return False
    # Prevent a foreground-colored prefix-L inside the mask from being found
    # before the true separator by the canonical Racket search.
    for r in range(1, h):
        for c in range(1, w):
            if (
                all(mask[r][cc] == 1 for cc in range(c + 1))
                and all(mask[rr][c] == 1 for rr in range(r + 1))
            ):
                return False
    return True


@lru_cache(maxsize=None)
def _mask_catalog(h: int, w: int) -> tuple[tuple[tuple[int, ...], ...], ...]:
    """Six deterministic, spread-out lawful masks for every 2..4 shape.

    We make two tiny passes over at most 2**16 bit strings and retain only six
    masks.  Selecting evenly spaced lawful ranks gives each variant a distinct
    recoverable morphology without storing a large catalog.
    """
    lawful_count = 0
    for bits in product((0, 1), repeat=h * w):
        if _catalog_candidate(bits, h, w):
            lawful_count += 1
    if lawful_count < 6:
        raise AssertionError(f"only {lawful_count} lawful masks for {h}x{w}")
    ranks = tuple(round(i * (lawful_count - 1) / 5) for i in range(6))
    selected: list[tuple[tuple[int, ...], ...]] = []
    lawful_index = 0
    rank_set = set(ranks)
    for bits in product((0, 1), repeat=h * w):
        if not _catalog_candidate(bits, h, w):
            continue
        if lawful_index in rank_set:
            selected.append(_bits_to_mask(bits, h, w))
        lawful_index += 1
    if len(selected) != 6 or len(set(selected)) != 6:
        raise AssertionError(f"failed to build six distinct masks for {h}x{w}")
    return tuple(selected)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    band = _validate_call(difficulty, overrides)
    profile = _PROFILES[band][sample_index % len(_PROFILES[band])]
    default_h, default_w, default_mh, default_mw, default_variant = profile
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h = _draw_scheduled_int(ctx, overrides, "grid_h", 7, 18, default_h)
    w = _draw_scheduled_int(ctx, overrides, "grid_w", 7, 18, default_w)
    mh = _draw_scheduled_int(ctx, overrides, "mask_h", 2, 4, default_mh)
    mw = _draw_scheduled_int(ctx, overrides, "mask_w", 2, 4, default_mw)
    variant = _draw_scheduled_int(
        ctx, overrides, "mask_variant", 0, 5, default_variant
    )
    # Racket prelude `mode` ignores color 0, so the background must be nonzero.
    bg = ctx.draw_color("background_color", exclude={0})
    fg = ctx.draw_color("foreground_color", exclude={bg})
    sep = ctx.draw_color("separator_color", exclude={bg, fg})
    mask = _mask_catalog(mh, mw)[variant]

    grid = full_grid(h, w, bg)
    for r in range(mh):
        for c in range(mw):
            if mask[r][c]:
                grid[r][c] = fg
    for c in range(mw + 1):
        grid[mh][c] = sep
    for r in range(mh + 1):
        grid[r][mw] = sep

    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid two-level mask: " + "; ".join(errors))
    return grid


def _find_separator_candidates(grid, bg: int):
    h, w = len(grid), len(grid[0])
    candidates = []
    for r in range(1, h):
        for c in range(1, w):
            sep = grid[r][c]
            if sep == bg:
                continue
            if all(grid[r][cc] == sep for cc in range(c + 1)) and all(
                grid[rr][c] == sep for rr in range(r + 1)
            ):
                candidates.append((r, c, sep))
    return candidates


def _analyze(grid):
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return {"errors": ["grid must be a non-empty list of rows"]}
    h, w = len(grid), len(grid[0])
    if w == 0 or any(not isinstance(row, list) or len(row) != w for row in grid):
        return {"errors": ["grid rows must be non-empty and rectangular"]}
    if not 7 <= h <= 18:
        errors.append(f"grid height {h} outside 7..18")
    if not 7 <= w <= 18:
        errors.append(f"grid width {w} outside 7..18")

    flat = [value for row in grid for value in row]
    if any(type(value) is not int or not 0 <= value <= 9 for value in flat):
        errors.append("all cells must be integer ARC colors 0..9")
        return {"errors": errors}
    from collections import Counter

    counts = Counter(flat)
    if len(counts) != 3:
        errors.append(f"expected exactly three colors, got {len(counts)}")
    modes = [color for color, count in counts.items() if count == max(counts.values())]
    if len(modes) != 1:
        errors.append("background must be the unique modal color")
        bg = modes[0]
    else:
        bg = modes[0]
    if bg == 0:
        errors.append("background cannot be color 0 because the canonical Racket mode ignores 0")

    candidates = _find_separator_candidates(grid, bg)
    if len(candidates) != 1:
        errors.append(f"expected one separator corner, got {len(candidates)}")
        return {
            "errors": errors,
            "grid_h": h,
            "grid_w": w,
            "background": bg,
            "separator_candidates": candidates,
        }
    mh, mw, sep = candidates[0]
    if not 2 <= mh <= 4:
        errors.append(f"mask height {mh} outside 2..4")
    if not 2 <= mw <= 4:
        errors.append(f"mask width {mw} outside 2..4")

    expected_sep = {(mh, c) for c in range(mw + 1)} | {
        (r, mw) for r in range(mh + 1)
    }
    actual_sep = {
        (r, c) for r in range(h) for c in range(w) if grid[r][c] == sep
    }
    if actual_sep != expected_sep:
        errors.append("separator color must occur only on the delimiting bottom row/right column")

    outside_bad = [
        (r, c)
        for r in range(h)
        for c in range(w)
        if (r > mh or c > mw) and grid[r][c] != bg
    ]
    if outside_bad:
        errors.append("all cells outside the delimited top-left block must be background")

    mask_values = [grid[r][c] for r in range(mh) for c in range(mw)]
    fg_colors = set(mask_values) - {bg}
    if len(fg_colors) != 1:
        errors.append(f"mask must use exactly one foreground color, got {len(fg_colors)}")
        fg = next(iter(fg_colors), sep)
    else:
        fg = next(iter(fg_colors))
    if fg == sep:
        errors.append("foreground and separator colors must differ")
    bits = tuple(1 if value == fg else 0 for value in mask_values)
    ones = sum(bits)
    n = mh * mw
    if not 2 <= ones <= n - 2:
        errors.append(f"mask must contain at least two foreground and two background cells, got {ones}/{n}")
    if mh >= 2 and mw >= 2:
        corner = (bits[0], bits[1], bits[mw], bits[mw + 1])
        if all(corner) or not any(corner):
            errors.append("top-left 2x2 must expose both macro truth values")
    mask = _bits_to_mask(bits, mh, mw)
    variant = None
    try:
        variant = _mask_catalog(mh, mw).index(mask)
    except (ValueError, AssertionError):
        pass

    return {
        "errors": errors,
        "grid_h": h,
        "grid_w": w,
        "background": bg,
        "foreground": fg,
        "separator": sep,
        "mask_h": mh,
        "mask_w": mw,
        "mask": mask,
        "mask_cells": ones,
        "mask_variant": variant,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    return list(_analyze(grid)["errors"])


def observe_overrides(grid):
    analysis = _analyze(grid)
    if analysis["errors"] or analysis.get("mask_variant") is None:
        return {}
    return {
        "grid_h": analysis["grid_h"],
        "grid_w": analysis["grid_w"],
        "mask_h": analysis["mask_h"],
        "mask_w": analysis["mask_w"],
        "mask_variant": analysis["mask_variant"],
    }


def semantic_observables(grid) -> dict[str, object]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        return {"errors": list(analysis["errors"])}
    n = analysis["mask_h"] * analysis["mask_w"]
    return {
        **observe_overrides(grid),
        "mask_cells": analysis["mask_cells"],
        "mask_background_cells": n - analysis["mask_cells"],
        "square_mask": analysis["mask_h"] == analysis["mask_w"],
        "rectangular_mask": analysis["mask_h"] != analysis["mask_w"],
        "non_square_canvas": analysis["grid_h"] != analysis["grid_w"],
        "top_left_foreground": bool(analysis["mask"][0][0]),
        "mask_larger_than_2x2": analysis["mask_h"] > 2 or analysis["mask_w"] > 2,
        "sparse_mask": analysis["mask_cells"] <= max(2, n // 3),
        "dense_mask": analysis["mask_cells"] >= n - max(2, n // 3),
    }


def strict_canonical_like(grid) -> list[str]:
    # The generated grammar is exactly the canonical cue grammar, with only
    # bounded extensions from 2x2/3x2/3x3 masks to 4-cell mask dimensions.
    return self_check(grid)


def _witness(grid, predicate: Callable[[dict[str, object]], bool]) -> bool:
    obs = semantic_observables(grid)
    return not obs.get("errors") and bool(predicate(obs))


SEMANTIC_WITNESSES = {
    "macro_modulation_visible": lambda grid: _witness(
        grid, lambda obs: obs["mask_cells"] >= 2 and obs["mask_background_cells"] >= 2
    ),
    "square_mask": lambda grid: _witness(grid, lambda obs: obs["square_mask"]),
    "rectangular_mask": lambda grid: _witness(grid, lambda obs: obs["rectangular_mask"]),
    "non_square_canvas": lambda grid: _witness(grid, lambda obs: obs["non_square_canvas"]),
    "top_left_foreground": lambda grid: _witness(grid, lambda obs: obs["top_left_foreground"]),
    "top_left_background": lambda grid: _witness(grid, lambda obs: not obs["top_left_foreground"]),
    "mask_larger_than_2x2": lambda grid: _witness(
        grid, lambda obs: obs["mask_larger_than_2x2"]
    ),
    "sparse_mask": lambda grid: _witness(grid, lambda obs: obs["sparse_mask"]),
    "dense_mask": lambda grid: _witness(grid, lambda obs: obs["dense_mask"]),
}


def rule_mirror(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    h, w = analysis["grid_h"], analysis["grid_w"]
    mh, mw = analysis["mask_h"], analysis["mask_w"]
    bg, fg, sep = analysis["background"], analysis["foreground"], analysis["separator"]
    mask = analysis["mask"]
    out = full_grid(h, w, bg)
    for r in range(h):
        for c in range(w):
            local = mask[r % mh][c % mw]
            if not local:
                continue
            macro = mask[(r // mh) % mh][(c // mw) % mw]
            out[r][c] = fg if macro else sep
    return out


def _local_repeat(grid):
    a = _analyze(grid)
    if a["errors"]:
        return None
    out = full_grid(a["grid_h"], a["grid_w"], a["background"])
    for r in range(a["grid_h"]):
        for c in range(a["grid_w"]):
            if a["mask"][r % a["mask_h"]][c % a["mask_w"]]:
                out[r][c] = a["foreground"]
    return out


def _binary_no_separator(grid):
    a = _analyze(grid)
    if a["errors"]:
        return None
    out = full_grid(a["grid_h"], a["grid_w"], a["background"])
    for r in range(a["grid_h"]):
        for c in range(a["grid_w"]):
            local = a["mask"][r % a["mask_h"]][c % a["mask_w"]]
            macro = a["mask"][(r // a["mask_h"]) % a["mask_h"]][
                (c // a["mask_w"]) % a["mask_w"]
            ]
            if local and macro:
                out[r][c] = a["foreground"]
    return out


def _swap_macro_colors(grid):
    a = _analyze(grid)
    if a["errors"]:
        return None
    out = full_grid(a["grid_h"], a["grid_w"], a["background"])
    for r in range(a["grid_h"]):
        for c in range(a["grid_w"]):
            local = a["mask"][r % a["mask_h"]][c % a["mask_w"]]
            if not local:
                continue
            macro = a["mask"][(r // a["mask_h"]) % a["mask_h"]][
                (c // a["mask_w"]) % a["mask_w"]
            ]
            out[r][c] = a["separator"] if macro else a["foreground"]
    return out


def _fixed_2x2(grid):
    a = _analyze(grid)
    if a["errors"]:
        return None
    mh = mw = 2
    mask = tuple(tuple(a["mask"][r][c] for c in range(2)) for r in range(2))
    out = full_grid(a["grid_h"], a["grid_w"], a["background"])
    for r in range(a["grid_h"]):
        for c in range(a["grid_w"]):
            local = mask[r % mh][c % mw]
            if not local:
                continue
            macro = mask[(r // mh) % mh][(c // mw) % mw]
            out[r][c] = a["foreground"] if macro else a["separator"]
    return out


SEMANTIC_RIVALS = {
    "local_repeat": _local_repeat,
    "binary_no_separator": _binary_no_separator,
    "swap_macro_colors": _swap_macro_colors,
    "fixed_2x2": _fixed_2x2,
}
WITNESS_RIVALS = {
    "macro_modulation_visible": [
        "local_repeat",
        "binary_no_separator",
        "swap_macro_colors",
    ],
    "square_mask": ["local_repeat"],
    "rectangular_mask": ["local_repeat"],
    "non_square_canvas": ["local_repeat"],
    "top_left_foreground": ["local_repeat"],
    "top_left_background": ["local_repeat"],
    "mask_larger_than_2x2": ["fixed_2x2"],
    "sparse_mask": ["local_repeat"],
    "dense_mask": ["local_repeat"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    query_input = query.get("input") if isinstance(query, dict) else None
    if self_check(query_input):
        return ["query input is not a lawful two-level mask scene"]
    for index, demo in enumerate(demos):
        demo_input = demo.get("input") if isinstance(demo, dict) else None
        if self_check(demo_input):
            reasons.append(f"demo {index} input is not a lawful two-level mask scene")
        elif demo.get("output") != rule_mirror(demo_input):
            reasons.append(f"demo {index} output disagrees with the two-level mask rule")
    if reasons:
        return reasons

    query_truth = rule_mirror(query_input)
    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(demo["input"]) == demo["output"] for demo in demos):
            if competitor(query_input) != query_truth:
                reasons.append(
                    f"demos remain compatible with competitor {name!r}, which changes the query answer"
                )
    return reasons
