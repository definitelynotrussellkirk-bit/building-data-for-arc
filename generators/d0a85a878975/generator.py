"""Generator for ARC task d0a85a878975 (legacy id b1986d4b).

The input is a noisy field whose modal color is background.  Some non-background
4-connected components are solid monochrome squares, side length >= 2.  Each
square size has one color and may occur several times; every other component is
a distractor.  The output is a left-to-right tally made from top-left nested
square glyphs.  Sizes are exhausted in count layers.  When the smallest size
occurs more often than the runner-up, one smallest square is a size key rather
than a tally and its count is reduced by one.

The generator deliberately includes dense non-square distractors, variable
modal backgrounds, non-{2,3,4} size sets, and same-color singleton distractors.
Those branches refute the principal shortcuts while retaining four canonical
anchor profiles in every six sequential draws.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "d0a85a878975"
TASK_ID = GENERATOR_ID
RULE_HASH = "2b65c25d51af"
VERSION = "3.0.0"

SUMMARY = (
    "Ignore non-square distractors, count monochrome solid-square components by "
    "side length, conditionally remove one excess smallest square as the size "
    "key, then emit count-layered top-left nested-square tally glyphs."
)

INVARIANTS = [
    "the modal color is a strict-majority background and may be any ARC color",
    "lawful tally objects are monochrome solid 4-connected squares of side >= 2",
    "each square size has exactly one color and each square color has one size",
    "non-square components are distractors and do not contribute to the tally",
    "if the smallest raw count exceeds the runner-up count, exactly one smallest tally is removed",
    "glyphs contain all sizes still active in that count layer, smallest color on top",
]

EXAMPLES_NEEDED = 6
MIN_STRICT_FRAC = 0.60

AXES = {
    "grid_h": {
        "type": "int",
        "default": "six-profile schedule",
        "valid": "20..30",
    },
    "grid_w": {
        "type": "int",
        "default": "six-profile schedule",
        "valid": "20..30",
    },
    "n_sizes": {
        "type": "int",
        "default": "six-profile schedule",
        "valid": "2..4",
    },
    "size_start": {
        "type": "int",
        "default": "six-profile schedule",
        "valid": "2..3",
    },
    "smallest_drop": {
        "type": "bool",
        "default": "six-profile schedule",
        "valid": "true|false",
    },
    "noise_mode": {
        "type": "str",
        "default": "six-profile schedule",
        "valid": "distinct|same_color",
    },
}

# Every Cartesian combination of the public axes is intentionally realizable.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

_DIRS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_CANONICAL_DIMS = {(28, 28), (26, 25)}
_CANONICAL_COUNTS = {(5, 2, 2), (5, 4, 2), (3, 4, 6), (5, 6, 3)}
SCHEDULE_PROFILES = (0, 1, 2, 3, 4, 5)

# Four canonical anchors followed by two shortcut-refuting broadened profiles.
_PROFILES: dict[int, dict[str, Any]] = {
    0: {
        "dims": (28, 28), "n_sizes": 3, "size_start": 2,
        "smallest_drop": True, "noise_mode": "distinct",
        "counts": (5, 2, 2), "noise_cells": 58,
    },
    1: {
        "dims": (28, 28), "n_sizes": 3, "size_start": 2,
        "smallest_drop": True, "noise_mode": "distinct",
        "counts": (5, 4, 2), "noise_cells": 65,
    },
    2: {
        "dims": (28, 28), "n_sizes": 3, "size_start": 2,
        "smallest_drop": False, "noise_mode": "distinct",
        "counts": (3, 4, 6), "noise_cells": 50,
    },
    3: {
        "dims": (26, 25), "n_sizes": 3, "size_start": 2,
        "smallest_drop": False, "noise_mode": "distinct",
        "counts": (5, 6, 3), "noise_cells": 55,
    },
    4: {
        "dims": (25, 27), "n_sizes": 3, "size_start": 3,
        "smallest_drop": True, "noise_mode": "same_color",
        "counts": (2, 1, 2), "noise_cells": 44,
    },
    5: {
        "dims": (30, 24), "n_sizes": 4, "size_start": 2,
        "smallest_drop": False, "noise_mode": "same_color",
        "counts": (1, 2, 1, 2), "noise_cells": 38,
    },
}


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return str(difficulty)
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> int:
    del seed, difficulty
    return int(sample_index) % len(SCHEDULE_PROFILES)


def _validate_grid(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["rows must be nonempty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["cells must be ARC colors 0..9"]
    return []


def _modal_background(grid: Any) -> tuple[int | None, list[str]]:
    counts = Counter(value for row in grid for value in row)
    top = max(counts.values())
    winners = sorted(color for color, count in counts.items() if count == top)
    errors: list[str] = []
    if len(winners) != 1:
        errors.append(f"background mode must be unique, tied colors are {winners}")
        return None, errors
    bg = winners[0]
    total = sum(counts.values())
    if top * 2 <= total:
        errors.append("modal background must occupy a strict majority of the grid")
    return bg, errors


def _components(grid: Any, background: int) -> list[dict[str, Any]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[dict[str, Any]] = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == background or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells: list[tuple[int, int]] = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in _DIRS4:
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            cells.sort()
            r0 = min(rr for rr, _ in cells)
            r1 = max(rr for rr, _ in cells)
            c0 = min(cc for _, cc in cells)
            c1 = max(cc for _, cc in cells)
            bh, bw = r1 - r0 + 1, c1 - c0 + 1
            solid_square = bh == bw and bh >= 2 and len(cells) == bh * bw
            result.append({
                "color": color,
                "cells": tuple(cells),
                "size": len(cells),
                "bbox": (r0, c0, r1, c1),
                "bbox_h": bh,
                "bbox_w": bw,
                "solid_square": solid_square,
                "side": bh if solid_square else None,
            })
    result.sort(key=lambda item: item["cells"][0])
    return result


def _render_encoding(
    sizes: Iterable[int],
    counts: dict[int, int],
    color_by_size: dict[int, int],
    background: int,
) -> list[list[int]]:
    ordered = sorted(int(size) for size in sizes)
    pairs = [(size, int(counts.get(size, 0))) for size in ordered]
    pairs = [(size, count) for size, count in pairs if count > 0]
    if not pairs:
        raise ValueError("tally has no positive square counts")

    blocks: list[tuple[int, ...]] = []
    while pairs:
        layer_count = min(count for _, count in pairs)
        active = tuple(size for size, _ in pairs)
        blocks.extend([active] * layer_count)
        pairs = [
            (size, count - layer_count)
            for size, count in pairs
            if count - layer_count > 0
        ]

    out_h = max(ordered) + 1
    out_w = sum(max(block) + 1 for block in blocks)
    output = full_grid(out_h, out_w, background)
    col0 = 0
    for block in blocks:
        glyph_w = max(block) + 1
        for r in range(out_h):
            for c in range(glyph_w):
                cover = [size for size in block if size >= 1 + max(r, c)]
                if cover:
                    output[r][col0 + c] = color_by_size[min(cover)]
        col0 += glyph_w
    return output


def _scene_analysis(grid: Any, *, enforce_envelope: bool = True) -> dict[str, Any]:
    errors = _validate_grid(grid)
    if errors:
        return {"errors": errors}
    h, w = len(grid), len(grid[0])
    bg, mode_errors = _modal_background(grid)
    errors.extend(mode_errors)
    if bg is None:
        return {"errors": errors, "grid_h": h, "grid_w": w}

    comps = _components(grid, bg)
    squares = [item for item in comps if item["solid_square"]]
    noise = [item for item in comps if not item["solid_square"]]
    sizes = sorted({int(item["side"]) for item in squares})
    colors_by_size: dict[int, set[int]] = defaultdict(set)
    sizes_by_color: dict[int, set[int]] = defaultdict(set)
    counts_by_size: Counter[int] = Counter()
    for item in squares:
        side = int(item["side"])
        color = int(item["color"])
        colors_by_size[side].add(color)
        sizes_by_color[color].add(side)
        counts_by_size[side] += 1

    if enforce_envelope and not (20 <= h <= 30 and 20 <= w <= 30):
        errors.append(f"input dimensions {h}x{w} outside declared 20..30 envelope")
    if len(sizes) < 2:
        errors.append(f"need at least two distinct solid-square sizes, found {sizes}")
    for size in sizes:
        colors = sorted(colors_by_size[size])
        if len(colors) != 1:
            errors.append(f"square size {size} must have exactly one color, found {colors}")
    for color, color_sizes in sorted(sizes_by_color.items()):
        if len(color_sizes) != 1:
            errors.append(
                f"square color {color} must encode exactly one size, found {sorted(color_sizes)}"
            )
    if not noise:
        errors.append("need at least one non-square distractor component")

    color_by_size = {
        size: next(iter(colors_by_size[size]))
        for size in sizes
        if len(colors_by_size[size]) == 1
    }
    raw_counts = {size: int(counts_by_size[size]) for size in sizes}
    adjusted_counts = dict(raw_counts)
    smallest_drop = False
    if len(sizes) >= 2 and raw_counts[sizes[0]] > raw_counts[sizes[1]]:
        adjusted_counts[sizes[0]] -= 1
        smallest_drop = True

    output = None
    output_error = None
    if len(color_by_size) == len(sizes) and sizes:
        try:
            output = _render_encoding(sizes, adjusted_counts, color_by_size, bg)
            if len(output) > 30 or len(output[0]) > 30:
                errors.append(
                    f"encoded output {len(output)}x{len(output[0])} exceeds ARC 30x30"
                )
        except Exception as exc:  # surfaced in errors; never silently accepted
            output_error = f"{type(exc).__name__}: {exc}"
            errors.append(f"cannot render encoded tally: {output_error}")

    square_colors = set(sizes_by_color)
    noise_colors = {int(item["color"]) for item in noise}
    shared_noise_colors = square_colors & noise_colors
    palette = {int(value) for row in grid for value in row}
    return {
        "errors": errors,
        "grid_h": h,
        "grid_w": w,
        "background": bg,
        "components": comps,
        "squares": squares,
        "noise": noise,
        "sizes": sizes,
        "n_sizes": len(sizes),
        "size_start": min(sizes) if sizes else None,
        "colors_by_size": {k: set(v) for k, v in colors_by_size.items()},
        "color_by_size": color_by_size,
        "sizes_by_color": {k: set(v) for k, v in sizes_by_color.items()},
        "raw_counts": raw_counts,
        "adjusted_counts": adjusted_counts,
        "smallest_drop": smallest_drop,
        "square_colors": square_colors,
        "noise_colors": noise_colors,
        "shared_noise_colors": shared_noise_colors,
        "noise_mode": "same_color" if shared_noise_colors else "distinct",
        "noise_cells": sum(item["size"] for item in noise),
        "noise_components": len(noise),
        "palette": palette,
        "palette_size": len(palette),
        "output": output,
        "output_error": output_error,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the teaching grammar while accepting every canonical input."""
    del difficulty, meta
    return list(_scene_analysis(grid)["errors"])


