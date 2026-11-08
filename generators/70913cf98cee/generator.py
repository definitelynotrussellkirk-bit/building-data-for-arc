"""Generator for Header Pair Recolor Map (70913cf98cee).

The first row is a left-to-right legend.  Ignoring zeros, consecutive legend
colors form ``source -> destination`` pairs.  The body contains sparse shapes
in every source color; applying the canonical Racket rule recolors those shapes
while preserving geometry, background, optional unmapped distractors, and the
legend row itself.
"""
from __future__ import annotations

from collections import deque

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "70913cf98cee"
VERSION = "3.0.0"
TASK_ID = "70913cf98cee"
RULE_HASH = "cfa85dd4cc66"
SUMMARY = (
    "A sparse same-size recoloring task. Row 0 contains two to four ordered "
    "source/destination color pairs, displayed as source, zero, destination "
    "triplets with an optional leading zero offset. Row 1 is a blank separator. "
    "Every source color appears in multiple body components below the separator. "
    "The output preserves row 0 and all geometry, replaces each body source color "
    "with its paired destination color, and leaves background plus at most one "
    "unmapped distractor color unchanged."
)

INVARIANTS = [
    "background is 0 and row 1 is a blank separator",
    "row 0 has an even reading-order sequence of 2..4 unique source/destination pairs",
    "every source color occurs in the body with at least one adjacent same-color pair",
    "destination colors do not occur in the generated body before recoloring",
    "the body is sparse and may contain at most one unmapped distractor color",
]

BODY_STYLES = ("canonical_shapes", "scattered", "mixed")
AXES = {
    "grid_h": {"type": "int", "default": "difficulty-aware", "valid": "7..12"},
    "grid_w": {"type": "int", "default": "difficulty-aware", "valid": "9..16"},
    "n_pairs": {"type": "int", "default": "2 easy, 2..3 medium, 3..4 hard", "valid": "2..4"},
    "header_offset": {"type": "int", "default": "0 easy, 0..1 medium, 0..2 hard", "valid": "0..2"},
    "n_neutral_colors": {"type": "int", "default": "0 easy, 0..1 otherwise", "valid": "0..1"},
    "body_style": {"type": "str", "default": "difficulty-aware", "valid": "|".join(BODY_STYLES)},
}

# Small connected motifs.  Every non-singleton motif contains a cardinally
# adjacent pair, which is a teaching-distribution invariant.
_DOMINOES = (
    ((0, 0), (0, 1)),
    ((0, 0), (1, 0)),
)
_TRIOMINOES = (
    ((0, 0), (0, 1), (1, 0)),
    ((0, 0), (0, 1), (1, 1)),
    ((0, 0), (1, 0), (1, 1)),
    ((0, 1), (1, 0), (1, 1)),
    ((0, 0), (0, 1), (0, 2)),
    ((0, 0), (1, 0), (2, 0)),
)


def _draw_default_int(ctx, label, lo, hi, *, override_lo, override_hi):
    """Consume a full-domain explicit override, else draw from a local band."""
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int(label, override_lo, override_hi)
    return ctx.draw_int(label, lo, hi)


def _difficulty_ranges(difficulty):
    if difficulty == "easy":
        return (2, 2), (0, 0), (0, 0), ("canonical_shapes", "scattered")
    if difficulty == "hard":
        return (3, 4), (0, 2), (0, 1), BODY_STYLES
    return (2, 3), (0, 1), (0, 1), BODY_STYLES


def _required_header_width(n_pairs: int, header_offset: int) -> int:
    # Last destination is at offset + 3*(n_pairs-1) + 2.
    return header_offset + 3 * n_pairs


def _place_component(grid, cells, color, rng, *, body_row0=2, attempts=400):
    """Place one motif without overlap or same-color component merging."""
    h, w = len(grid), len(grid[0])
    motif_h = max(r for r, _ in cells) + 1
    motif_w = max(c for _, c in cells) + 1
    if body_row0 + motif_h > h or motif_w > w:
        raise ValueError("grid too small for required body motif")

    anchors = [
        (r, c)
        for r in range(body_row0, h - motif_h + 1)
        for c in range(0, w - motif_w + 1)
    ]
    rng.shuffle(anchors)
    for anchor_r, anchor_c in anchors[:attempts]:
        placed = {(anchor_r + dr, anchor_c + dc) for dr, dc in cells}
        if any(grid[r][c] != 0 for r, c in placed):
            continue
        merges = False
        for r, c in placed:
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nr, nc = r + dr, c + dc
                if (nr, nc) not in placed and 0 <= nr < h and 0 <= nc < w:
                    if grid[nr][nc] == color:
                        merges = True
                        break
            if merges:
                break
        if merges:
            continue
        for r, c in placed:
            grid[r][c] = color
        return
    raise ValueError("unable to place required sparse component")


