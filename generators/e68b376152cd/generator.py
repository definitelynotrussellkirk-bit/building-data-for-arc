"""Generator for e68b376152cd — crop, order, and center-pack objects.

A lawful scene contains two to five isolated monochrome objects on black.
The selected rule finds same-color 4-connected components, sorts them by the
left edge of their bounding boxes (top edge breaks ties), tightly crops every
component, and packs the crops left-to-right with one black separator column.
Shorter crops are vertically centered in the tallest crop's output row.

The default four-step schedule is linked to the four official input profiles.
Every four consecutive samples also expose the ordering, tight-crop, gap, and
vertical-centering choices needed to distinguish the selected rule from the
plausible shortcuts declared below. Exact overrides deliberately expose only
three honest, recoverable axes.
"""
from __future__ import annotations

from collections import deque
from typing import Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e68b376152cd"
TASK_ID = "e68b376152cd"
VERSION = "3.0.0"
RULE_HASH = "c90e481827fb"

SUMMARY = (
    "A 0-background grid contains 2-5 distinctly colored 4-connected objects. "
    "Sort objects by (bounding-box left column, bounding-box top row), tightly "
    "crop each object, and pack the crops horizontally with exactly one black "
    "column between neighbors. Vertically center every crop in an output whose "
    "height is the maximum crop height."
)

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.95

