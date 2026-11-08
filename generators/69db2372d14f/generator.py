"""Generator for ARC task 83eb0a57.

The input contains a unique largest filled rectangle (the output container)
and one to three smaller filled rectangles (pieces).  Each piece shares an
anchor color with the container.  Crop the container, slide each piece-shaped
window over the evolving crop until the anchor-color cells match exactly, and
paste the whole piece there.  Pieces are processed largest first.

The three-profile schedule is lesson-level: every three consecutive examples
contain a one-piece canonical-scale scene, a two-piece shared-anchor scene,
and a three-piece distinct-anchor scene.  That makes crop-only, first-piece-
only, fixed-position, and one-marker-per-piece shortcuts observable.
"""
from __future__ import annotations

import copy
from collections import Counter, deque
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "69db2372d14f"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "657328d7828c"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.50

SUMMARY = (
    "Crop the unique largest multicolor rectangle; paste every smaller "
    "multicolor rectangle into it where that piece's shared marker-color "
    "pattern aligns exactly, processing pieces largest first."
)

INVARIANTS = [
    "the modal color is a unique background and separates every object",
    "there are two to four full rectangular multicolor objects",
    "the unique largest object is the output container",
    "each smaller rectangle has exactly one usable shared marker color",
    "each piece has exactly one exact marker-pattern alignment in the evolving container",
    "every aligned paste changes at least one non-marker cell",
]

# Every declared axis is exact and recoverable from the returned grid.
AXES = {
    "grid_h": {
        "type": "int",
        "default": "profile/difficulty schedule within 24..30",
        "valid": "24..30",
    },
    "grid_w": {
        "type": "int",
        "default": "profile/difficulty schedule within 24..30",
        "valid": "24..30",
    },
    "piece_count": {
        "type": "int",
        "default": "three-profile schedule 1..3",
        "valid": "1..3",
    },
    "container_top": {
        "type": "bool",
        "default": "three-profile schedule false|true",
        "valid": "false|true",
    },
}

# Declared empty means every Cartesian combination of the exact axes is lawful.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[()] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

SCHEDULE_PROFILES = (
    "canonical_single",
    "canonical_shared_pair",
    "distinct_triple",
)

_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_CANONICAL_CONTAINER_SHAPES = {(9, 5), (10, 10), (12, 16), (13, 15)}


def schedule_profile(seed, sample_index, difficulty=None):
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _mode_with_tie(values: list[int]) -> tuple[int, bool]:
    counts = Counter(values)
    if not counts:
        raise ValueError("empty color stream")
    top = max(counts.values())
    winners = [value for value, count in counts.items() if count == top]
    return min(winners), len(winners) > 1


def _bbox(cells: list[tuple[int, int]]) -> tuple[int, int, int, int]:
    return (
        min(r for r, _ in cells),
        min(c for _, c in cells),
        max(r for r, _ in cells),
        max(c for _, c in cells),
    )


def _crop(grid: list[list[int]], bbox: tuple[int, int, int, int]) -> list[list[int]]:
    r1, c1, r2, c2 = bbox
    return [row[c1 : c2 + 1] for row in grid[r1 : r2 + 1]]


def _components(grid: list[list[int]], background: int) -> list[list[tuple[int, int]]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[list[tuple[int, int]]] = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] == background or (row, col) in seen:
                continue
            queue = deque([(row, col)])
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while queue:
                current = queue.popleft()
                cells.append(current)
                for dr, dc in _CARDINAL:
                    neighbor = (current[0] + dr, current[1] + dc)
                    if not (0 <= neighbor[0] < height and 0 <= neighbor[1] < width):
                        continue
                    if neighbor in seen or grid[neighbor[0]][neighbor[1]] == background:
                        continue
                    seen.add(neighbor)
                    queue.append(neighbor)
            components.append(cells)
    return components


def _ordered_colors_latest(grid: list[list[int]], background: int) -> list[int]:
    seen: list[int] = []
    for row in grid:
        for value in row:
            if value != background and value not in seen:
                seen.append(value)
    return list(reversed(seen))


def _alignment_hits(
    out: list[list[int]], piece: list[list[int]], marker: int
) -> list[tuple[int, int]]:
    out_h, out_w = len(out), len(out[0])
    piece_h, piece_w = len(piece), len(piece[0])
    local_marker = {
        (row, col)
        for row in range(piece_h)
        for col in range(piece_w)
        if piece[row][col] == marker
    }
    if not local_marker or piece_h > out_h or piece_w > out_w:
        return []
    hits: list[tuple[int, int]] = []
    for dr in range(out_h - piece_h + 1):
        for dc in range(out_w - piece_w + 1):
            window_marker = {
                (row - dr, col - dc)
                for row in range(dr, dr + piece_h)
                for col in range(dc, dc + piece_w)
                if out[row][col] == marker
            }
            if window_marker == local_marker:
                hits.append((dr, dc))
    return hits


