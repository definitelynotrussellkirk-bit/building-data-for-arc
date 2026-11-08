"""Generator for ARC task e9b4f6fc / content hash 36275402c6b2.

The input contains one frame-coloured rectangle with source-colour cells in its
crop, including a non-corner border cell on alternating draws. Horizontal pairs
outside the rectangle on any of its four sides encode
``(target, source)`` substitutions.  The answer is the rectangle's bounding-box
crop after applying every substitution.
"""
from __future__ import annotations

from collections import Counter, deque
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import fill_box, full_grid

GENERATOR_ID = "36275402c6b2"
TASK_ID = GENERATOR_ID
VERSION = "4.1.0"
RULE_HASH = "08894540e7f2"
EXAMPLES_NEEDED = 3
SCHEDULE_PROFILES = ("interior", "border_and_side")

SUMMARY = (
    "Find the unique largest same-colour component and crop its bounding box. "
    "Every isolated horizontal pair outside that box is read left-to-right as "
    "(replacement, source). Recolour all matching source cells inside the crop "
    "with their replacements; leave the frame cells unchanged."
)

INVARIANTS = [
    "background is colour 0",
    "the unique largest nonzero component defines the crop and occupies all four bbox corners",
    "two or three isolated outside horizontal pairs encode (target, source)",
    "frame, source, and target colours are pairwise distinct",
    "every source occurs inside the frame crop and no target does",
    "the output is the frame bbox crop after applying every left-to-right substitution",
]

# Every declared axis is an exact value recoverable from the returned grid by
# observe_overrides().  All boundary combinations fit by construction.
AXES = {
    "grid_h": {"type": "int", "default": "weighted 11..15", "valid": "11..15"},
    "grid_w": {"type": "int", "default": "weighted 11..15", "valid": "11..15"},
    "rect_h": {"type": "int", "default": "rng 4..7", "valid": "4..7"},
    "rect_w": {"type": "int", "default": "rng 4..7", "valid": "4..7"},
    "frame_color": {"type": "color", "default": "rng 1..9", "valid": "1..9"},
    "pair_count": {"type": "int", "default": "rng 2..3", "valid": "2..3"},
}

# The finite boundary matrix is fully supported; no multi-axis combination is
# intentionally rejected.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

_GRID_CHOICES = (11, 12, 13, 13, 13, 13, 13, 13, 14, 15)