INVARIANTS = [
    "background is color 0 and all values are ARC colors 0..9",
    "there are 2-5 same-color 4-connected objects",
    "every object has a distinct nonzero color and a bounding box at most 3x3",
    "different-colored objects never touch orthogonally",
    "the default schedule cycles all four official (height,width,palette) profiles",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "sample_index cycles official heights 4,4,5,6",
        "valid": "4..8",
    },
    "grid_w": {
        "type": "int",
        "default": "sample_index cycles official widths 6,8,6,7",
        "valid": "6..12",
    },
    "n_objects": {
        "type": "int",
        "default": "sample_index cycles official object counts 2,3,3,4",
        "valid": "2..5",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

SCHEDULE_PROFILES = (
    "official_4x6_two",
    "official_4x8_three",
    "official_5x6_three",
    "official_6x7_four",
)
_PROFILE_AXES = {
    "official_4x6_two": (4, 6, 2),
    "official_4x8_three": (4, 8, 3),
    "official_5x6_three": (5, 6, 3),
    "official_6x7_four": (6, 7, 4),
}
# Official input profiles, represented as (height, width, total palette size).
_CANONICAL_PROFILES = frozenset({(4, 6, 3), (4, 8, 4), (5, 6, 4), (6, 7, 5)})

_DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Name the deterministic four-step teaching profile for audit replay."""
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _grid_errors(grid) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty row sequence"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid must have at least one column"]
    width = len(grid[0])
    errors: list[str] = []
    for index, row in enumerate(grid):
        if not isinstance(row, (list, tuple)) or len(row) != width:
            errors.append(f"row {index} is not rectangular width {width}")
            continue
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                errors.append("grid values must be integer ARC colors 0..9")
                return errors
    return errors


def _components(grid) -> list[dict[str, object]]:
    """Same-color 4-connected components, matching `(objects g 0)`."""
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    records: list[dict[str, object]] = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            queue = deque([(r, c)])
            seen.add((r, c))
            cells: set[tuple[int, int]] = set()
            while queue:
                rr, cc = queue.popleft()
                cells.add((rr, cc))
                for dr, dc in _DIR4:
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            rows = [rr for rr, _ in cells]
            cols = [cc for _, cc in cells]
            records.append({
                "color": color,
                "cells": cells,
                "bbox": (min(rows), min(cols), max(rows), max(cols)),
                "area": len(cells),
            })
    return records


def _crop(record: dict[str, object], *, fill_bbox: bool = False) -> list[list[int]]:
    r0, c0, r1, c1 = record["bbox"]  # type: ignore[misc]
    color = int(record["color"])
    cells = record["cells"]
    piece = full_grid(r1 - r0 + 1, c1 - c0 + 1, 0)
    if fill_bbox:
        return full_grid(r1 - r0 + 1, c1 - c0 + 1, color)
    for r, c in cells:  # type: ignore[assignment]
        piece[r - r0][c - c0] = color
    return piece


def _pack_records(
    records: Iterable[dict[str, object]],
    *,
    gap: int = 1,
    align: str = "center",
    fill_bbox: bool = False,
) -> list[list[int]]:
    pieces = [_crop(record, fill_bbox=fill_bbox) for record in records]
    if not pieces:
        return [[0]]
    height = max(len(piece) for piece in pieces)
    width = sum(len(piece[0]) for piece in pieces) + gap * (len(pieces) - 1)
    out = full_grid(height, width, 0)
    left = 0
    for piece in pieces:
        if align == "top":
            top = 0
        elif align == "bottom":
            top = height - len(piece)
        else:
            top = (height - len(piece)) // 2
        for r, row in enumerate(piece):
            for c, value in enumerate(row):
                if value != 0:
                    out[top + r][left + c] = value
        left += len(piece[0]) + gap
    return out


def _official_order(grid) -> list[dict[str, object]]:
    return sorted(_components(grid), key=lambda record: (
        record["bbox"][1],  # type: ignore[index]
        record["bbox"][0],  # type: ignore[index]
    ))


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Independent Python mirror of the selected canonical Racket rule."""
    if _grid_errors(grid):
        raise ValueError("rule_mirror expects a rectangular ARC grid")
    return _pack_records(_official_order(grid), gap=1, align="center")


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed scenes while accepting every authoritative input."""
    del difficulty, meta
    errors = _grid_errors(grid)
    if errors:
        return errors
    h, w = len(grid), len(grid[0])
    if not 4 <= h <= 8:
        errors.append(f"height {h} outside honest generator envelope 4..8")
    if not 6 <= w <= 12:
        errors.append(f"width {w} outside honest generator envelope 6..12")
    if all(value != 0 for row in grid for value in row):
        errors.append("scene has no black background cells")

    records = _components(grid)
    if not 2 <= len(records) <= 5:
        errors.append(f"expected 2..5 objects, found {len(records)}")
    colors = [int(record["color"]) for record in records]
    if len(colors) != len(set(colors)):
        errors.append("each object must use a distinct nonzero color")

    for index, record in enumerate(records):
        r0, c0, r1, c1 = record["bbox"]  # type: ignore[misc]
        bh, bw = r1 - r0 + 1, c1 - c0 + 1
        area = int(record["area"])
        if bh > 3 or bw > 3:
            errors.append(f"object {index} bbox {bh}x{bw} exceeds 3x3 teaching grammar")
        if not 1 <= area <= 6:
            errors.append(f"object {index} area {area} outside 1..6")

    # Different colors are still distinct Racket objects when touching, but the
    # teaching grammar keeps the visual segmentation unambiguous.
    touching = False
    for r in range(h):
        for c in range(w):
            value = grid[r][c]
            if value == 0:
                continue
            for dr, dc in ((1, 0), (0, 1)):
                nr, nc = r + dr, c + dc
                if 0 <= nr < h and 0 <= nc < w:
                    other = grid[nr][nc]
                    if other != 0 and other != value:
                        touching = True
                        break
            if touching:
                break
        if touching:
            break
    if touching:
        errors.append("different-colored objects touch orthogonally")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Recognize the linked official shape/palette profiles, not a loose envelope."""
    errors = self_check(grid)
    if errors:
        return errors
    palette_size = len({value for row in grid for value in row})
    signature = (len(grid), len(grid[0]), palette_size)
    if signature not in _CANONICAL_PROFILES:
        return [f"profile {signature} is outside the four official input profiles"]
    return []


def observe_overrides(grid) -> dict[str, int]:
    """Recover every exact declared axis from the returned scene."""
    errors = _grid_errors(grid)
    if errors:
        raise ValueError("cannot observe malformed grid: " + "; ".join(errors))
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_objects": len(_components(grid)),
    }


def _shifted_palette(rng, n: int) -> list[int]:
    """Distinct colors deliberately not monotone in left-to-right order."""
    chosen = sorted(rng.sample(list(range(1, 10)), n))
    shift = 1 + rng.randrange(n - 1)
    return chosen[shift:] + chosen[:shift]


def _paint_specs(
    h: int,
    w: int,
    specs: list[tuple[set[tuple[int, int]], int, int]],
    colors: list[int],
) -> list[list[int]]:
    grid = full_grid(h, w, 0)
    for (shape, top, left), color in zip(specs, colors):
        for dr, dc in shape:
            r, c = top + dr, left + dc
            if not (0 <= r < h and 0 <= c < w):
                raise ValueError("internal teaching template escaped the canvas")
            if grid[r][c] != 0:
                raise ValueError("internal teaching templates overlap")
            grid[r][c] = color
    return grid