def _paint_piece(
    out: list[list[int]], piece: list[list[int]], offset: tuple[int, int], background: int
) -> list[list[int]]:
    result = copy.deepcopy(out)
    dr, dc = offset
    for row, values in enumerate(piece):
        for col, value in enumerate(values):
            if value != background:
                result[dr + row][dc + col] = value
    return result


def _analyze_grid(grid: Any) -> tuple[list[str], dict[str, Any] | None]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return ["grid must be a non-empty list of non-empty rows"], None
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid must be rectangular"], None
    height = len(grid)
    if not (4 <= height <= 30 and 4 <= width <= 30):
        errors.append(f"grid dimensions must be within 4..30, got {height}x{width}")
    if any(type(value) is not int or not (0 <= value <= 9) for row in grid for value in row):
        errors.append("grid colors must be integers in 0..9")
    if errors:
        return errors, None

    background, tied_mode = _mode_with_tie([value for row in grid for value in row])
    if tied_mode:
        errors.append("background mode must be unique")
    components = _components(grid, background)
    if not (2 <= len(components) <= 4):
        errors.append(f"expected 2..4 non-background objects, found {len(components)}")

    infos: list[dict[str, Any]] = []
    for index, cells in enumerate(components):
        bbox = _bbox(cells)
        r1, c1, r2, c2 = bbox
        area = (r2 - r1 + 1) * (c2 - c1 + 1)
        colors = Counter(grid[row][col] for row, col in cells)
        if area != len(cells):
            errors.append(f"object {index} is not a full rectangle")
        if len(colors) < 2:
            errors.append(f"object {index} is not multicolor")
        infos.append(
            {
                "index": index,
                "cells": cells,
                "bbox": bbox,
                "size": len(cells),
                "height": r2 - r1 + 1,
                "width": c2 - c1 + 1,
                "colors": colors,
                "rect": _crop(grid, bbox),
            }
        )
    if errors:
        return sorted(set(errors)), None

    largest_size = max(info["size"] for info in infos)
    containers = [info for info in infos if info["size"] == largest_size]
    if len(containers) != 1:
        return [f"largest object must be unique, found {len(containers)} tied objects"], None
    container = containers[0]
    pieces = sorted(
        (info for info in infos if info is not container),
        key=lambda info: (-info["size"], info["bbox"][0], info["bbox"][1]),
    )
    if any(piece["size"] >= container["size"] for piece in pieces):
        errors.append("every piece must be smaller than the container")

    max_count = max(container["colors"].values())
    dominant = [color for color, count in container["colors"].items() if count == max_count]
    if len(dominant) != 1:
        errors.append("container dominant color must be unique")
        container_color = dominant[0]
    else:
        container_color = dominant[0]

    initial_out = copy.deepcopy(container["rect"])
    out = copy.deepcopy(initial_out)
    piece_records: list[dict[str, Any]] = []
    for piece_index, piece in enumerate(pieces):
        piece_colors = _ordered_colors_latest(piece["rect"], background)
        out_colors = set(_ordered_colors_latest(out, background))
        common = [
            color
            for color in piece_colors
            if color != container_color and color in out_colors
        ]
        if len(common) != 1:
            errors.append(
                f"piece {piece_index} must have exactly one usable shared marker color, "
                f"found {common}"
            )
            continue
        marker = common[0]
        hits = _alignment_hits(out, piece["rect"], marker)
        if len(hits) != 1:
            errors.append(
                f"piece {piece_index} must have exactly one exact marker alignment, "
                f"found {len(hits)}"
            )
            continue
        hit = hits[0]
        changed = sum(
            piece["rect"][row][col] != out[hit[0] + row][hit[1] + col]
            for row in range(piece["height"])
            for col in range(piece["width"])
            if piece["rect"][row][col] != background
        )
        if changed == 0:
            errors.append(f"piece {piece_index} paste changes no cells")
            continue
        out = _paint_piece(out, piece["rect"], hit, background)
        piece_records.append({**piece, "marker": marker, "hit": hit, "changed": changed})

    if errors:
        return sorted(set(errors)), None

    r1, _, r2, _ = container["bbox"]
    container_top = (r1 + r2 + 1) < height
    analysis = {
        "height": height,
        "width": width,
        "background": background,
        "palette_size": len(set(value for row in grid for value in row)),
        "container": container,
        "container_color": container_color,
        "container_top": container_top,
        "pieces": piece_records,
        "piece_count": len(piece_records),
        "initial_out": initial_out,
        "output": out,
        "marker_colors": [record["marker"] for record in piece_records],
    }
    return [], analysis


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed rectangles, ambiguous anchors, and rule-hiding scenes."""
    del difficulty, meta
    errors, _ = _analyze_grid(grid)
    return errors


def observe_overrides(grid) -> dict[str, int | bool]:
    """Recover every exact declared axis from a valid returned grid."""
    errors, analysis = _analyze_grid(grid)
    if errors or analysis is None:
        raise ValueError("cannot observe axes from invalid grid: " + "; ".join(errors))
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "piece_count": analysis["piece_count"],
        "container_top": analysis["container_top"],
    }


def rule_python(grid: list[list[int]]) -> list[list[int]]:
    """Pure Python mirror for tests and shortcut analysis only.

    The canonical Racket program remains the sole output authority used by the
    materialization and validation pipeline.
    """
    errors, analysis = _analyze_grid(grid)
    if errors or analysis is None:
        raise ValueError("outside rule domain: " + "; ".join(errors))
    return copy.deepcopy(analysis["output"])


def strict_canonical_like(grid) -> list[str]:
    """Task-linked canonical manifold, not merely coarse morphology."""
    reasons, analysis = _analyze_grid(grid)
    if reasons or analysis is None:
        return reasons
    if (analysis["height"], analysis["width"]) != (30, 30):
        reasons.append(
            f"canonical input shape is 30x30, got {analysis['height']}x{analysis['width']}"
        )
    if analysis["palette_size"] not in {4, 5}:
        reasons.append(f"canonical palette size is 4 or 5, got {analysis['palette_size']}")
    container_shape = (
        analysis["container"]["height"],
        analysis["container"]["width"],
    )
    if container_shape not in _CANONICAL_CONTAINER_SHAPES:
        reasons.append(f"container shape {container_shape} is outside canonical support")
    if analysis["piece_count"] not in {1, 2}:
        reasons.append(f"canonical piece count is 1 or 2, got {analysis['piece_count']}")
    return reasons


def _analysis_if_valid(grid):
    errors, analysis = _analyze_grid(grid)
    return None if errors else analysis


def _rival_crop_only(grid):
    analysis = _analysis_if_valid(grid)
    if analysis is None:
        return copy.deepcopy(grid)
    return copy.deepcopy(analysis["initial_out"])


def _rival_largest_piece_only(grid):
    analysis = _analysis_if_valid(grid)
    if analysis is None:
        return copy.deepcopy(grid)
    out = copy.deepcopy(analysis["initial_out"])
    if analysis["pieces"]:
        piece = analysis["pieces"][0]
        out = _paint_piece(out, piece["rect"], piece["hit"], analysis["background"])
    return out


def _rival_top_left_paste(grid):
    analysis = _analysis_if_valid(grid)
    if analysis is None:
        return copy.deepcopy(grid)
    out = copy.deepcopy(analysis["initial_out"])
    for piece in analysis["pieces"]:
        out = _paint_piece(out, piece["rect"], (0, 0), analysis["background"])
    return out


SEMANTIC_RIVALS: dict[str, Callable] = {
    "crop_container_only": _rival_crop_only,
    "paste_only_largest_piece": _rival_largest_piece_only,
    "paste_every_piece_at_top_left": _rival_top_left_paste,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _witness_strict(grid):
    return strict_canonical_like(grid) == []


def _witness_single_piece(grid):
    analysis = _analysis_if_valid(grid)
    return analysis is not None and analysis["piece_count"] == 1


def _witness_multiple_pieces(grid):
    analysis = _analysis_if_valid(grid)
    return analysis is not None and analysis["piece_count"] >= 2


def _witness_non_top_left_alignment(grid):
    analysis = _analysis_if_valid(grid)
    return analysis is not None and any(piece["hit"] != (0, 0) for piece in analysis["pieces"])


def _witness_shared_marker(grid):
    analysis = _analysis_if_valid(grid)
    if analysis is None or analysis["piece_count"] < 2:
        return False
    return len(set(analysis["marker_colors"])) == 1


def _witness_distinct_markers(grid):
    analysis = _analysis_if_valid(grid)
    if analysis is None or analysis["piece_count"] < 2:
        return False
    return len(set(analysis["marker_colors"])) == analysis["piece_count"]


SEMANTIC_WITNESSES = {
    "canonical_30x30_palette_and_output_shape": _witness_strict,
    "single_piece_branch": _witness_single_piece,
    "multiple_pieces_all_applied": _witness_multiple_pieces,
    "non_top_left_exact_alignment": _witness_non_top_left_alignment,
    "multiple_pieces_share_one_marker_color": _witness_shared_marker,
    "pieces_use_distinct_marker_colors": _witness_distinct_markers,
}

WITNESS_RIVALS = {
    "canonical_30x30_palette_and_output_shape": ["crop_container_only"],
    "single_piece_branch": ["crop_container_only", "paste_every_piece_at_top_left"],
    "multiple_pieces_all_applied": ["crop_container_only", "paste_only_largest_piece"],
    "non_top_left_exact_alignment": ["paste_every_piece_at_top_left"],
    "multiple_pieces_share_one_marker_color": ["paste_only_largest_piece"],
    "pieces_use_distinct_marker_colors": ["paste_only_largest_piece"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require every three-demo lesson to kill the named shortcut family."""
    reasons: list[str] = []
    analyses: list[dict[str, Any]] = []
    for index, demo in enumerate(demos):
        analysis = _analysis_if_valid(demo["input"])
        if analysis is None:
            reasons.append(f"demo {index} is outside the rule domain")
            continue
        analyses.append(analysis)
        if rule_python(demo["input"]) != demo["output"]:
            reasons.append(f"demo {index} output disagrees with marker-alignment composition")
    query_analysis = _analysis_if_valid(query["input"])
    if query_analysis is None:
        reasons.append("query is outside the rule domain")
        return reasons
    query_answer = rule_python(query["input"])

    counts = {analysis["piece_count"] for analysis in analyses}
    if counts != {1, 2, 3}:
        reasons.append(f"demos must cover piece counts 1, 2, and 3; got {sorted(counts)}")
    if not any(
        analysis["piece_count"] >= 2
        and len(set(analysis["marker_colors"])) == 1
        for analysis in analyses
    ):
        reasons.append("demos lack a multi-piece shared-marker example")
    if not any(
        analysis["piece_count"] >= 2
        and len(set(analysis["marker_colors"])) == analysis["piece_count"]
        for analysis in analyses
    ):
        reasons.append("demos lack a multi-piece distinct-marker example")
    if not ({True, False} <= {analysis["container_top"] for analysis in analyses}):
        reasons.append("demos do not vary the container between top and bottom placements")

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(competitor(demo["input"]) == demo["output"] for demo in demos)
        if survives and competitor(query["input"]) != query_answer:
            reasons.append(f"competing rule {name!r} fits every demo but changes the query")
    return reasons