def expected_output(grid: Any) -> list[list[int]]:
    """Pure Python mirror for tests and rival audits; Racket remains authority."""
    analysis = _scene_analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid square-tally input: " + "; ".join(analysis["errors"]))
    return [list(row) for row in analysis["output"]]


def strict_canonical_like(grid) -> list[str]:
    """Recognize the two canonical profiles and their observed count families."""
    analysis = _scene_analysis(grid)
    reasons = list(analysis["errors"])
    if reasons:
        return reasons
    if (analysis["grid_h"], analysis["grid_w"]) not in _CANONICAL_DIMS:
        reasons.append("dimensions are not one of the canonical 28x28 or 26x25 profiles")
    if analysis["sizes"] != [2, 3, 4]:
        reasons.append(f"canonical square sizes are [2, 3, 4], found {analysis['sizes']}")
    counts = tuple(analysis["raw_counts"].get(size, 0) for size in (2, 3, 4))
    if counts not in _CANONICAL_COUNTS:
        reasons.append(f"square-count profile {counts} is not canonical")
    if analysis["palette_size"] != 5:
        reasons.append(f"canonical palette size is 5, found {analysis['palette_size']}")
    if analysis["shared_noise_colors"]:
        reasons.append("canonical distractor color is distinct from all square colors")
    if len(analysis["noise_colors"]) != 1:
        reasons.append(
            f"canonical input has one distractor color, found {sorted(analysis['noise_colors'])}"
        )
    if not (40 <= analysis["noise_components"] <= 80):
        reasons.append(
            f"canonical distractor-component envelope is 40..80, found {analysis['noise_components']}"
        )
    if not (40 <= analysis["noise_cells"] <= 80):
        reasons.append(
            f"canonical distractor-cell envelope is 40..80, found {analysis['noise_cells']}"
        )
    return reasons


