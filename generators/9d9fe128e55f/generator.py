"""Generator for 9d9fe128e55f — rank-fill color-8 components from a legend.

The authoritative Racket rule splits at the full-height color-9 separator,
reads the non-zero cells in the first column of the right panel from top to
bottom, sorts the left panel's 4-connected color-8 components by increasing
size, and paints those components with the legend colors in that order.  The
output is a new, background-zero grid having exactly the left panel's shape.

The schedule deliberately varies component count, absolute sizes, reading
order, legend order, right-panel padding, and a separated non-8 distractor.
Those variations refute the canonical-only shortcuts "sizes are always 2/3/4",
"there are always three components", and "recolor every non-zero object".
"""
from __future__ import annotations

from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "9d9fe128e55f"
TASK_ID = GENERATOR_ID
VERSION = "3.0.1"
RULE_HASH = "0e2a46f39d85"

SUMMARY = (
    "Split at the full color-9 column. Read the right panel's first-column "
    "legend top-to-bottom. Repaint the left panel's distinct-size color-8 "
    "components from smallest to largest with that ordered legend, and output "
    "only the recolored left panel."
)

INVARIANTS = [
    "exactly one full-height color-9 column separates the panels",
    "the left panel has three or four 4-connected color-8 components with distinct sizes",
    "the right panel has one legend color per color-8 component, contiguously from row 0",
    "all right-panel cells outside its first column are background 0",
    "an optional differently colored singleton is cardinally separated and is dropped by the rule",
]

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, Any], ...] = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled canonical-weighted 8..14",
        "valid": "8..18",
    },
    "left_w": {
        "type": "int",
        "default": "scheduled canonical-weighted 8..12",
        "valid": "7..16",
    },
    "right_w": {
        "type": "int",
        "default": "scheduled canonical-weighted 1..3",
        "valid": "1..3",
    },
    "n_blobs": {
        "type": "int",
        "default": "scheduled 3|3|4|3",
        "valid": "3..4",
    },
    "palette_order": {
        "type": "str",
        "default": "scheduled",
        "valid": "ascending|descending|mixed",
    },
    "distractor": {
        "type": "bool",
        "default": "scheduled false|false|false|true",
        "valid": "true|false",
    },
}

_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_PALETTE_COLORS = tuple(range(1, 9))

_PROFILES = (
    {
        "name": "canonical_three",
        "h": 8,
        "left_w": 8,
        "right_w": 1,
        "n_blobs": 3,
        "palette_order": "ascending",
        "distractor": False,
        "size_mode": "canonical",
    },
    {
        "name": "rank_swap_three",
        "h": 10,
        "left_w": 9,
        "right_w": 2,
        "n_blobs": 3,
        "palette_order": "descending",
        "distractor": False,
        "size_mode": "gapped_descending",
    },
    {
        "name": "four_components",
        "h": 12,
        "left_w": 11,
        "right_w": 3,
        "n_blobs": 4,
        "palette_order": "mixed",
        "distractor": False,
        "size_mode": "gapped_alternating",
    },
    {
        "name": "color_specific_distractor",
        "h": 11,
        "left_w": 10,
        "right_w": 1,
        "n_blobs": 3,
        "palette_order": "mixed",
        "distractor": True,
        "size_mode": "gapped_alternating",
    },
)
SCHEDULE_PROFILES = tuple(profile["name"] for profile in _PROFILES)


def schedule_profile(seed, sample_index, difficulty=None):
    """Return the deterministic semantic profile used by the shared census."""
    del seed
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    return _PROFILES[int(sample_index) % len(_PROFILES)]["name"]


def _profile_for(sample_index: int) -> dict[str, Any]:
    return _PROFILES[int(sample_index) % len(_PROFILES)]


def _draw_profile_int(ctx, overrides, label: str, default: int, lo: int, hi: int) -> int:
    """Keep scheduled defaults while accepting every declared exact boundary."""
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, default, default)


def _draw_profile_choice(ctx, overrides, label: str, default: Any, options: tuple[Any, ...]):
    if label in overrides and overrides[label] is not None:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, (default,))