def _draw_int_axis(ctx, label: str, lo: int, hi: int, default: int) -> int:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, default, default)


def _draw_bool_axis(ctx, label: str, default: bool) -> bool:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return bool(ctx.draw_choice(label, (False, True)))
    return bool(ctx.draw_choice(label, (default,)))


def _validate_call(difficulty, overrides) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {unknown}")
    for label in ("grid_h", "grid_w", "piece_count"):
        if label in overrides and overrides[label] is not None and type(overrides[label]) is not int:
            raise ValueError(f"{label} override must be an integer")
    if (
        "container_top" in overrides
        and overrides["container_top"] is not None
        and type(overrides["container_top"]) is not bool
    ):
        raise ValueError("container_top override must be a boolean")


def _profile_defaults(profile: int, difficulty: str | None) -> tuple[int, int, int, bool]:
    if profile == 0:
        return 30, 30, 1, True
    if profile == 1:
        return 30, 30, 2, False
    size = {None: 27, "easy": 24, "medium": 27, "hard": 30}[difficulty]
    return size, size, 3, True


def _container_dimensions(profile: int, piece_count: int, height: int, width: int, rng) -> tuple[int, int]:
    if profile == 0 and piece_count == 1:
        return 9, 5
    if profile == 1 and piece_count == 2:
        return 10, 10
    if profile == 2 and piece_count == 3:
        return 12, 16
    minimum_width = {1: 6, 2: 10, 3: 14}[piece_count]
    maximum_width = min(16, width - 4)
    container_w = rng.randint(minimum_width, maximum_width)
    minimum_height = {1: 7, 2: 8, 3: 9}[piece_count]
    maximum_height = min(14, height - 9)
    container_h = rng.randint(minimum_height, maximum_height)
    return container_h, container_w