def _default_scene(profile: str, rng) -> list[list[int]]:
    """Four canonical-profile templates with seed-driven lawful variation."""
    h, w, n = _PROFILE_AXES[profile]
    colors = _shifted_palette(rng, n)

    if profile == "official_4x6_two":
        left_shapes = (
            {(0, 0), (1, 0), (1, 1)},
            {(0, 1), (1, 0), (1, 1)},
            {(0, 0), (0, 1), (1, 0)},
            {(0, 0), (0, 1), (1, 1)},
        )
        right_shapes = tuple(left_shapes)
        specs = [
            (rng.choice(left_shapes), rng.choice((1, 2)), rng.choice((0, 1))),
            (rng.choice(right_shapes), 0, 4),
        ]
    elif profile == "official_4x8_three":
        tall = rng.choice((
            {(0, 0), (1, 0), (2, 0), (2, 1)},
            {(0, 1), (1, 1), (2, 0), (2, 1)},
        ))
        specs = [
            (tall, 0, rng.choice((0, 1))),
            ({(0, 0)}, 3, rng.choice((3, 4))),
            ({(0, 0), (0, 1)}, rng.choice((0, 1)), 6),
        ]
    elif profile == "official_5x6_three":
        hook = rng.choice((
            {(0, 0), (0, 1), (1, 0)},
            {(0, 0), (0, 1), (1, 1)},
        ))
        specs = [
            ({(0, 0)}, rng.choice((0, 1)), 0),
            ({(0, 0), (1, 0), (2, 0)}, 2, 2),
            (hook, rng.choice((0, 1)), 4),
        ]
    else:  # official_6x7_four
        tall_hook = rng.choice((
            {(0, 0), (1, 0), (2, 0), (2, 1)},
            {(0, 1), (1, 1), (2, 0), (2, 1)},
        ))
        specs = [
            (tall_hook, 3, 0),
            ({(0, 0)}, rng.choice((0, 1)), 2),
            ({(0, 0), (1, 0)}, rng.choice((3, 4)), 4),
            ({(0, 0), (1, 0), (2, 0)}, rng.choice((0, 1)), 6),
        ]
    grid = _paint_specs(h, w, specs, colors)
    errors = self_check(grid)
    if errors:
        raise ValueError("internal teaching template failed: " + "; ".join(errors))
    return grid


def _explicit_scene(h: int, w: int, n: int, rng) -> list[list[int]]:
    """Always-realizable exact-override scene using isolated checkerboard cells."""
    parity = rng.randrange(2)
    positions = [
        (r, c)
        for r in range(h)
        for c in range(w)
        if (r + c) % 2 == parity
    ]
    rng.shuffle(positions)
    if len(positions) < n:
        raise ValueError(f"cannot place {n} isolated objects on {h}x{w}")
    colors = _shifted_palette(rng, n)
    grid = full_grid(h, w, 0)
    # Sort selected positions only for stable color assignment; their geometric
    # placement remains seed-dependent because the selected set is shuffled.
    for (r, c), color in zip(sorted(positions[:n], key=lambda p: (p[1], p[0])), colors):
        grid[r][c] = color
    errors = self_check(grid)
    if errors:
        raise ValueError("exact override construction failed: " + "; ".join(errors))
    return grid


def _draw_exact_int(ctx, label: str, default: int, lo: int, hi: int) -> int:
    """Record a keyed exact-axis draw while honoring the full declared domain."""
    if ctx.overrides.get(label) is None:
        ctx.overrides[label] = default
    return ctx.draw_int(label, lo, hi)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override key(s): " + ", ".join(unknown))

    profile = schedule_profile(seed, sample_index, difficulty=difficulty)
    default_h, default_w, default_n = _PROFILE_AXES[profile]
    caller_pinned = any(value is not None for value in overrides.values())
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=dict(overrides),
    )
    h = _draw_exact_int(ctx, "grid_h", default_h, 4, 8)
    w = _draw_exact_int(ctx, "grid_w", default_w, 6, 12)
    n = _draw_exact_int(ctx, "n_objects", default_n, 2, 5)
    band_label = str(difficulty) if difficulty is not None else "default"
    rng = ctx.draw_rng(f"layout:{band_label}")

    if caller_pinned:
        return _explicit_scene(h, w, n, rng)
    return _default_scene(profile, rng)


# ---------------------------------------------------------------------------
# Task-linked semantic rivals and witnesses
# ---------------------------------------------------------------------------

def _identity(grid):
    return [list(row) for row in grid]


def _row_major(grid):
    records = sorted(_components(grid), key=lambda record: (
        record["bbox"][0], record["bbox"][1]  # type: ignore[index]
    ))
    return _pack_records(records)