def _components(grid, color: int) -> list[list[tuple[int, int]]]:
    """Return 4-connected components of one color in reading order."""
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    out: list[list[tuple[int, int]]] = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != color or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells: list[tuple[int, int]] = []
            while stack:
                cr, cc = stack.pop()
                cells.append((cr, cc))
                for dr, dc in _CARDINAL:
                    nr, nc = cr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            out.append(sorted(cells))
    return out


def _split(grid) -> tuple[int, list[list[int]], list[list[int]]] | None:
    if not grid or not grid[0]:
        return None
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return None
    dividers = [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]
    if len(dividers) != 1:
        return None
    divider = dividers[0]
    if divider == 0 or divider == w - 1:
        return None
    left = [row[:divider] for row in grid]
    right = [row[divider + 1 :] for row in grid]
    return divider, left, right


def _legend(right: list[list[int]]) -> tuple[list[int], list[str]]:
    errors: list[str] = []
    if not right or not right[0]:
        return [], ["empty right panel"]
    h, w = len(right), len(right[0])
    if any(len(row) != w for row in right):
        return [], ["ragged right panel"]
    if any(right[r][c] != 0 for r in range(h) for c in range(1, w)):
        errors.append("right-panel padding outside the first column is non-zero")
    values = [right[r][0] for r in range(h)]
    count = 0
    while count < h and values[count] != 0:
        count += 1
    if any(value != 0 for value in values[count:]):
        errors.append("legend colors are not contiguous from row 0")
    palette = values[:count]
    if any(value in (0, 9) for value in palette):
        errors.append("legend contains background or separator color")
    if len(set(palette)) != len(palette):
        errors.append("legend colors are not distinct")
    return palette, errors