def _motifs_for_style(style, rng):
    if style == "canonical_shapes":
        return rng.choice(_TRIOMINOES), rng.choice(_DOMINOES)
    if style == "scattered":
        # One adjacent pair plus a separated singleton component.
        return rng.choice(_DOMINOES), ((0, 0),)
    if style == "mixed":
        return rng.choice(_TRIOMINOES + _DOMINOES), rng.choice(_DOMINOES + (((0, 0),),))
    raise ValueError(f"unknown body_style {style!r}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    pair_range, offset_range, neutral_range, style_options = _difficulty_ranges(difficulty)

    # Consume an explicit width first so ordinary defaults can remain compatible
    # with a caller-requested narrow canvas.  Mixed explicit incompatibilities
    # reject below rather than silently clamping either axis.
    if "grid_w" in overrides and overrides["grid_w"] is not None:
        w = ctx.draw_int("grid_w", 9, 16)
    else:
        w = None

    if "n_pairs" in overrides and overrides["n_pairs"] is not None:
        n_pairs = ctx.draw_int("n_pairs", 2, 4)
    else:
        lo, hi = pair_range
        if w is not None:
            hi = min(hi, w // 3)
            lo = min(lo, hi)
        if hi < 2:
            raise ValueError("grid_w cannot fit the minimum two legend pairs")
        n_pairs = ctx.draw_int("n_pairs", max(2, lo), max(2, hi))

    if "header_offset" in overrides and overrides["header_offset"] is not None:
        header_offset = ctx.draw_int("header_offset", 0, 2)
    else:
        lo, hi = offset_range
        if w is not None:
            hi = min(hi, w - 3 * n_pairs)
        if hi < 0:
            raise ValueError("grid_w and n_pairs leave no room for the header")
        header_offset = ctx.draw_int("header_offset", lo, max(lo, hi))

    required_w = _required_header_width(n_pairs, header_offset)
    if required_w > 16:
        raise ValueError(
            f"n_pairs={n_pairs} and header_offset={header_offset} require width {required_w} > 16"
        )
    if w is None:
        w = ctx.draw_int_diff("grid_w", max(9, required_w), 16)
    elif required_w > w:
        raise ValueError(
            f"grid_w={w} cannot fit n_pairs={n_pairs} with header_offset={header_offset}"
        )

    h = ctx.draw_int_diff("grid_h", 7, 12)
    n_neutral = _draw_default_int(
        ctx,
        "n_neutral_colors",
        neutral_range[0],
        neutral_range[1],
        override_lo=0,
        override_hi=1,
    )
    if "body_style" in overrides and overrides["body_style"] is not None:
        body_style = ctx.draw_choice("body_style", BODY_STYLES)
    else:
        body_style = ctx.draw_choice("body_style", style_options)

    needed_colors = 2 * n_pairs + n_neutral
    if needed_colors > 9:
        raise ValueError("legend plus neutral colors exceed ARC palette 1..9")
    palette_rng = ctx.draw_rng("palette")
    colors = palette_rng.sample(list(range(1, 10)), needed_colors)
    pairs = [(colors[2 * i], colors[2 * i + 1]) for i in range(n_pairs)]
    neutral_colors = colors[2 * n_pairs :]

    grid = full_grid(h, w, 0)
    for i, (src, dst) in enumerate(pairs):
        start = header_offset + 3 * i
        grid[0][start] = src
        grid[0][start + 2] = dst

    layout_rng = ctx.draw_rng(f"layout:{body_style}")
    for src, _dst in pairs:
        for motif in _motifs_for_style(body_style, layout_rng):
            _place_component(grid, motif, src, layout_rng)
    for neutral in neutral_colors:
        _place_component(grid, layout_rng.choice(_DOMINOES), neutral, layout_rng)

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise ValueError("internal generator postcondition failed: " + "; ".join(errors))
    return grid


def _header_pairs(grid):
    nonzero = [value for value in grid[0] if value != 0]
    if len(nonzero) % 2:
        return []
    return [(nonzero[i], nonzero[i + 1]) for i in range(0, len(nonzero), 2)]


def _components4(grid, color, *, row0=2):
    remaining = {
        (r, c)
        for r in range(row0, len(grid))
        for c in range(len(grid[0]))
        if grid[r][c] == color
    }
    components = []
    while remaining:
        start = remaining.pop()
        queue = deque([start])
        component = {start}
        while queue:
            r, c = queue.popleft()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nxt = (r + dr, c + dc)
                if nxt in remaining:
                    remaining.remove(nxt)
                    component.add(nxt)
                    queue.append(nxt)
        components.append(component)
    return components


def observe_overrides(grid):
    """Recover every exact semantic axis directly from a returned grid."""
    pairs = _header_pairs(grid)
    legend_colors = {color for pair in pairs for color in pair}
    body_colors = {
        grid[r][c]
        for r in range(2, len(grid))
        for c in range(len(grid[0]))
        if grid[r][c] != 0
    }
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_pairs": len(pairs),
        "header_offset": next((i for i, v in enumerate(grid[0]) if v != 0), 0),
        "n_neutral_colors": len(body_colors - legend_colors),
    }


def semantic_observables(grid):
    """Task-linked observables used by the focused census and review tests."""
    pairs = _header_pairs(grid)
    sources = [src for src, _ in pairs]
    destinations = [dst for _, dst in pairs]
    source_counts = {
        src: sum(row.count(src) for row in grid[2:])
        for src in sources
    }
    source_components = {
        src: sorted(len(component) for component in _components4(grid, src))
        for src in sources
    }
    body_colors = {
        value for row in grid[2:] for value in row if value != 0
    }
    legend_colors = set(sources) | set(destinations)
    return {
        **observe_overrides(grid),
        "sources": sources,
        "destinations": destinations,
        "source_counts": source_counts,
        "source_components": source_components,
        "neutral_colors": sorted(body_colors - legend_colors),
        "destination_cells_in_body": sum(
            value in set(destinations) for row in grid[2:] for value in row
        ),
        "changed_cells": sum(source_counts.values()),
        "header_nonzero_positions": [i for i, value in enumerate(grid[0]) if value],
        "separator_blank": all(value == 0 for value in grid[1]),
    }


def self_check(grid, *, difficulty=None, meta=None):
    """Reject malformed or shortcut-prone lessons; accept all canonical inputs."""
    errors = []
    if not isinstance(grid, list) or len(grid) < 3 or not isinstance(grid[0], list):
        return ["grid must have at least three rectangular rows"]
    w = len(grid[0])
    if w == 0 or any(not isinstance(row, list) or len(row) != w for row in grid):
        return ["grid is empty or ragged"]
    if any(
        not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 9
        for row in grid for value in row
    ):
        errors.append("grid contains a non-ARC color")
    if not all(value == 0 for value in grid[1]):
        errors.append("row 1 must be a blank separator")

    header = [value for value in grid[0] if value != 0]
    if len(header) % 2:
        errors.append("header has an odd number of nonzero legend entries")
    if not 4 <= len(header) <= 8:
        errors.append(f"header must encode 2..4 pairs, found {len(header) // 2}")
    if len(set(header)) != len(header):
        errors.append("all source and destination legend colors must be unique")
    if errors:
        return errors

    pairs = [(header[i], header[i + 1]) for i in range(0, len(header), 2)]
    sources = [src for src, _ in pairs]
    destinations = {dst for _, dst in pairs}
    body = [value for row in grid[2:] for value in row]
    body_nonzero = [value for value in body if value != 0]
    if not body_nonzero:
        errors.append("body has no colored cells")
        return errors
    if len(body_nonzero) > max(24, int(0.45 * len(body))):
        errors.append("body is too dense for the sparse canonical grammar")
    if body.count(0) < 2:
        errors.append("body must retain background cells")
    if any(value in destinations for value in body_nonzero):
        errors.append("destination colors must not appear in the input body")

    neutral_colors = set(body_nonzero) - set(sources) - destinations
    if len(neutral_colors) > 1:
        errors.append("body has more than one unmapped distractor color")
    for neutral in neutral_colors:
        if body_nonzero.count(neutral) < 2:
            errors.append("an unmapped distractor must form a visible multi-cell witness")

    for src in sources:
        count = body_nonzero.count(src)
        if count < 3:
            errors.append(f"source color {src} appears only {count} times in the body")
            continue
        if not any(len(component) >= 2 for component in _components4(grid, src)):
            errors.append(f"source color {src} has no adjacent same-color body witness")
    return errors