def observe_overrides(grid) -> dict[str, Any]:
    """Recover every exact public axis from the returned grid."""
    analysis = _scene_analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {
        "grid_h": analysis["grid_h"],
        "grid_w": analysis["grid_w"],
        "n_sizes": analysis["n_sizes"],
        "size_start": analysis["size_start"],
        "smallest_drop": analysis["smallest_drop"],
        "noise_mode": analysis["noise_mode"],
    }


def _axis_int(ctx, label: str, default: int, lo: int, hi: int) -> int:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return int(ctx.draw_int(label, lo, hi))
    return int(ctx.draw_int(label, default, default))


def _axis_choice(ctx, label: str, default: Any, options: tuple[Any, ...]) -> Any:
    choices = options if label in ctx.overrides and ctx.overrides[label] is not None else (default,)
    return ctx.draw_choice(label, choices)


def _counts_for_axes(
    *,
    n_sizes: int,
    smallest_drop: bool,
    profile_counts: tuple[int, ...] | None,
) -> dict[int, int]:
    if profile_counts is not None and len(profile_counts) == n_sizes:
        values = list(profile_counts)
    elif smallest_drop:
        values = [2, 1] + [1] * (n_sizes - 2)
    else:
        values = [1, 2] + [1] * (n_sizes - 2)
    if smallest_drop and not values[0] > values[1]:
        raise AssertionError(f"drop profile is not observable: {values}")
    if not smallest_drop and values[0] > values[1]:
        raise AssertionError(f"non-drop profile is not observable: {values}")
    return {index: value for index, value in enumerate(values)}