def _piece_dimensions(piece_count: int) -> list[tuple[int, int]]:
    if piece_count == 1:
        return [(3, 3)]
    if piece_count == 2:
        return [(4, 4), (3, 3)]
    return [(5, 4), (4, 3), (3, 3)]


def _shared_marker_masks(piece_count: int) -> list[tuple[tuple[int, int], ...]]:
    masks = [
        ((0, 1), (1, 1)),
        ((1, 0), (1, 1)),
        ((0, 0), (1, 0), (1, 1)),
    ]
    return masks[:piece_count]


def _distinct_marker_masks(piece_count: int) -> list[tuple[tuple[int, int], ...]]:
    masks = [
        ((1, 1),),
        ((0, 1), (1, 1)),
        ((0, 0), (1, 0), (1, 1)),
    ]
    return masks[:piece_count]


def _build_grid(
    *,
    height: int,
    width: int,
    piece_count: int,
    container_top: bool,
    profile: int,
    ctx,
) -> list[list[int]]:
    dims = _piece_dimensions(piece_count)
    shared_marker = profile == 1 and piece_count >= 2
    color_count = 2 + piece_count + (1 if shared_marker else piece_count)
    color_rng = ctx.draw_rng("colors")
    colors = color_rng.sample(list(range(1, 10)), color_count)
    background, container_color = colors[:2]
    fill_colors = colors[2 : 2 + piece_count]
    marker_pool = colors[2 + piece_count :]
    marker_colors = [marker_pool[0]] * piece_count if shared_marker else marker_pool
    masks = (
        _shared_marker_masks(piece_count)
        if shared_marker
        else _distinct_marker_masks(piece_count)
    )

    for attempt in range(80):
        rng = ctx.draw_rng(f"layout:{attempt}")
        container_h, container_w = _container_dimensions(
            profile, piece_count, height, width, rng
        )
        max_piece_h = max(piece_h for piece_h, _ in dims)
        if container_top:
            container_r = 1
            piece_band_r = height - max_piece_h - 1
        else:
            container_r = height - container_h - 1
            piece_band_r = 1
        container_c = rng.randint(1, width - container_w - 1)

        piece_input_gap = 2
        piece_input_width = sum(piece_w for _, piece_w in dims) + piece_input_gap * (piece_count - 1)
        piece_start_c = rng.randint(1, width - piece_input_width - 1)

        anchor_gap = 1
        anchor_width = sum(piece_w for _, piece_w in dims) + anchor_gap * (piece_count - 1)
        anchor_start_c = rng.randint(0, container_w - anchor_width)
        anchor_offsets: list[tuple[int, int]] = []
        cursor = anchor_start_c
        for piece_h, piece_w in dims:
            anchor_row = rng.randint(0, container_h - piece_h)
            anchor_offsets.append((anchor_row, cursor))
            cursor += piece_w + anchor_gap

        grid = full_grid(height, width, background)
        for row in range(container_r, container_r + container_h):
            for col in range(container_c, container_c + container_w):
                grid[row][col] = container_color

        for index, ((piece_h, piece_w), mask, marker) in enumerate(
            zip(dims, masks, marker_colors)
        ):
            anchor_r, anchor_c = anchor_offsets[index]
            for local_r, local_c in mask:
                if local_r >= piece_h or local_c >= piece_w:
                    raise RuntimeError("marker mask does not fit piece dimensions")
                grid[container_r + anchor_r + local_r][container_c + anchor_c + local_c] = marker

            input_r = piece_band_r + (max_piece_h - piece_h)
            input_c = piece_start_c + sum(
                dims[j][1] + piece_input_gap for j in range(index)
            )
            for row in range(input_r, input_r + piece_h):
                for col in range(input_c, input_c + piece_w):
                    grid[row][col] = fill_colors[index]
            for local_r, local_c in mask:
                grid[input_r + local_r][input_c + local_c] = marker

        errors = self_check(grid)
        if errors:
            continue
        observed = observe_overrides(grid)
        expected = {
            "grid_h": height,
            "grid_w": width,
            "piece_count": piece_count,
            "container_top": container_top,
        }
        if observed != expected:
            continue
        return grid

    raise ValueError(
        "could not realize a unique marker-alignment scene for "
        f"{height}x{width}, piece_count={piece_count}, container_top={container_top}"
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    profile = sample_index % len(SCHEDULE_PROFILES)
    default_h, default_w, default_count, default_top = _profile_defaults(profile, difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    height = _draw_int_axis(ctx, "grid_h", 24, 30, default_h)
    width = _draw_int_axis(ctx, "grid_w", 24, 30, default_w)
    piece_count = _draw_int_axis(ctx, "piece_count", 1, 3, default_count)
    container_top = _draw_bool_axis(ctx, "container_top", default_top)
    return _build_grid(
        height=height,
        width=width,
        piece_count=piece_count,
        container_top=container_top,
        profile=profile,
        ctx=ctx,
    )