def _analysis(grid) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return {"errors": ["empty grid"]}
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, list) or len(row) != w for row in grid):
        return {"errors": ["ragged grid"]}
    if any(
        not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("grid contains a non-integer or out-of-range color")

    split = _split(grid)
    if split is None:
        errors.append("expected exactly one interior full-height color-9 separator")
        return {"errors": errors, "height": h, "width": w}
    divider, left, right = split
    right_w = len(right[0])
    if not (8 <= h <= 18):
        errors.append(f"grid_h={h} outside 8..18")
    if not (7 <= divider <= 16):
        errors.append(f"left_w={divider} outside 7..16")
    if not (1 <= right_w <= 3):
        errors.append(f"right_w={right_w} outside 1..3")
    if any(value == 9 for row in left for value in row):
        errors.append("left panel contains separator color 9")

    palette, legend_errors = _legend(right)
    errors.extend(legend_errors)
    components = _components(left, 8)
    sizes = [len(cells) for cells in components]
    if not (3 <= len(components) <= 4):
        errors.append(f"expected 3-4 color-8 components, got {len(components)}")
    if len(set(sizes)) != len(sizes):
        errors.append(f"color-8 component sizes are not distinct: {sorted(sizes)}")
    if len(palette) != len(components):
        errors.append(
            f"legend/component count mismatch: legend={len(palette)} components={len(components)}"
        )

    foreign_cells = [
        (r, c, left[r][c])
        for r in range(h)
        for c in range(divider)
        if left[r][c] not in (0, 8)
    ]
    foreign_components: list[dict[str, Any]] = []
    for color in sorted({value for _, _, value in foreign_cells}):
        for cells in _components(left, color):
            foreign_components.append({"color": color, "cells": cells})
    if len(foreign_components) > 1:
        errors.append(f"expected at most one foreign distractor component, got {len(foreign_components)}")
    if foreign_components and len(foreign_components[0]["cells"]) != 1:
        errors.append("foreign distractor must be a singleton")

    owners: dict[tuple[int, int], tuple[str, int]] = {}
    for index, cells in enumerate(components):
        for cell in cells:
            owners[cell] = ("target", index)
    for index, component in enumerate(foreign_components):
        for cell in component["cells"]:
            owners[cell] = ("foreign", index)
    touching: list[tuple[tuple[int, int], tuple[int, int]]] = []
    for (r, c), owner in owners.items():
        for dr, dc in _CARDINAL:
            neighbor = (r + dr, c + dc)
            other = owners.get(neighbor)
            if other is not None and other != owner:
                touching.append(((r, c), neighbor))
    if touching:
        errors.append(f"distinct left-panel objects touch cardinally: {touching[:3]}")

    if palette == sorted(palette):
        palette_order = "ascending"
    elif palette == sorted(palette, reverse=True):
        palette_order = "descending"
    else:
        palette_order = "mixed"

    return {
        "errors": errors,
        "height": h,
        "width": w,
        "divider": divider,
        "left": left,
        "right": right,
        "right_w": right_w,
        "palette": palette,
        "palette_order": palette_order,
        "components": components,
        "sizes": sizes,
        "foreign_components": foreign_components,
        "distractor": bool(foreign_components),
    }


def _size_sequence(n_blobs: int, mode: str) -> list[int]:
    if mode == "canonical":
        base = list(range(2, n_blobs + 2))
        return base[:1] + base[:0:-1]
    gapped = [1, 3, 5, 7][:n_blobs]
    if mode == "gapped_descending":
        return list(reversed(gapped))
    # Large, small, next-large, next-small: reading order is not size order.
    out: list[int] = []
    lo, hi = 0, len(gapped) - 1
    while lo <= hi:
        out.append(gapped[hi])
        hi -= 1
        if lo <= hi:
            out.append(gapped[lo])
            lo += 1
    return out


def _two_row_shape(size: int, flip: bool) -> list[tuple[int, int]]:
    """A connected, normalized <=2-row polyomino of exactly ``size`` cells."""
    if size <= 2:
        return [(0, c) for c in range(size)]
    top = (size + 1) // 2
    bottom = size - top
    cells = [(0, c) for c in range(top)] + [(1, c) for c in range(bottom)]
    if flip:
        width = max(c for _, c in cells) + 1
        cells = [(r, width - 1 - c) for r, c in cells]
    min_c = min(c for _, c in cells)
    return sorted((r, c - min_c) for r, c in cells)


def _place_targets(grid: list[list[int]], sizes: list[int], rng) -> None:
    """Place exact-size targets with a guaranteed compact fallback geometry."""
    h, w = len(grid), len(grid[0])
    n = len(sizes)
    rich = h >= 3 * n and w >= 4
    if rich:
        starts = [3 * index for index in range(n)]
        shapes = [_two_row_shape(size, bool(rng.randrange(2))) for size in sizes]
    else:
        starts = [2 * index for index in range(n)]
        shapes = [[(0, c) for c in range(size)] for size in sizes]
    if starts[-1] + max(r for r, _ in shapes[-1]) >= h:
        raise ValueError("target placement rows do not fit")
    for index, (row0, shape) in enumerate(zip(starts, shapes)):
        width = max(c for _, c in shape) + 1
        if width > w:
            raise ValueError(f"component size {sizes[index]} does not fit left_w={w}")
        max_col = w - width
        col0 = rng.randint(0, max_col) if max_col else 0
        if index % 2:
            col0 = max_col - col0
        for dr, dc in shape:
            grid[row0 + dr][col0 + dc] = 8


def _place_distractor(left: list[list[int]], rng) -> None:
    h, w = len(left), len(left[0])
    candidates = []
    for r in range(h):
        for c in range(w):
            if left[r][c] != 0:
                continue
            if any(
                0 <= r + dr < h
                and 0 <= c + dc < w
                and left[r + dr][c + dc] != 0
                for dr, dc in _CARDINAL
            ):
                continue
            candidates.append((r, c))
    if not candidates:
        raise ValueError("no cardinally separated cell available for distractor")
    r, c = candidates[rng.randrange(len(candidates))]
    left[r][c] = 5


def _ordered_palette(rng, n: int, order: str) -> list[int]:
    colors = sorted(rng.sample(list(_PALETTE_COLORS), n))
    if order == "ascending":
        return colors
    if order == "descending":
        return list(reversed(colors))
    if order == "mixed":
        return colors[1:] + colors[:1]
    raise ValueError(f"unknown palette_order: {order!r}")


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    return nested if isinstance(nested, dict) else meta


def observe_overrides(grid) -> dict[str, int | str | bool]:
    """Recover every exact declared axis from a lawful returned grid."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        return {}
    return {
        "grid_h": analysis["height"],
        "left_w": analysis["divider"],
        "right_w": analysis["right_w"],
        "n_blobs": len(analysis["components"]),
        "palette_order": analysis["palette_order"],
        "distractor": analysis["distractor"],
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed, ambiguous, shortcut-hiding, or off-contract scenes."""
    del difficulty
    analysis = _analysis(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    observed = observe_overrides(grid)
    for name, requested in _meta_overrides(meta).items():
        if name in AXES and observed.get(name) != requested:
            errors.append(
                f"override {name}={requested!r} realized as {observed.get(name)!r}"
            )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """The strict generated grammar includes every official canonical input."""
    return self_check(grid)


def rule_mirror(grid) -> list[list[int]]:
    """Independent Python mirror; canonical Racket remains the authority."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid grid: " + "; ".join(analysis["errors"]))
    out = full_grid(analysis["height"], analysis["divider"], 0)
    ranked = sorted(analysis["components"], key=len)
    for cells, color in zip(ranked, analysis["palette"]):
        for r, c in cells:
            out[r][c] = color
    return out


def _paint_ranked(analysis: dict[str, Any], components, palette) -> list[list[int]]:
    out = full_grid(analysis["height"], analysis["divider"], 0)
    for cells, color in zip(components, palette):
        for r, c in cells:
            out[r][c] = color
    return out


def _rival_identity_crop(grid):
    analysis = _analysis(grid)
    return [row[:] for row in analysis["left"]]


def _rival_reading_order(grid):
    analysis = _analysis(grid)
    components = sorted(analysis["components"], key=lambda cells: min(cells))
    return _paint_ranked(analysis, components, analysis["palette"])


def _rival_numeric_palette(grid):
    analysis = _analysis(grid)
    components = sorted(analysis["components"], key=len)
    return _paint_ranked(analysis, components, sorted(analysis["palette"]))


def _rival_fixed_size_buckets(grid):
    """Canonical-only shortcut: size 2, size 3, and every larger size are fixed ranks."""
    analysis = _analysis(grid)
    out = full_grid(analysis["height"], analysis["divider"], 0)
    for cells in analysis["components"]:
        size = len(cells)
        slot = 0 if size == 2 else 1 if size == 3 else 2
        if slot < len(analysis["palette"]):
            for r, c in cells:
                out[r][c] = analysis["palette"][slot]
    return out


def _rival_first_three_only(grid):
    analysis = _analysis(grid)
    components = sorted(analysis["components"], key=len)[:3]
    return _paint_ranked(analysis, components, analysis["palette"][:3])


def _rival_all_nonzero_components(grid):
    analysis = _analysis(grid)
    components = list(analysis["components"])
    components.extend(component["cells"] for component in analysis["foreign_components"])
    components.sort(key=len)
    return _paint_ranked(analysis, components, analysis["palette"])


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "identity_crop": _rival_identity_crop,
    "reading_order": _rival_reading_order,
    "numeric_palette": _rival_numeric_palette,
    "fixed_size_buckets": _rival_fixed_size_buckets,
    "first_three_only": _rival_first_three_only,
    "all_nonzero_components": _rival_all_nonzero_components,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = {
    "fixed_size_buckets": _rival_fixed_size_buckets,
    "first_three_only": _rival_first_three_only,
    "all_nonzero_components": _rival_all_nonzero_components,
}


def _lawful(grid) -> dict[str, Any] | None:
    analysis = _analysis(grid)
    return analysis if not analysis["errors"] else None


def _witness_source_recolored(grid) -> bool:
    analysis = _lawful(grid)
    return bool(analysis and rule_mirror(grid) != analysis["left"])


def _witness_rank_not_reading(grid) -> bool:
    analysis = _lawful(grid)
    if not analysis:
        return False
    reading = [len(cells) for cells in sorted(analysis["components"], key=lambda cells: min(cells))]
    return reading != sorted(reading)


def _witness_descending_palette(grid) -> bool:
    analysis = _lawful(grid)
    return bool(analysis and analysis["palette_order"] == "descending")


def _witness_noncanonical_sizes(grid) -> bool:
    analysis = _lawful(grid)
    return bool(analysis and sorted(analysis["sizes"]) != [2, 3, 4])


def _witness_four_components(grid) -> bool:
    analysis = _lawful(grid)
    return bool(analysis and len(analysis["components"]) == 4)


def _witness_distractor(grid) -> bool:
    analysis = _lawful(grid)
    return bool(analysis and analysis["distractor"])


SEMANTIC_WITNESSES = {
    "source_recolored_and_panel_cropped": _witness_source_recolored,
    "size_rank_differs_from_reading_order": _witness_rank_not_reading,
    "legend_order_differs_from_numeric_order": _witness_descending_palette,
    "sizes_not_fixed_to_2_3_4": _witness_noncanonical_sizes,
    "component_count_can_be_four": _witness_four_components,
    "non_8_object_is_not_a_target": _witness_distractor,
}
WITNESS_RIVALS = {
    "source_recolored_and_panel_cropped": ["identity_crop"],
    "size_rank_differs_from_reading_order": ["reading_order"],
    "legend_order_differs_from_numeric_order": ["numeric_palette"],
    "sizes_not_fixed_to_2_3_4": ["fixed_size_buckets"],
    "component_count_can_be_four": ["first_three_only"],
    "non_8_object_is_not_a_target": ["all_nonzero_components"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require each materialized lesson to refute every named plausible rival."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]
    reasons: list[str] = []
    if self_check(query["input"]):
        reasons.append("query input is outside the teaching grammar")
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        errors = self_check(demo["input"])
        if errors:
            reasons.append(f"demo {index} input is outside the teaching grammar: {errors[0]}")
            continue
        expected = rule_mirror(demo["input"])
        if expected != demo["output"]:
            reasons.append(f"demo {index} output does not match the authoritative rule")
    if reasons:
        return reasons
    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(demo["input"]) == demo["output"] for demo in demos):
            reasons.append(f"competitor {name!r} survives every demonstration")
    return reasons


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic input grid; the canonical Racket owns output."""
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")

    profile = _profile_for(sample_index)
    # Difficulty changes keyed layout placement, not the semantic-scale schedule.
    # Keeping the same four scale profiles in every band guarantees that each
    # band retains canonical-size anchors instead of teaching hard=oversized.
    default_h = int(profile["h"])
    default_left_w = int(profile["left_w"])

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h = _draw_profile_int(ctx, overrides, "grid_h", default_h, 8, 18)
    left_w = _draw_profile_int(ctx, overrides, "left_w", default_left_w, 7, 16)
    right_w = _draw_profile_int(ctx, overrides, "right_w", int(profile["right_w"]), 1, 3)
    n_blobs = _draw_profile_int(ctx, overrides, "n_blobs", int(profile["n_blobs"]), 3, 4)
    palette_order = _draw_profile_choice(
        ctx,
        overrides,
        "palette_order",
        profile["palette_order"],
        ("ascending", "descending", "mixed"),
    )
    distractor = _draw_profile_choice(
        ctx, overrides, "distractor", bool(profile["distractor"]), (False, True)
    )

    layout_rng = ctx.draw_rng(f"layout:{difficulty or 'medium'}")
    palette_rng = ctx.draw_rng("palette")
    sizes = _size_sequence(n_blobs, profile["size_mode"])
    left = full_grid(h, left_w, 0)
    _place_targets(left, sizes, layout_rng)
    if distractor:
        _place_distractor(left, ctx.draw_rng("distractor_position"))
    palette = _ordered_palette(palette_rng, n_blobs, palette_order)

    grid = full_grid(h, left_w + 1 + right_w, 0)
    for r in range(h):
        grid[r][:left_w] = left[r]
        grid[r][left_w] = 9
    for index, color in enumerate(palette):
        grid[index][left_w + 1] = color

    errors = self_check(
        grid,
        difficulty=difficulty,
        meta={"overrides": {name: value for name, value in overrides.items()}},
    )
    if errors:
        raise ValueError("constructed invalid instance: " + "; ".join(errors))
    return [row[:] for row in grid]