def _square_color_order(colors: Iterable[int]) -> tuple[int, ...]:
    """A deterministic numeric-order decoy: mapping is never ascending."""
    ordered = sorted(int(color) for color in colors)
    if len(ordered) == 2:
        return tuple(reversed(ordered))
    if len(ordered) == 3:
        return (ordered[1], ordered[2], ordered[0])
    if len(ordered) == 4:
        return (ordered[3], ordered[0], ordered[2], ordered[1])
    raise ValueError(f"unsupported square-color count: {len(ordered)}")


def _cells_for_square(r0: int, c0: int, side: int) -> set[tuple[int, int]]:
    return {
        (r, c)
        for r in range(r0, r0 + side)
        for c in range(c0, c0 + side)
    }


def _orthogonal_halo(cells: Iterable[tuple[int, int]], h: int, w: int) -> set[tuple[int, int]]:
    halo = set(cells)
    for r, c in tuple(cells):
        for dr, dc in _DIRS4:
            nr, nc = r + dr, c + dc
            if 0 <= nr < h and 0 <= nc < w:
                halo.add((nr, nc))
    return halo


def _place_squares(
    *,
    h: int,
    w: int,
    sizes: list[int],
    color_by_size: dict[int, int],
    counts: dict[int, int],
    background: int,
    rng,
) -> tuple[list[list[int]], set[tuple[int, int]], dict[int, set[tuple[int, int]]]]:
    instances = [
        (size, color_by_size[size])
        for size in sorted(sizes, reverse=True)
        for _ in range(counts[size])
    ]
    all_positions = {
        size: [(r, c) for r in range(h - size + 1) for c in range(w - size + 1)]
        for size in sizes
    }

    for _restart in range(128):
        grid = full_grid(h, w, background)
        occupied: set[tuple[int, int]] = set()
        forbidden_by_color: dict[int, set[tuple[int, int]]] = defaultdict(set)
        color_cells: dict[int, set[tuple[int, int]]] = defaultdict(set)
        success = True
        # Keep large objects first but randomize within each equal-size group.
        candidates_instances = list(instances)
        start = 0
        while start < len(candidates_instances):
            end = start + 1
            while end < len(candidates_instances) and candidates_instances[end][0] == candidates_instances[start][0]:
                end += 1
            chunk = candidates_instances[start:end]
            rng.shuffle(chunk)
            candidates_instances[start:end] = chunk
            start = end

        for size, color in candidates_instances:
            positions = list(all_positions[size])
            rng.shuffle(positions)
            chosen = None
            for r0, c0 in positions:
                cells = _cells_for_square(r0, c0, size)
                if cells & occupied or cells & forbidden_by_color[color]:
                    continue
                chosen = cells
                break
            if chosen is None:
                success = False
                break
            for r, c in chosen:
                grid[r][c] = color
            occupied.update(chosen)
            color_cells[color].update(chosen)
            forbidden_by_color[color].update(_orthogonal_halo(chosen, h, w))
        if success:
            return grid, occupied, {k: set(v) for k, v in color_cells.items()}
    raise ValueError(
        f"could not place square multiset {[(s, counts[s]) for s in sizes]} in {h}x{w}"
    )