def _coerce_grid(grid: Any) -> list[list[int]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("grid must be a non-empty sequence of rows")
    rows: list[list[int]] = []
    width: int | None = None
    for row in grid:
        if isinstance(row, str):
            values = [int(ch) for ch in row.strip()]
        elif isinstance(row, (list, tuple)):
            if any(type(value) is not int for value in row):
                raise ValueError("grid colours must be integers in 0..9")
            values = list(row)
        else:
            raise ValueError("every grid row must be a sequence")
        if width is None:
            width = len(values)
            if width == 0:
                raise ValueError("grid rows must be non-empty")
        elif len(values) != width:
            raise ValueError("grid must be rectangular")
        if any(value < 0 or value > 9 for value in values):
            raise ValueError("grid colours must be integers in 0..9")
        rows.append(values)
    return rows


def _components(grid: list[list[int]]) -> list[dict[str, Any]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[dict[str, Any]] = []
    for row in range(h):
        for col in range(w):
            colour = grid[row][col]
            if colour == 0 or (row, col) in seen:
                continue
            queue = deque([(row, col)])
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while queue:
                rr, cc = queue.popleft()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == colour
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            rs = [cell[0] for cell in cells]
            cs = [cell[1] for cell in cells]
            result.append(
                {
                    "color": colour,
                    "cells": cells,
                    "size": len(cells),
                    "bbox": (min(rs), min(cs), max(rs), max(cs)),
                }
            )
    return result


def _analyze(grid: Any) -> dict[str, Any]:
    try:
        values = _coerce_grid(grid)
    except (TypeError, ValueError) as exc:
        return {"errors": [str(exc)]}

    h, w = len(values), len(values[0])
    errors: list[str] = []
    comps = _components(values)
    if not comps:
        return {"errors": ["no nonzero object"]}

    sizes = sorted((component["size"] for component in comps), reverse=True)
    if len(sizes) > 1 and sizes[0] == sizes[1]:
        errors.append("largest nonzero component is not unique")
    frame_component = max(comps, key=lambda component: component["size"])
    frame = frame_component["color"]
    r1, c1, r2, c2 = frame_component["bbox"]
    rect_h, rect_w = r2 - r1 + 1, c2 - c1 + 1
    if rect_h < 4 or rect_w < 4:
        errors.append(f"frame bbox {rect_h}x{rect_w} is smaller than 4x4")
    corners = ((r1, c1), (r1, c2), (r2, c1), (r2, c2))
    if any(values[row][col] != frame for row, col in corners):
        errors.append("all four frame-bbox corners must have the frame colour")

    def inside(row: int, col: int) -> bool:
        return r1 <= row <= r2 and c1 <= col <= c2

    outside_nonzero = {
        (r, c)
        for r in range(h)
        for c in range(w)
        if values[r][c] != 0 and not inside(r, c)
    }
    pair_cells: set[tuple[int, int]] = set()
    pairs: list[tuple[int, int, int, int]] = []
    for row in range(h):
        col = 0
        while col < w:
            if (row, col) not in outside_nonzero:
                col += 1
                continue
            start = col
            while col < w and (row, col) in outside_nonzero:
                col += 1
            run = list(range(start, col))
            if len(run) != 2:
                errors.append(
                    f"outside nonzero run at row {row}, cols {start}..{col - 1} has length {len(run)}, expected 2"
                )
                pair_cells.update((row, cc) for cc in run)
                continue
            left, right = run
            target, source = values[row][left], values[row][right]
            pairs.append((target, source, row, left))
            pair_cells.update(((row, left), (row, right)))

    leftovers = sorted(outside_nonzero - pair_cells)
    if leftovers:
        errors.append(f"outside nonzero cell {leftovers[0]} is not part of an isolated pair")
    if len(pairs) not in (2, 3):
        errors.append(f"found {len(pairs)} outside pairs, expected 2 or 3")

    targets = [pair[0] for pair in pairs]
    sources = [pair[1] for pair in pairs]
    role_colours = [frame, *targets, *sources]
    if len(set(role_colours)) != len(role_colours):
        errors.append("frame, targets, and sources must be pairwise distinct")

    crop = [row[c1 : c2 + 1] for row in values[r1 : r2 + 1]]
    crop_counts = Counter(value for row in crop for value in row)
    allowed_crop = {frame, *sources}
    extra_crop = sorted(set(crop_counts) - allowed_crop)
    if extra_crop:
        errors.append(f"crop contains unkeyed colour {extra_crop[0]}")
    for source in sources:
        if crop_counts[source] == 0:
            errors.append(f"source colour {source} is absent from the crop")
    for target in targets:
        if crop_counts[target] != 0:
            errors.append(f"target colour {target} already occurs inside the crop")

    other_max = max(
        (component["size"] for component in comps if component is not frame_component),
        default=0,
    )
    if frame_component["size"] <= other_max:
        errors.append("frame is not strictly larger than every other component")

    mapping = {source: target for target, source, _, _ in pairs}
    output = [[mapping.get(value, value) for value in row] for row in crop]
    changed = sum(
        int(before != after)
        for before_row, after_row in zip(crop, output)
        for before, after in zip(before_row, after_row)
    )
    if changed == 0:
        errors.append("the encoded transformation is an identity")

    return {
        "errors": errors,
        "grid": values,
        "height": h,
        "width": w,
        "frame": frame,
        "bbox": (r1, c1, r2, c2),
        "rect_h": rect_h,
        "rect_w": rect_w,
        "pairs": pairs,
        "pair_count": len(pairs),
        "sources": sources,
        "targets": targets,
        "crop": crop,
        "mapping": mapping,
        "output": output,
        "changed": changed,
    }


def _analysis_or_raise(grid: Any) -> dict[str, Any]:
    analysis = _analyze(grid)
    if analysis.get("errors"):
        raise ValueError("invalid task grid: " + "; ".join(analysis["errors"]))
    return analysis


def _legend_slots(height: int, width: int, bbox: tuple[int, int, int, int]):
    r1, c1, r2, c2 = bbox
    # Both cells of a legend pair stay outside the crop with a black-cell gap.
    # Keep row-major order: the exact sampler counts this ordered slot set.
    return [
        (row, col)
        for row in range(height)
        for col in range(width - 1)
        if row <= r1 - 2 or row >= r2 + 2 or col + 1 <= c1 - 2 or col >= c2 + 2
    ]


def _choose_legend_slots(height, width, bbox, count, rng, *, require_side=False):
    slots = _legend_slots(height, width, bbox)
    n = len(slots)
    if count < 0:
        raise ValueError("r must be non-negative")
    if count > n:
        raise ValueError("no lawful isolated legend placement")
    is_side = [require_side and bbox[0] <= row <= bbox[2] for row, _ in slots]

    # Slots are in row-major order. After taking i, skip starts on its row
    # until the next pair has at least one black cell between the two pairs.
    # The monotone pointer also handles gaps and transitions to a new row.
    next_slot = [n] * n
    following = 0
    for i, (row, col) in enumerate(slots):
        following = max(following, i + 1)
        while following < n:
            next_row, next_col = slots[following]
            if next_row != row or next_col >= col + 3:
                break
            following += 1
        next_slot[i] = following

    # ways[i][k] counts legal k-slot selections from the suffix starting at i.
    # Every selection either skips i or takes i and resumes at next_slot[i].
    # This needs O(n * count) table cells, instead of materializing C(n,count)
    # candidates. Integer counts retain the exact uniform distribution.
    ways = [[0] * (count + 1) for _ in range(n + 1)]
    # The optional second table counts selections containing a side witness.
    # Taking a side slot satisfies the requirement; otherwise it persists.
    ways_side = (
        [[0] * (count + 1) for _ in range(n + 1)] if require_side else None
    )
    ways[n][0] = 1
    for i in range(n - 1, -1, -1):
        ways[i][0] = 1
        for remaining in range(1, count + 1):
            ways[i][remaining] = (
                ways[i + 1][remaining] + ways[next_slot[i]][remaining - 1]
            )
            if ways_side is not None:
                suffix = ways if is_side[i] else ways_side
                ways_side[i][remaining] = (
                    ways_side[i + 1][remaining] + suffix[next_slot[i]][remaining - 1]
                )
    total = ways_side[0][count] if ways_side is not None else ways[0][count]
    if not total:
        raise ValueError("no lawful isolated legend placement")

    # Random.choice(lawful) uses the same _randbelow(total) draw as randrange.
    # Unrank in combinations() order: the block taking i precedes skipping i.
    rank = rng.randrange(total)
    chosen = []
    i, remaining = 0, count
    need_side = require_side
    while remaining:
        suffix = ways_side if need_side and not is_side[i] else ways
        taking = suffix[next_slot[i]][remaining - 1]
        if rank < taking:
            chosen.append(slots[i])
            need_side = need_side and not is_side[i]
            i = next_slot[i]
            remaining -= 1
        else:
            rank -= taking
            i += 1
    return chosen


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis: {unknown[0]}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    grid_h = ctx.draw_choice("grid_h", _GRID_CHOICES)
    grid_w = ctx.draw_choice("grid_w", _GRID_CHOICES)
    rect_h = ctx.draw_int("rect_h", 4, 7)
    rect_w = ctx.draw_int("rect_w", 4, 7)
    frame = ctx.draw_color("frame_color", exclude=(0,))
    pair_count = ctx.draw_int("pair_count", 2, 3)

    role_colours = ctx.draw_distinct_colors(
        "role_colours", n=2 * pair_count, exclude=(0, frame)
    )
    sources = list(role_colours[:pair_count])
    targets = list(role_colours[pair_count:])

    layout_rng = ctx.draw_rng("layout")
    border_and_side = sample_index % 2 == 1
    r0 = layout_rng.randint(0, grid_h - rect_h)
    crop_columns = list(range(grid_w - rect_w + 1))
    if border_and_side:
        # A horizontal two-cell legend needs three columns including its gap.
        # grid_w - rect_w >= 4 for every advertised joint override, so this
        # conditional set is nonempty even for an 11x11 grid with a 7x7 crop.
        crop_columns = [
            col for col in crop_columns
            if col >= 3 or grid_w - col - rect_w >= 3
        ]
    c0 = layout_rng.choice(crop_columns)
    bbox = (r0, c0, r0 + rect_h - 1, c0 + rect_w - 1)

    grid = full_grid(grid_h, grid_w, 0)
    fill_box(grid, *bbox, frame)

    interior = [
        (row, col)
        for row in range(r0 + 1, r0 + rect_h - 1)
        for col in range(c0 + 1, c0 + rect_w - 1)
    ]
    texture_rng = ctx.draw_rng("source_texture")
    texture_rng.shuffle(interior)
    difficulty_fraction = {"easy": 0.35, "medium": 0.50, "hard": 0.65}.get(
        difficulty, 0.50
    )
    max_cells = max(pair_count, min(len(interior), round(len(interior) * difficulty_fraction)))
    total_source_cells = texture_rng.randint(pair_count, max_cells)
    assignments = sources[:]
    assignments.extend(texture_rng.choice(sources) for _ in range(total_source_cells - pair_count))
    texture_rng.shuffle(assignments)
    for (row, col), colour in zip(interior, assignments):
        grid[row][col] = colour

    if border_and_side:
        # Removing one non-corner cell from the rectangular frame's perimeter
        # leaves a connected path through all four corners. Its size still
        # exceeds every source component throughout the declared size range.
        boundary = [
            (row, col)
            for row in range(r0, r0 + rect_h)
            for col in range(c0, c0 + rect_w)
            if (row in (r0, r0 + rect_h - 1) or col in (c0, c0 + rect_w - 1))
            and not (row in (r0, r0 + rect_h - 1) and col in (c0, c0 + rect_w - 1))
        ]
        row, col = texture_rng.choice(boundary)
        grid[row][col] = texture_rng.choice(sources)

    legend_rng = ctx.draw_rng("legend_layout")
    slots = _choose_legend_slots(
        grid_h, grid_w, bbox, pair_count, legend_rng, require_side=border_and_side
    )
    mappings = list(zip(targets, sources))
    legend_rng.shuffle(mappings)
    legend_rng.shuffle(slots)
    for (target, source), (row, col) in zip(mappings, slots):
        grid[row][col] = target
        grid[row][col + 1] = source

    errors = self_check(
        grid,
        difficulty=difficulty,
        meta={"overrides": ctx.overrides_used()},
    )
    if errors:
        raise AssertionError("generator produced invalid task grid: " + "; ".join(errors))
    return grid


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty
    analysis = _analyze(grid)
    errors = list(analysis.get("errors", []))
    if errors or not isinstance(meta, dict):
        return errors
    requested = meta.get("overrides") if isinstance(meta.get("overrides"), dict) else meta
    observed = observe_overrides(grid)
    for axis, value in requested.items():
        if axis in observed and observed[axis] != value:
            errors.append(f"meta {axis} requested {value!r}, observed {observed[axis]!r}")
    return errors


def observe_overrides(grid) -> dict[str, int]:
    analysis = _analysis_or_raise(grid)
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "rect_h": analysis["rect_h"],
        "rect_w": analysis["rect_w"],
        "frame_color": analysis["frame"],
        "pair_count": analysis["pair_count"],
    }


def strict_canonical_like(grid) -> list[str]:
    analysis = _analyze(grid)
    errors = list(analysis.get("errors", []))
    if errors:
        return errors
    if analysis["height"] != 13 or analysis["width"] != 13:
        return ["canonical grids are 13x13"]
    palette_size = len({value for row in analysis["grid"] for value in row})
    expected_palette = 2 + 2 * analysis["pair_count"]
    if palette_size != expected_palette:
        return [
            f"canonical palette has background plus frame and two colours per pair ({expected_palette}), got {palette_size}"
        ]
    return []


def rule_mirror(grid) -> list[list[int]]:
    """Diagnostic mirror; canonical Racket remains the sole output authority."""
    return [row[:] for row in _analysis_or_raise(grid)["output"]]


def _rival_reverse_pair_direction(grid):
    analysis = _analysis_or_raise(grid)
    reverse = {target: source for target, source, _, _ in analysis["pairs"]}
    return [[reverse.get(value, value) for value in row] for row in analysis["crop"]]


def _rival_first_pair_only(grid):
    analysis = _analysis_or_raise(grid)
    target, source, _, _ = analysis["pairs"][0]
    return [[target if value == source else value for value in row] for row in analysis["crop"]]


def _rival_source_to_frame(grid):
    analysis = _analysis_or_raise(grid)
    source_set = set(analysis["sources"])
    return [
        [analysis["frame"] if value in source_set else value for value in row]
        for row in analysis["crop"]
    ]


def _rival_recolour_whole_grid(grid):
    analysis = _analysis_or_raise(grid)
    return [
        [analysis["mapping"].get(value, value) for value in row]
        for row in analysis["grid"]
    ]


def _rival_preserve_border_sources(grid):
    analysis = _analysis_or_raise(grid)
    output = [row[:] for row in analysis["output"]]
    crop = analysis["crop"]
    for row in range(len(crop)):
        for col in range(len(crop[0])):
            if row in (0, len(crop) - 1) or col in (0, len(crop[0]) - 1):
                output[row][col] = crop[row][col]
    return output


def _rival_ignore_side_legends(grid):
    analysis = _analysis_or_raise(grid)
    r1, _, r2, _ = analysis["bbox"]
    mapping = {
        source: target for target, source, row, _ in analysis["pairs"]
        if row < r1 or row > r2
    }
    return [[mapping.get(value, value) for value in row] for row in analysis["crop"]]


SEMANTIC_RIVALS = {
    "reverse_pair_direction": _rival_reverse_pair_direction,
    "first_pair_only": _rival_first_pair_only,
    "replace_sources_with_frame": _rival_source_to_frame,
    "recolour_whole_grid": _rival_recolour_whole_grid,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS.update({
    "preserve_border_sources": _rival_preserve_border_sources,
    "ignore_side_legends": _rival_ignore_side_legends,
})
# These rivals are already refuted by canonical pairs. None is claimed to be
# a shortcut that fits every canonical answer.
CANONICAL_SHORTCUTS = {}
SEMANTIC_RIVALS.update({
    name: LESSON_COMPETITORS[name]
    for name in ("preserve_border_sources", "ignore_side_legends")
})


def schedule_profile(seed, sample_index, difficulty=None):
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % 2]


def _valid_analysis(grid):
    analysis = _analyze(grid)
    return None if analysis.get("errors") else analysis


def _pair_count_is(grid, count):
    analysis = _valid_analysis(grid)
    return analysis is not None and analysis["pair_count"] == count


def _rect_relation(grid, relation):
    analysis = _valid_analysis(grid)
    if analysis is None:
        return False
    if relation == "square":
        return analysis["rect_h"] == analysis["rect_w"]
    return analysis["rect_h"] != analysis["rect_w"]


def _legend_above(grid):
    analysis = _valid_analysis(grid)
    return analysis is not None and any(row < analysis["bbox"][0] for _, _, row, _ in analysis["pairs"])


def _legend_below(grid):
    analysis = _valid_analysis(grid)
    return analysis is not None and any(row > analysis["bbox"][2] for _, _, row, _ in analysis["pairs"])


def _canonical_profile(grid):
    return strict_canonical_like(grid) == []


def _has_border_source(grid):
    analysis = _valid_analysis(grid)
    if analysis is None:
        return False
    crop = analysis["crop"]
    return any(
        value in analysis["sources"]
        and (row in (0, len(crop) - 1) or col in (0, len(crop[0]) - 1))
        for row, values in enumerate(crop) for col, value in enumerate(values)
    )


def _has_side_legend(grid):
    analysis = _valid_analysis(grid)
    return analysis is not None and any(
        analysis["bbox"][0] <= row <= analysis["bbox"][2]
        for _, _, row, _ in analysis["pairs"]
    )


SEMANTIC_WITNESSES = {
    "left_to_right_mapping": lambda grid: _valid_analysis(grid) is not None,
    "all_pairs_required": lambda grid: _valid_analysis(grid) is not None,
    "crop_output_geometry": lambda grid: _valid_analysis(grid) is not None,
    "targets_are_not_frame": lambda grid: _valid_analysis(grid) is not None,
    "two_pair_branch": lambda grid: _pair_count_is(grid, 2),
    "three_pair_branch": lambda grid: _pair_count_is(grid, 3),
    "square_crop_branch": lambda grid: _rect_relation(grid, "square"),
    "nonsquare_crop_branch": lambda grid: _rect_relation(grid, "nonsquare"),
    "legend_above_crop": _legend_above,
    "legend_below_crop": _legend_below,
    "canonical_13x13_profile": _canonical_profile,
    "border_source_recoloured": _has_border_source,
    "side_legend_applied": _has_side_legend,
}

WITNESS_RIVALS = {
    "left_to_right_mapping": ["reverse_pair_direction"],
    "all_pairs_required": ["first_pair_only"],
    "crop_output_geometry": ["recolour_whole_grid"],
    "targets_are_not_frame": ["replace_sources_with_frame"],
    "two_pair_branch": ["first_pair_only"],
    "three_pair_branch": ["first_pair_only"],
    "square_crop_branch": ["recolour_whole_grid"],
    "nonsquare_crop_branch": ["recolour_whole_grid"],
    "legend_above_crop": ["reverse_pair_direction"],
    "legend_below_crop": ["reverse_pair_direction"],
    "canonical_13x13_profile": ["first_pair_only"],
    "border_source_recoloured": ["preserve_border_sources"],
    "side_legend_applied": ["ignore_side_legends"],
}


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    all_pairs = [*demos, query]
    for index, pair in enumerate(all_pairs):
        label = f"demo {index}" if index < len(demos) else "query"
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"{label} is not an input/output pair")
            continue
        structural = self_check(pair["input"])
        if structural:
            reasons.append(f"{label} input violates teaching grammar: {structural[0]}")
            continue
        if rule_mirror(pair["input"]) != _coerce_grid(pair["output"]):
            reasons.append(f"{label} output disagrees with the substitution rule")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(competitor(demo["input"]) == _coerce_grid(demo["output"]) for demo in demos)
        if survives and competitor(query["input"]) != _coerce_grid(query["output"]):
            reasons.append(
                f"competing rule {name!r} fits every demo but answers the query differently"
            )
    return reasons
