"""Generator for ARC task c181f41a09f0 (legacy slug d255d7a7).

The input is an orange (7) canvas containing two to four parallel, full-span,
three-cell-thick black strips.  Some strips carry a marker-colored cap in the
three-wide block at one common source end; at least one strip is deliberately
unmarked.  Marker-colored decoys outside the strips stay fixed.  The Racket
rule clears each strip and copies its source-end 3-wide block to the opposite
end, using the marked strips' common direction for unmarked strips.
"""
from __future__ import annotations

import itertools
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_rect, full_grid

GENERATOR_ID = "c181f41a09f0"
TASK_ID = "c181f41a09f0"
VERSION = "3.0.0"
RULE_HASH = "bd986c826aae"
EXAMPLES_NEEDED = 4

SUMMARY = (
    "On a literal orange-7 canvas, two to four parallel full-span black strips "
    "are exactly three cells thick. One to three strips carry a same-colored "
    "cap in the three-wide block at a common source end, while at least one "
    "strip is unmarked and inherits that direction. Clear every strip and copy "
    "its complete source-end 3-wide block to the opposite end. Same-colored "
    "markers outside all strips are stationary decoys."
)

INVARIANTS = [
    "the canvas is 8..20 by 8..20 with literal background color 7",
    "there are 2..4 parallel, full-span black strips, each exactly 3 cells thick",
    "strips are separated by at least one all-background row or column",
    "1..3 strips are marked at one common source side and at least one strip is unmarked",
    "all non-{0,7} cells share one marker color; 0..6 of them may be stationary decoys outside strips",
    "the output authority clears each strip then copies its source 3-wide block to the opposite end",
]

HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()

_MARKER_COLORS = (1, 2, 3, 4, 5, 6, 8, 9)
_ORIENTATIONS = ("horizontal", "vertical")
_SOURCE_SIDES = ("low", "high")
_CANONICAL_SIZES = (8, 14, 16, 20)
_PROFILE_PRIOR = {"easy": 0.35, "medium": 0.28, "hard": 0.20}

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical-size prior or difficulty-skewed",
        "valid": "8..20",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical-size prior or difficulty-skewed",
        "valid": "8..20",
    },
    "orientation": {
        "type": "str",
        "default": "four-sample branch schedule",
        "valid": "horizontal|vertical",
    },
    "source_side": {
        "type": "str",
        "default": "four-sample branch schedule",
        "valid": "low|high",
    },
    "strip_count": {
        "type": "int",
        "default": "difficulty/capacity aware",
        "valid": "2..4",
    },
    "marked_count": {
        "type": "int",
        "default": "1..strip_count-1",
        "valid": "1..3",
    },
    "decoy_count": {
        "type": "int",
        "default": "0..6",
        "valid": "0..6",
    },
    "cap_color": {
        "type": "color",
        "default": "9 on canonical-size prior; otherwise keyed random",
        "valid": "1|2|3|4|5|6|8|9",
    },
}


def _validate_call(difficulty, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")

    for name, lo, hi in (
        ("grid_h", 8, 20),
        ("grid_w", 8, 20),
        ("strip_count", 2, 4),
        ("marked_count", 1, 3),
        ("decoy_count", 0, 6),
    ):
        value = overrides.get(name)
        if value is None:
            continue
        if type(value) is not int or not lo <= value <= hi:
            raise ValueError(f"{name} must be an integer in {lo}..{hi}")

    for name, options in (
        ("orientation", _ORIENTATIONS),
        ("source_side", _SOURCE_SIDES),
    ):
        value = overrides.get(name)
        if value is not None and (type(value) is not str or value not in options):
            raise ValueError(f"{name} must be {'|'.join(options)}")

    value = overrides.get("cap_color")
    if value is not None and (type(value) is not int or value not in _MARKER_COLORS):
        raise ValueError("cap_color must be one of 1|2|3|4|5|6|8|9")

    strips = overrides.get("strip_count")
    marked = overrides.get("marked_count")
    if strips is not None and marked is not None and marked >= strips:
        raise ValueError("marked_count must be smaller than strip_count")


def _scheduled_choice(ctx, label: str, options, scheduled):
    if label in ctx.overrides:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, (scheduled,))