def _place_isolated_cells(
    *,
    grid: list[list[int]],
    color: int,
    count: int,
    occupied: set[tuple[int, int]],
    rng,
    avoid_color_cells: set[tuple[int, int]] | None = None,
    same_parity: bool = False,
) -> set[tuple[int, int]]:
    h, w = len(grid), len(grid[0])
    avoid = set(avoid_color_cells or ())
    chosen: set[tuple[int, int]] = set()

    if same_parity:
        by_parity: dict[int, list[tuple[int, int]]] = {0: [], 1: []}
        for r in range(h):
            for c in range(w):
                if (r, c) not in occupied:
                    by_parity[(r + c) % 2].append((r, c))
        parity = max((0, 1), key=lambda p: len(by_parity[p]))
        candidates = by_parity[parity]
    else:
        candidates = [
            (r, c)
            for r in range(h)
            for c in range(w)
            if (r, c) not in occupied
        ]
    rng.shuffle(candidates)

    for cell in candidates:
        if len(chosen) >= count:
            break
        r, c = cell
        if cell in occupied:
            continue
        # Same-color distractors must remain singleton 4-components and must
        # not attach to any lawful square of that color.
        if any((r + dr, c + dc) in (avoid | chosen) for dr, dc in _DIRS4):
            continue
        grid[r][c] = color
        occupied.add(cell)
        chosen.add(cell)
    if len(chosen) != count:
        raise ValueError(
            f"could place only {len(chosen)}/{count} isolated color-{color} distractors"
        )
    return chosen


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")

    band = _band(difficulty)
    profile_id = schedule_profile(seed, sample_index, band)
    profile = _PROFILES[profile_id]
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )

    h = _axis_int(ctx, "grid_h", int(profile["dims"][0]), 20, 30)
    w = _axis_int(ctx, "grid_w", int(profile["dims"][1]), 20, 30)
    n_sizes = _axis_int(ctx, "n_sizes", int(profile["n_sizes"]), 2, 4)
    size_start = _axis_int(ctx, "size_start", int(profile["size_start"]), 2, 3)
    smallest_drop = bool(
        _axis_choice(ctx, "smallest_drop", bool(profile["smallest_drop"]), (False, True))
    )
    noise_mode = str(
        _axis_choice(ctx, "noise_mode", str(profile["noise_mode"]), ("distinct", "same_color"))
    )

    sizes = list(range(size_start, size_start + n_sizes))
    profile_counts = None if overrides else tuple(int(v) for v in profile["counts"])
    indexed_counts = _counts_for_axes(
        n_sizes=n_sizes,
        smallest_drop=smallest_drop,
        profile_counts=profile_counts,
    )
    counts = {size: indexed_counts[index] for index, size in enumerate(sizes)}

    palette = ctx.draw_distinct_colors("palette", n=n_sizes + 2)
    background = int(palette[0])
    square_colors = _square_color_order(palette[1:-1])
    dedicated_noise_color = int(palette[-1])
    color_by_size = {size: square_colors[index] for index, size in enumerate(sizes)}

    rng = ctx.draw_rng("layout")
    grid, occupied, color_cells = _place_squares(
        h=h,
        w=w,
        sizes=sizes,
        color_by_size=color_by_size,
        counts=counts,
        background=background,
        rng=rng,
    )

    # Same-color mode adds exactly s^2 singleton cells in the smallest square's
    # color.  A raw-color-area shortcut therefore overcounts that size by one.
    if noise_mode == "same_color":
        smallest = sizes[0]
        shared_color = color_by_size[smallest]
        added = _place_isolated_cells(
            grid=grid,
            color=shared_color,
            count=smallest * smallest,
            occupied=occupied,
            rng=rng,
            avoid_color_cells=color_cells[shared_color],
            same_parity=False,
        )
        color_cells[shared_color].update(added)

    noise_target = int(profile["noise_cells"])
    if overrides:
        # Exact boundary combinations prioritize realizability while retaining
        # enough components to stay near the canonical object-count envelope.
        noise_target = 24 if band == "easy" else 32 if band == "medium" else 40
    else:
        noise_target += -4 if band == "easy" else 4 if band == "hard" else 0
    _place_isolated_cells(
        grid=grid,
        color=dedicated_noise_color,
        count=noise_target,
        occupied=occupied,
        rng=rng,
        same_parity=True,
    )

    errors = self_check(grid, difficulty=band)
    if errors:
        raise AssertionError("generated invalid square-tally lesson: " + "; ".join(errors))
    observed = observe_overrides(grid)
    requested = {
        "grid_h": h,
        "grid_w": w,
        "n_sizes": n_sizes,
        "size_start": size_start,
        "smallest_drop": smallest_drop,
        "noise_mode": noise_mode,
    }
    if observed != requested:
        raise AssertionError(f"axis observability mismatch: requested={requested}, observed={observed}")
    return grid