def _color_order(grid):
    return _pack_records(sorted(_components(grid), key=lambda record: record["color"]))


def _area_ascending(grid):
    records = sorted(_components(grid), key=lambda record: (
        record["area"], record["bbox"][1], record["bbox"][0]  # type: ignore[index]
    ))
    return _pack_records(records)


def _area_descending(grid):
    records = sorted(_components(grid), key=lambda record: (
        -int(record["area"]), record["bbox"][1], record["bbox"][0]  # type: ignore[index]
    ))
    return _pack_records(records)


def _reverse_left_to_right(grid):
    return _pack_records(list(reversed(_official_order(grid))))


def _top_aligned(grid):
    return _pack_records(_official_order(grid), align="top")


def _bottom_aligned(grid):
    return _pack_records(_official_order(grid), align="bottom")


def _filled_bounding_boxes(grid):
    return _pack_records(_official_order(grid), fill_bbox=True)


def _no_separator(grid):
    return _pack_records(_official_order(grid), gap=0)


def _two_separators(grid):
    return _pack_records(_official_order(grid), gap=2)


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "identity": _identity,
    "row_major_order": _row_major,
    "sort_by_color": _color_order,
    "sort_by_area_ascending": _area_ascending,
    "sort_by_area_descending": _area_descending,
    "reverse_left_to_right": _reverse_left_to_right,
    "top_align": _top_aligned,
    "bottom_align": _bottom_aligned,
    "fill_bounding_boxes": _filled_bounding_boxes,
    "zero_column_gap": _no_separator,
    "two_column_gap": _two_separators,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _rival_witness(name: str):
    rival = SEMANTIC_RIVALS[name]

    def witness(grid) -> bool:
        return not self_check(grid) and rule_mirror(grid) != rival(grid)

    witness.__name__ = f"refutes_{name}"
    return witness


SEMANTIC_WITNESSES = {
    f"refutes_{name}": _rival_witness(name)
    for name in SEMANTIC_RIVALS
}
WITNESS_RIVALS = {
    f"refutes_{name}": [name]
    for name in SEMANTIC_RIVALS
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a materialized lesson if any declared rival survives the demos."""
    if not isinstance(demos, (list, tuple)) or not demos:
        return ["at least one demonstration pair is required"]
    reasons: list[str] = []
    pairs = [*demos, query]
    for index, pair in enumerate(pairs):
        role = f"demo {index}" if index < len(demos) else "query"
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"{role} is not an input/output pair")
            continue
        grammar_errors = strict_canonical_like(pair["input"])
        if grammar_errors:
            reasons.append(f"{role} input is outside linked grammar: {grammar_errors[0]}")
            continue
        if rule_mirror(pair["input"]) != pair["output"]:
            reasons.append(f"{role} output disagrees with selected rule")

    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return reasons
    for name, competitor in LESSON_COMPETITORS.items():
        try:
            survives = all(
                competitor(pair["input"]) == pair["output"]
                for pair in demos
            )
            changes_query = competitor(query["input"]) != query["output"]
        except Exception as exc:
            reasons.append(f"competitor {name!r} raised {type(exc).__name__}: {exc}")
            continue
        if survives and changes_query:
            reasons.append(
                f"competitor {name!r} matches every demo but changes the query answer"
            )
    return reasons


def mutation_fixtures():
    """Task-local malformed scenes that the structural grammar must reject."""
    blank = full_grid(4, 8, 0)

    one_object = [row[:] for row in blank]
    one_object[1][1] = 3
    one_object[2][1] = 3

    split_color = [row[:] for row in blank]
    split_color[0][0] = 4
    split_color[3][7] = 4

    touching_colors = [row[:] for row in blank]
    touching_colors[1][2] = 2
    touching_colors[1][3] = 7

    too_many = full_grid(4, 12, 0)
    for (r, c), color in zip(
        ((0, 0), (0, 2), (0, 4), (0, 6), (0, 8), (0, 10)),
        (1, 2, 3, 4, 5, 6),
    ):
        too_many[r][c] = color

    oversized = full_grid(6, 8, 0)
    for r in range(4):
        oversized[r][1] = 5
    oversized[5][6] = 8

    invalid_color = [row[:] for row in blank]
    invalid_color[0][0] = 10
    invalid_color[3][7] = 2

    return [
        ("blank", blank),
        ("only_one_object", one_object),
        ("same_color_split_into_two_objects", split_color),
        ("different_colors_touch_orthogonally", touching_colors),
        ("six_objects", too_many),
        ("object_bbox_taller_than_three", oversized),
        ("non_arc_color", invalid_color),
    ]