def _dimension_draw(ctx, label: str, minimum: int, profile_value: int | None) -> int:
    if label in ctx.overrides:
        return ctx.draw_int(label, minimum, 20)
    if profile_value is not None:
        if profile_value < minimum:
            raise AssertionError("profile dimension cannot fit requested strips")
        return ctx.draw_choice(label, (profile_value,))
    return ctx.draw_int_diff(label, minimum, 20)


def _strip_starts(span: int, count: int, rng) -> tuple[int, ...]:
    choices = [
        starts
        for starts in itertools.combinations(range(span - 2), count)
        if all(right - left >= 4 for left, right in zip(starts, starts[1:]))
    ]
    if not choices:
        raise ValueError(f"cannot place {count} separated 3-wide strips in span {span}")
    return rng.choice(choices)


def _safe_cap_cells(rng) -> tuple[tuple[int, int], ...]:
    """Choose a 1..3-cell cap that cannot split the black component.

    The first coordinate is the strip-thickness coordinate.  Keeping every
    marker on the middle thickness line leaves the two outer zero lanes intact
    from end to end, even for a three-cell cap.
    """
    size = rng.randint(1, 3)
    return tuple((1, major) for major in sorted(rng.sample(range(3), size)))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic input grid; the Racket program is the oracle."""
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    schedule = (
        ("horizontal", "low"),
        ("vertical", "high"),
        ("horizontal", "high"),
        ("vertical", "low"),
    )[sample_index % EXAMPLES_NEEDED]
    orientation = _scheduled_choice(ctx, "orientation", _ORIENTATIONS, schedule[0])
    source_side = _scheduled_choice(ctx, "source_side", _SOURCE_SIDES, schedule[1])

    requested_strips = overrides.get("strip_count")
    requested_marked = overrides.get("marked_count")
    minimum_strips = max(2, (int(requested_marked) + 1) if requested_marked is not None else 2)
    desired_strips = int(requested_strips) if requested_strips is not None else minimum_strips
    if desired_strips < minimum_strips:
        raise ValueError("strip_count cannot leave the requested marked_count an unmarked strip")
    minimum_minor = 4 * desired_strips - 1

    band = difficulty if difficulty in _PROFILE_PRIOR else "medium"
    use_profile = not overrides and ctx.draw_rng("scene_family").random() < _PROFILE_PRIOR[band]
    profile_size = None
    if use_profile:
        eligible = [size for size in _CANONICAL_SIZES if size >= minimum_minor]
        profile_size = ctx.draw_rng("canonical_size").choice(eligible)

    if orientation == "horizontal":
        h = _dimension_draw(ctx, "grid_h", max(8, minimum_minor), profile_size)
        w = _dimension_draw(ctx, "grid_w", 8, profile_size)
        minor = h
    else:
        h = _dimension_draw(ctx, "grid_h", 8, profile_size)
        w = _dimension_draw(ctx, "grid_w", max(8, minimum_minor), profile_size)
        minor = w

    max_strips = min(4, (minor + 1) // 4)
    if requested_strips is not None:
        strip_count = ctx.draw_int("strip_count", minimum_strips, max_strips)
    else:
        strip_count = ctx.draw_int_diff("strip_count", minimum_strips, max_strips)

    marked_count = ctx.draw_int("marked_count", 1, strip_count - 1)
    decoy_count = ctx.draw_int("decoy_count", 0, 6)
    if use_profile:
        cap_color = ctx.draw_choice("cap_color", (9,))
    else:
        cap_color = ctx.draw_choice("cap_color", _MARKER_COLORS)

    starts = _strip_starts(minor, strip_count, ctx.draw_rng("strip_positions"))
    marked_indices = set(
        ctx.draw_rng("marked_indices").sample(range(strip_count), marked_count)
    )
    grid = full_grid(h, w, 7)
    strip_cells: set[tuple[int, int]] = set()

    for index, start in enumerate(starts):
        if orientation == "horizontal":
            draw_rect(grid, start, 0, 3, w, 0)
            strip_cells.update((r, c) for r in range(start, start + 3) for c in range(w))
        else:
            draw_rect(grid, 0, start, h, 3, 0)
            strip_cells.update((r, c) for r in range(h) for c in range(start, start + 3))

        if index not in marked_indices:
            continue
        pattern = _safe_cap_cells(ctx.draw_rng(f"cap_pattern_{index}"))
        for local_minor, local_major in pattern:
            if source_side == "high":
                local_major = 2 - local_major
            if orientation == "horizontal":
                row = start + local_minor
                col = local_major if source_side == "low" else w - 1 - local_major
            else:
                row = local_major if source_side == "low" else h - 1 - local_major
                col = start + local_minor
            grid[row][col] = cap_color

    decoy_candidates = [
        (r, c)
        for r in range(h)
        for c in range(w)
        if (r, c) not in strip_cells
    ]
    if decoy_count > len(decoy_candidates):
        raise ValueError("decoy_count exceeds cells outside the strips")
    for r, c in ctx.draw_rng("decoy_positions").sample(decoy_candidates, decoy_count):
        grid[r][c] = cap_color

    errors = self_check(grid, difficulty=difficulty, meta={"overrides": overrides})
    if errors:
        raise AssertionError("generated invalid scene: " + "; ".join(errors))
    return grid


def _zero_components(grid) -> list[list[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[list[tuple[int, int]]] = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            component: list[tuple[int, int]] = []
            while stack:
                rr, cc = stack.pop()
                component.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and grid[nr][nc] == 0
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            components.append(component)
    return components


def _analyze(grid) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return {}, ["grid must be a nonempty list or tuple"]
    if not all(isinstance(row, (list, tuple)) and row for row in grid):
        return {}, ["grid rows must be nonempty lists or tuples"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return {}, ["grid must be rectangular"]
    h = len(grid)
    if not 8 <= h <= 20 or not 8 <= w <= 20:
        errors.append(f"grid dimensions must both be in 8..20, got {h}x{w}")
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("every cell must be an integer ARC color 0..9")
        return {}, errors

    marker_colors = sorted({value for row in grid for value in row if value not in (0, 7)})
    if len(marker_colors) != 1:
        errors.append(f"expected exactly one marker color besides 0 and 7, got {marker_colors}")
    cap_color = marker_colors[0] if len(marker_colors) == 1 else None

    components = _zero_components(grid)
    strips: list[dict[str, Any]] = []
    for component in components:
        rows = [r for r, _ in component]
        cols = [c for _, c in component]
        r1, r2, c1, c2 = min(rows), max(rows), min(cols), max(cols)
        bh, bw = r2 - r1 + 1, c2 - c1 + 1
        orientation = None
        if bh == 3 and c1 == 0 and c2 == w - 1 and bw >= 6:
            orientation = "horizontal"
        elif bw == 3 and r1 == 0 and r2 == h - 1 and bh >= 6:
            orientation = "vertical"
        if orientation is None:
            errors.append(
                "every black component must be a full-span 3-thick strip; "
                f"found bbox {(r1, c1, r2, c2)}"
            )
            continue
        bbox_cells = {(r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)}
        marker_cells = [
            (r, c)
            for r, c in bbox_cells
            if grid[r][c] not in (0, 7)
        ]
        if orientation == "horizontal":
            low = [(r, c) for r, c in marker_cells if c <= 2]
            high = [(r, c) for r, c in marker_cells if c >= w - 3]
            middle = [(r, c) for r, c in marker_cells if 3 <= c < w - 3]
        else:
            low = [(r, c) for r, c in marker_cells if r <= 2]
            high = [(r, c) for r, c in marker_cells if r >= h - 3]
            middle = [(r, c) for r, c in marker_cells if 3 <= r < h - 3]
        if middle:
            errors.append(f"strip {r1,c1,r2,c2} has marker cells outside both end blocks")
        if low and high:
            errors.append(f"strip {r1,c1,r2,c2} is marked at both ends")
        side = "low" if low else "high" if high else None
        strips.append(
            {
                "bbox": (r1, c1, r2, c2),
                "orientation": orientation,
                "source_side": side,
                "marker_count": len(marker_cells),
                "cells": bbox_cells,
            }
        )

    if len(components) != len(strips):
        errors.append("one or more black components is not a valid strip")
    if not 2 <= len(strips) <= 4:
        errors.append(f"expected 2..4 strips, got {len(strips)}")

    orientations = {strip["orientation"] for strip in strips}
    if len(orientations) != 1:
        errors.append(f"all strips must be parallel, got {sorted(orientations)}")
    orientation = next(iter(orientations)) if len(orientations) == 1 else None

    marked = [strip for strip in strips if strip["source_side"] is not None]
    if not marked:
        errors.append("at least one strip must carry a source cap")
    if len(marked) >= len(strips) and strips:
        errors.append("at least one strip must remain unmarked for fallback-direction teaching")
    source_sides = {strip["source_side"] for strip in marked}
    if len(source_sides) > 1:
        errors.append(f"marked strips disagree on source side: {sorted(source_sides)}")
    source_side = next(iter(source_sides)) if len(source_sides) == 1 else None

    strip_union = set().union(*(strip["cells"] for strip in strips)) if strips else set()
    outside_markers = [
        (r, c)
        for r in range(h)
        for c in range(w)
        if grid[r][c] not in (0, 7) and (r, c) not in strip_union
    ]
    if not 0 <= len(outside_markers) <= 6:
        errors.append(f"stationary decoy count must be in 0..6, got {len(outside_markers)}")

    facts = {
        "grid_h": h,
        "grid_w": w,
        "orientation": orientation,
        "source_side": source_side,
        "strip_count": len(strips),
        "marked_count": len(marked),
        "decoy_count": len(outside_markers),
        "cap_color": cap_color,
        "strip_bboxes": tuple(strip["bbox"] for strip in strips),
        "cap_sizes": tuple(strip["marker_count"] for strip in marked),
    }
    return facts, errors


def observe_overrides(grid) -> dict[str, Any]:
    """Recover every declared exact semantic axis from the returned pixels."""
    facts, errors = _analyze(grid)
    if errors:
        return {}
    return {name: facts[name] for name in AXES}


def profile_signature(grid) -> dict[str, Any]:
    """Task-linked feature extractor used by focused coverage evidence."""
    facts, errors = _analyze(grid)
    return {"valid": not errors, "errors": errors, **facts}


def is_canonical_like(grid) -> bool:
    facts, errors = _analyze(grid)
    return not errors and (
        facts["grid_h"] in _CANONICAL_SIZES
        and facts["grid_w"] in _CANONICAL_SIZES
        and facts["cap_color"] == 9
    )


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Structural, mutation-sensitive validation of the teaching scene."""
    del difficulty
    facts, errors = _analyze(grid)
    requested: dict[str, Any] = {}
    if isinstance(meta, dict):
        nested = meta.get("overrides")
        if isinstance(nested, dict):
            requested.update(nested)
        requested.update({name: meta[name] for name in AXES if name in meta})
    if facts and requested:
        observed = observe_overrides(grid)
        for axis, value in requested.items():
            if axis in AXES and observed.get(axis) != value:
                errors.append(
                    f"override {axis} requested {value!r}, observed {observed.get(axis)!r}"
                )
    return errors