# ---------------------------------------------------------------------------
# Named wrong rules used by the semantic gate and lesson-level audit.
# ---------------------------------------------------------------------------


def _rival_output(
    grid: Any,
    *,
    drop_policy: str = "canonical",
    normalize_sizes: bool = False,
    numeric_colors: bool = False,
    raw_area_counts: bool = False,
    include_noise_size1: bool = False,
) -> list[list[int]]:
    analysis = _scene_analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid rival input: " + "; ".join(analysis["errors"]))
    actual_sizes = list(analysis["sizes"])
    sizes = list(range(2, 2 + len(actual_sizes))) if normalize_sizes else actual_sizes
    actual_to_render = dict(zip(actual_sizes, sizes))

    counts: dict[int, int] = {}
    for actual, rendered in zip(actual_sizes, sizes):
        count = analysis["raw_counts"][actual]
        if raw_area_counts:
            color = analysis["color_by_size"][actual]
            total_cells = sum(
                item["size"] for item in analysis["components"] if item["color"] == color
            )
            count = total_cells // (actual * actual)
        counts[rendered] = int(count)

    if drop_policy == "canonical":
        if len(sizes) >= 2 and counts[sizes[0]] > counts[sizes[1]]:
            counts[sizes[0]] -= 1
    elif drop_policy == "always":
        counts[sizes[0]] = max(0, counts[sizes[0]] - 1)
    elif drop_policy != "never":
        raise ValueError(f"unknown drop policy: {drop_policy}")

    actual_colors = [analysis["color_by_size"][size] for size in actual_sizes]
    render_colors = sorted(actual_colors) if numeric_colors else actual_colors
    color_by_size = {size: render_colors[index] for index, size in enumerate(sizes)}

    if include_noise_size1:
        noise_count = len(analysis["noise"])
        if noise_count:
            sizes = [1] + sizes
            counts[1] = noise_count
            # The wrong rule uses the first distractor color for the fake size-1 tally.
            color_by_size[1] = int(analysis["noise"][0]["color"])

    return _render_encoding(sizes, counts, color_by_size, analysis["background"])


def rival_never_drop_smallest(grid: Any) -> list[list[int]]:
    return _rival_output(grid, drop_policy="never")


def rival_always_drop_smallest(grid: Any) -> list[list[int]]:
    return _rival_output(grid, drop_policy="always")


def rival_normalize_sizes_234(grid: Any) -> list[list[int]]:
    return _rival_output(grid, normalize_sizes=True)


def rival_numeric_color_order(grid: Any) -> list[list[int]]:
    return _rival_output(grid, numeric_colors=True)


def rival_raw_color_area_counts(grid: Any) -> list[list[int]]:
    return _rival_output(grid, raw_area_counts=True)


def rival_include_noise_as_size1(grid: Any) -> list[list[int]]:
    return _rival_output(grid, include_noise_size1=True)


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "never_drop_smallest": rival_never_drop_smallest,
    "always_drop_smallest": rival_always_drop_smallest,
    "normalize_sizes_234": rival_normalize_sizes_234,
    "numeric_color_order": rival_numeric_color_order,
    "raw_color_area_counts": rival_raw_color_area_counts,
    "include_noise_as_size1": rival_include_noise_as_size1,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "normalize_sizes_234": rival_normalize_sizes_234,
    "raw_color_area_counts": rival_raw_color_area_counts,
}


def _valid_and_rival_differs(grid: Any, rival_name: str, predicate: Callable[[dict[str, Any]], bool]) -> bool:
    analysis = _scene_analysis(grid)
    if analysis["errors"] or not predicate(analysis):
        return False
    return SEMANTIC_RIVALS[rival_name](grid) != expected_output(grid)


SEMANTIC_WITNESSES = {
    "smallest_drop_active": lambda grid: _valid_and_rival_differs(
        grid, "never_drop_smallest", lambda a: bool(a["smallest_drop"])
    ),
    "smallest_drop_inactive": lambda grid: _valid_and_rival_differs(
        grid, "always_drop_smallest", lambda a: not a["smallest_drop"]
    ),
    "noncanonical_size_set": lambda grid: _valid_and_rival_differs(
        grid, "normalize_sizes_234", lambda a: a["sizes"] != [2, 3, 4]
    ),
    "numeric_color_decoy": lambda grid: _valid_and_rival_differs(
        grid,
        "numeric_color_order",
        lambda a: [a["color_by_size"][s] for s in a["sizes"]]
        != sorted(a["square_colors"]),
    ),
    "same_color_distractors": lambda grid: _valid_and_rival_differs(
        grid, "raw_color_area_counts", lambda a: bool(a["shared_noise_colors"])
    ),
    "non_square_distractors": lambda grid: _valid_and_rival_differs(
        grid, "include_noise_as_size1", lambda a: bool(a["noise"])
    ),
}

WITNESS_RIVALS = {
    "smallest_drop_active": ["never_drop_smallest"],
    "smallest_drop_inactive": ["always_drop_smallest"],
    "noncanonical_size_set": ["normalize_sizes_234"],
    "numeric_color_decoy": ["numeric_color_order"],
    "same_color_distractors": ["raw_color_area_counts"],
    "non_square_distractors": ["include_noise_as_size1"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require six sequential demos to refute every named plausible shortcut."""
    reasons: list[str] = []
    if len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]

    valid_demos: list[dict[str, Any]] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} is not an input/output pair")
            continue
        analysis = _scene_analysis(pair["input"])
        if analysis["errors"]:
            reasons.append(f"demo {index} input is outside teaching grammar")
            continue
        official = expected_output(pair["input"])
        if pair["output"] != official:
            reasons.append(f"demo {index} output is not the square-tally rule")
            continue
        valid_demos.append(pair)

    for name, competitor in LESSON_COMPETITORS.items():
        if valid_demos and all(competitor(pair["input"]) == pair["output"] for pair in valid_demos):
            reasons.append(f"competitor {name} survives every demonstration")

    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query is not an input/output pair")
    else:
        analysis = _scene_analysis(query["input"])
        if analysis["errors"]:
            reasons.append("query input is outside teaching grammar")
        elif "output" in query and query["output"] != expected_output(query["input"]):
            reasons.append("query output is not the square-tally rule")
    return reasons
