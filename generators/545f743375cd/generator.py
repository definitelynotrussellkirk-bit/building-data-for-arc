"""Generator for ARC task 545f743375cd — copy a green blob by a marker vector.

A single red(2) marker and blue(1) marker define the displacement from red to
blue.  Every cell of one connected green(3) tetromino is copied by that vector
and recolored orange(7); the input also contains one irrelevant gray(5)
decoration.  Generated destinations are in bounds, disjoint, and empty.

The eight-slot sample schedule starts with all five canonical dimension/vector
profiles, then adds an up-left direction and smaller diagonal vectors.  Any four
consecutive samples contain multiple marker vectors and source placements, so a
materialized lesson cannot identify a fixed translation or fixed answer zone as
the rule.  The Racket program remains the output authority; ``rule_mirror`` is
only a pure audit/test mirror.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "545f743375cd"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"  # exact observable axes + structural checker + semantic schedule
# sha256[:12] of whitespace-normalized canonical program_solution.
RULE_HASH = "37534d4aa1ea"

SUMMARY = (
    "Use the displacement from the single red(2) marker to the single blue(1) "
    "marker. Copy every cell of the connected green(3) tetromino by that "
    "vector and paint the translated cells orange(7). Keep the green source, "
    "both markers, and the single irrelevant gray(5) decoration unchanged."
)

INVARIANTS = [
    "rectangular 9..16 by 10..16 task grid; generated axes use 10..16 by 11..16",
    "exactly one red(2) marker and one blue(1) marker",
    "exactly four 4-connected green(3) source cells",
    "the red-to-blue vector is non-zero and translates the whole source in bounds",
    "source and every in-bounds translated target cell are disjoint; in-bounds targets are background",
    "exactly one gray(5) decoration outside source, target, and markers",
]

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.50

# Exact vectors include the five canonical task vectors plus three generalized
# diagonal directions.  Names are intentionally recoverable from the grid.
VECTOR_PROFILES: dict[str, tuple[int, int]] = {
    "down_right_5_7": (5, 7),
    "down_left_5_7": (5, -7),
    "up_right_6_5": (-6, 5),
    "down_right_6_4": (6, 4),
    "up_right_6_7": (-6, 7),
    "up_left_5_6": (-5, -6),
    "down_left_4_5": (4, -5),
    "down_right_4_5": (4, 5),
}
_VECTOR_BY_VALUE = {value: name for name, value in VECTOR_PROFILES.items()}
CANONICAL_VECTORS = frozenset(
    ((5, 7), (5, -7), (-6, 5), (6, 4), (-6, 7))
)
CANONICAL_DIMS = frozenset(((10, 12), (9, 11), (10, 10), (11, 12), (10, 13)))

# All profiles are asymmetric connected tetrominoes with a <=3x3 footprint, so
# every shape remains compatible with every declared grid/vector boundary.
BLOB_SHAPES: dict[str, tuple[tuple[int, int], ...]] = {
    "hook_top": ((0, 0), (0, 1), (1, 0), (2, 0)),
    "zig_down": ((0, 0), (1, 0), (1, 1), (2, 1)),
    "hook_right": ((0, 0), (0, 1), (1, 1), (2, 1)),
    "hook_bottom": ((0, 0), (1, 0), (2, 0), (2, 1)),
    "tee_top": ((0, 0), (0, 1), (0, 2), (1, 1)),
    "tee_bottom": ((0, 1), (1, 0), (1, 1), (1, 2)),
    "zig_right": ((0, 0), (0, 1), (1, 1), (1, 2)),
    "cup": ((0, 0), (1, 0), (1, 1), (1, 2)),
}
_SHAPE_BY_VALUE = {tuple(sorted(value)): name for name, value in BLOB_SHAPES.items()}
MARKER_ANCHORS = ("edge", "interior")
DECORATION_ANCHORS = ("corner", "edge", "interior")

AXES = {
    "grid_h": {
        "type": "int",
        "default": "eight-slot canonical/general schedule",
        "valid": "10..16",
    },
    "grid_w": {
        "type": "int",
        "default": "eight-slot canonical/general schedule",
        "valid": "11..16",
    },
    "vector_profile": {
        "type": "str",
        "default": "eight-slot schedule",
        "valid": "down_right_5_7|down_left_5_7|up_right_6_5|down_right_6_4|up_right_6_7|up_left_5_6|down_left_4_5|down_right_4_5",
    },
    "blob_shape": {
        "type": "str",
        "default": "eight-slot schedule",
        "valid": "hook_top|zig_down|hook_right|hook_bottom|tee_top|tee_bottom|zig_right|cup",
    },
    "clip_profile": {
        "type": "str",
        "default": "alternating full/partial schedule",
        "valid": "full|partial",
    },
    "marker_anchor": {
        "type": "str",
        "default": "alternating edge/interior",
        "valid": "edge|interior",
    },
    "decoration_anchor": {
        "type": "str",
        "default": "corner/edge/interior schedule",
        "valid": "corner|edge|interior",
    },
}
_ALLOWED_OVERRIDES = frozenset(AXES)

# Slots 0..4 anchor the real canonical profiles.  Slots 5..7 widen direction,
# dimensions, marker placement, and decoration placement without changing the
# task grammar.
_SCHEDULE = (
    (10, 12, "down_right_5_7", "hook_top", "full", "edge", "corner"),
    (11, 12, "down_left_5_7", "zig_down", "partial", "interior", "corner"),
    (10, 13, "up_right_6_5", "hook_right", "partial", "edge", "corner"),
    (11, 12, "down_right_6_4", "hook_bottom", "full", "edge", "corner"),
    (10, 13, "up_right_6_7", "zig_down", "partial", "interior", "corner"),
    (12, 14, "up_left_5_6", "tee_top", "full", "edge", "edge"),
    (14, 15, "down_left_4_5", "tee_bottom", "partial", "interior", "interior"),
    (16, 16, "down_right_4_5", "cup", "full", "edge", "interior"),
)
SCHEDULE_PROFILES = tuple(range(len(_SCHEDULE)))
_NEIGHBORS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _band_name(difficulty: Any) -> str:
    if difficulty is None:
        return "medium"
    if difficulty in ("easy", "medium", "hard"):
        return str(difficulty)
    if isinstance(difficulty, (int, float)) and not isinstance(difficulty, bool):
        value = float(difficulty)
        if value < 0.34:
            return "easy"
        if value < 0.67:
            return "medium"
        return "hard"
    raise ValueError(f"unknown difficulty {difficulty!r}")


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - _ALLOWED_OVERRIDES)
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")
    for name, lo, hi in (("grid_h", 10, 16), ("grid_w", 11, 16)):
        if overrides.get(name) is not None:
            value = int(overrides[name])
            if not lo <= value <= hi:
                raise ValueError(f"{name}={value} outside {lo}..{hi}")
    if (
        overrides.get("vector_profile") is not None
        and overrides["vector_profile"] not in VECTOR_PROFILES
    ):
        raise ValueError(f"unknown vector_profile {overrides['vector_profile']!r}")
    if (
        overrides.get("blob_shape") is not None
        and overrides["blob_shape"] not in BLOB_SHAPES
    ):
        raise ValueError(f"unknown blob_shape {overrides['blob_shape']!r}")
    if (
        overrides.get("clip_profile") is not None
        and overrides["clip_profile"] not in ("full", "partial")
    ):
        raise ValueError("clip_profile must be full or partial")
    if (
        overrides.get("marker_anchor") is not None
        and overrides["marker_anchor"] not in MARKER_ANCHORS
    ):
        raise ValueError("marker_anchor must be edge or interior")
    if (
        overrides.get("decoration_anchor") is not None
        and overrides["decoration_anchor"] not in DECORATION_ANCHORS
    ):
        raise ValueError("decoration_anchor must be corner, edge, or interior")


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> int:
    del seed, difficulty
    return int(sample_index) % len(_SCHEDULE)


def _default_dimensions(slot: int, band: str) -> tuple[int, int]:
    h, w = _SCHEDULE[slot][0], _SCHEDULE[slot][1]
    if slot < 5:
        return h, w
    # Keep generalized slots difficulty-aware while preserving their profile.
    offsets = {"easy": (-2, -2), "medium": (0, 0), "hard": (0, 1)}[band]
    return max(10, min(16, h + offsets[0])), max(11, min(16, w + offsets[1]))


def _prepare_ctx(seed: int, sample_index: int, difficulty: Any, overrides: dict[str, Any]):
    band = _band_name(difficulty)
    slot = schedule_profile(seed, sample_index, difficulty)
    defaults = _SCHEDULE[slot]
    effective = dict(overrides)
    default_h, default_w = _default_dimensions(slot, band)
    effective.setdefault("grid_h", default_h)
    effective.setdefault("grid_w", default_w)
    effective.setdefault("vector_profile", defaults[2])
    effective.setdefault("blob_shape", defaults[3])
    effective.setdefault("clip_profile", defaults[4])
    effective.setdefault("marker_anchor", defaults[5])
    effective.setdefault("decoration_anchor", defaults[6])
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective,
    )
    return ctx, band, slot


def _is_edge(cell: tuple[int, int], h: int, w: int) -> bool:
    r, c = cell
    return r in (0, h - 1) or c in (0, w - 1)


def _anchor_kind(cell: tuple[int, int], h: int, w: int) -> str:
    r, c = cell
    if r in (0, h - 1) and c in (0, w - 1):
        return "corner"
    if _is_edge(cell, h, w):
        return "edge"
    return "interior"


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    values = tuple(cells)
    r0 = min(r for r, _ in values)
    c0 = min(c for _, c in values)
    return tuple(sorted((r - r0, c - c0) for r, c in values))


def _connected(cells: Iterable[tuple[int, int]]) -> bool:
    remaining = set(cells)
    if not remaining:
        return False
    seen = {next(iter(remaining))}
    stack = list(seen)
    while stack:
        r, c = stack.pop()
        for dr, dc in _NEIGHBORS:
            nb = (r + dr, c + dc)
            if nb in remaining and nb not in seen:
                seen.add(nb)
                stack.append(nb)
    return seen == remaining


def _shuffled(values: Iterable[Any], rng) -> list[Any]:
    result = list(values)
    rng.shuffle(result)
    return result


def _marker_candidates(
    h: int,
    w: int,
    vector: tuple[int, int],
    anchor: str,
    forbidden: set[tuple[int, int]],
    rng,
) -> list[tuple[tuple[int, int], tuple[int, int]]]:
    dr, dc = vector
    result = []
    for red_r in range(h):
        for red_c in range(w):
            red = (red_r, red_c)
            blue = (red_r + dr, red_c + dc)
            if not (0 <= blue[0] < h and 0 <= blue[1] < w):
                continue
            if red in forbidden or blue in forbidden:
                continue
            realized = "edge" if _is_edge(red, h, w) or _is_edge(blue, h, w) else "interior"
            if realized == anchor:
                result.append((red, blue))
    return _shuffled(result, rng)


def _decoration_candidates(
    h: int,
    w: int,
    anchor: str,
    forbidden: set[tuple[int, int]],
    rng,
) -> list[tuple[int, int]]:
    values = (
        (r, c)
        for r in range(h)
        for c in range(w)
        if (r, c) not in forbidden and _anchor_kind((r, c), h, w) == anchor
    )
    return _shuffled(values, rng)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    ctx, _band, _slot = _prepare_ctx(seed, sample_index, difficulty, overrides)
    h = ctx.draw_int("grid_h", 10, 16)
    w = ctx.draw_int("grid_w", 11, 16)
    vector_profile = ctx.draw_choice("vector_profile", tuple(VECTOR_PROFILES))
    blob_shape = ctx.draw_choice("blob_shape", tuple(BLOB_SHAPES))
    clip_profile = ctx.draw_choice("clip_profile", ("full", "partial"))
    marker_anchor = ctx.draw_choice("marker_anchor", MARKER_ANCHORS)
    decoration_anchor = ctx.draw_choice("decoration_anchor", DECORATION_ANCHORS)

    vector = VECTOR_PROFILES[vector_profile]
    local_shape = BLOB_SHAPES[blob_shape]
    shape_h = max(r for r, _ in local_shape) + 1
    shape_w = max(c for _, c in local_shape) + 1
    dr, dc = vector

    placement_rng = ctx.draw_rng("placement")
    marker_rng = ctx.draw_rng("markers")
    decoration_rng = ctx.draw_rng("decoration")
    origins = _shuffled(
        ((r, c) for r in range(0, h - shape_h + 1) for c in range(0, w - shape_w + 1)),
        placement_rng,
    )

    for top, left in origins:
        source = {(top + r, left + c) for r, c in local_shape}
        target = {(r + dr, c + dc) for r, c in source}
        in_bounds_target = {(r, c) for r, c in target if 0 <= r < h and 0 <= c < w}
        realized_clip = "full" if len(in_bounds_target) == len(source) else (
            "partial" if in_bounds_target else "all_out"
        )
        if realized_clip != clip_profile or source & in_bounds_target:
            continue
        for red, blue in _marker_candidates(
            h, w, vector, marker_anchor, source | in_bounds_target, marker_rng
        ):
            occupied = source | in_bounds_target | {red, blue}
            decorations = _decoration_candidates(
                h, w, decoration_anchor, occupied, decoration_rng
            )
            if not decorations:
                continue
            decoration = decorations[0]
            grid = full_grid(h, w, 0)
            for r, c in source:
                grid[r][c] = 3
            grid[red[0]][red[1]] = 2
            grid[blue[0]][blue[1]] = 1
            grid[decoration[0]][decoration[1]] = 5
            findings = self_check(grid, difficulty=difficulty)
            if not findings:
                return grid
    raise ValueError(
        "could not realize exact axis combination "
        f"grid={h}x{w}, vector={vector_profile}, shape={blob_shape}, "
        f"clip={clip_profile}, marker={marker_anchor}, decoration={decoration_anchor}"
    )


def _grid_errors(grid: Any) -> tuple[list[str], int, int]:
    if not isinstance(grid, list) or not grid or not all(isinstance(row, list) for row in grid):
        return ["grid must be a non-empty list of rows"], 0, 0
    h = len(grid)
    w = len(grid[0]) if grid[0] else 0
    errors: list[str] = []
    if w == 0 or any(len(row) != w for row in grid):
        errors.append("grid must be non-empty and rectangular")
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("grid cells must be ARC color integers 0..9")
    return errors, h, w


def semantic_observables(grid: Any) -> dict[str, Any]:
    errors, h, w = _grid_errors(grid)
    if errors:
        return {"errors": errors}
    positions = {
        color: [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color]
        for color in (1, 2, 3, 5)
    }
    ones, twos, threes, fives = positions[1], positions[2], positions[3], positions[5]
    facts: dict[str, Any] = {
        "errors": [],
        "grid_h": h,
        "grid_w": w,
        "ones": tuple(ones),
        "twos": tuple(twos),
        "source": tuple(threes),
        "decoration": tuple(fives),
        "blob_size": len(threes),
        "blob_connected": _connected(threes),
    }
    normalized = _normalize(threes) if threes else ()
    facts["blob_shape"] = _SHAPE_BY_VALUE.get(normalized, "other")
    if len(twos) == 1 and len(ones) == 1:
        vector = (ones[0][0] - twos[0][0], ones[0][1] - twos[0][1])
        target = {(r + vector[0], c + vector[1]) for r, c in threes}
        facts.update(
            {
                "vector": vector,
                "vector_profile": _VECTOR_BY_VALUE.get(vector, "other"),
                "target": tuple(sorted(target)),
                "in_bounds_target": tuple(sorted((r, c) for r, c in target if 0 <= r < h and 0 <= c < w)),
                "in_bounds_target_count": sum(0 <= r < h and 0 <= c < w for r, c in target),
                "clip_profile": ("full" if all(0 <= r < h and 0 <= c < w for r, c in target) else ("partial" if any(0 <= r < h and 0 <= c < w for r, c in target) else "all_out")),
                "marker_anchor": (
                    "edge"
                    if _is_edge(twos[0], h, w) or _is_edge(ones[0], h, w)
                    else "interior"
                ),
            }
        )
    if len(fives) == 1:
        facts["decoration_anchor"] = _anchor_kind(fives[0], h, w)
    return facts


def observe_overrides(grid: Any) -> dict[str, Any]:
    facts = semantic_observables(grid)
    if facts.get("errors"):
        raise ValueError("; ".join(facts["errors"]))
    if facts.get("vector_profile") not in VECTOR_PROFILES:
        raise ValueError("grid does not realize a declared vector_profile")
    if facts.get("blob_shape") not in BLOB_SHAPES:
        raise ValueError("grid does not realize a declared blob_shape")
    if facts.get("clip_profile") not in ("full", "partial"):
        raise ValueError("grid does not realize a declared clip_profile")
    if facts.get("marker_anchor") not in MARKER_ANCHORS:
        raise ValueError("grid does not realize a declared marker_anchor")
    if facts.get("decoration_anchor") not in DECORATION_ANCHORS:
        raise ValueError("grid does not realize a declared decoration_anchor")
    return {
        "grid_h": int(facts["grid_h"]),
        "grid_w": int(facts["grid_w"]),
        "vector_profile": str(facts["vector_profile"]),
        "blob_shape": str(facts["blob_shape"]),
        "clip_profile": str(facts["clip_profile"]),
        "marker_anchor": str(facts["marker_anchor"]),
        "decoration_anchor": str(facts["decoration_anchor"]),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Recognize the lawful task grammar and reject rule-hiding impostors."""
    del difficulty, meta
    errors, h, w = _grid_errors(grid)
    if errors:
        return errors
    if not 9 <= h <= 16 or not 10 <= w <= 16:
        errors.append(f"expected dimensions 9..16 by 10..16, got {h}x{w}")
    palette = {value for row in grid for value in row}
    unexpected = sorted(palette - {0, 1, 2, 3, 5})
    if unexpected:
        errors.append(f"unexpected input colors {unexpected}; orange(7) belongs only in output")

    positions = {
        color: [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color]
        for color in (1, 2, 3, 5)
    }
    ones, twos, threes, fives = positions[1], positions[2], positions[3], positions[5]
    if len(ones) != 1:
        errors.append(f"expected exactly one blue(1) marker, found {len(ones)}")
    if len(twos) != 1:
        errors.append(f"expected exactly one red(2) marker, found {len(twos)}")
    if len(threes) != 4:
        errors.append(f"expected exactly four green(3) source cells, found {len(threes)}")
    if threes and not _connected(threes):
        errors.append("green source must be one 4-connected object")
    if len(fives) != 1:
        errors.append(f"expected exactly one gray(5) decoration, found {len(fives)}")

    if len(ones) == 1 and len(twos) == 1 and threes:
        vector = (ones[0][0] - twos[0][0], ones[0][1] - twos[0][1])
        if vector not in _VECTOR_BY_VALUE:
            errors.append(f"marker vector {vector} is outside the declared teaching family")
        target = {(r + vector[0], c + vector[1]) for r, c in threes}
        in_bounds_target = {(r, c) for r, c in target if 0 <= r < h and 0 <= c < w}
        source = set(threes)
        if source & in_bounds_target:
            errors.append("green source and in-bounds translated target must be disjoint")
        blocked = sorted((r, c, grid[r][c]) for r, c in in_bounds_target if grid[r][c] != 0)
        if blocked:
            errors.append(
                "in-bounds translated target must be empty background; "
                f"found occupied cells {blocked[:3]}"
            )
    return errors


def strict_canonical_like(grid) -> list[str]:
    errors = self_check(grid)
    if errors:
        return errors
    facts = semantic_observables(grid)
    reasons: list[str] = []
    dims = (facts["grid_h"], facts["grid_w"])
    if dims not in CANONICAL_DIMS:
        reasons.append(f"dimensions {dims} are outside the five canonical profiles")
    if facts.get("vector") not in CANONICAL_VECTORS:
        reasons.append(f"vector {facts.get('vector')} is not canonical")
    if facts.get("decoration_anchor") != "corner":
        reasons.append("canonical decoration is a corner singleton")
    return reasons


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Pure Python audit mirror; the canonical Racket rule remains authoritative."""
    out = deepcopy(grid)
    red = next((r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2)
    blue = next((r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 1)
    dr, dc = blue[0] - red[0], blue[1] - red[1]
    h, w = len(grid), len(grid[0])
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == 3:
                nr, nc = r + dr, c + dc
                if 0 <= nr < h and 0 <= nc < w:
                    out[nr][nc] = 7
    return out


def _tuple_grid(grid: Any) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(int(value) for value in row) for row in grid)


def _vector_copy(
    grid: list[list[int]],
    vector: tuple[int, int],
    *,
    copy_color: int = 7,
    erase_source: bool = False,
    fill_bbox: bool = False,
    source_color: int = 3,
) -> list[list[int]]:
    out = deepcopy(grid)
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == source_color]
    if erase_source:
        for r, c in cells:
            out[r][c] = 0
    if fill_bbox and cells:
        r0, r1 = min(r for r, _ in cells), max(r for r, _ in cells)
        c0, c1 = min(c for _, c in cells), max(c for _, c in cells)
        cells = [(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)]
    h, w = len(grid), len(grid[0])
    for r, c in cells:
        nr, nc = r + vector[0], c + vector[1]
        if 0 <= nr < h and 0 <= nc < w:
            out[nr][nc] = copy_color
    return out


def _actual_vector(grid: list[list[int]]) -> tuple[int, int]:
    red = next((r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2)
    blue = next((r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 1)
    return blue[0] - red[0], blue[1] - red[1]


def _reverse_vector(grid: list[list[int]]) -> list[list[int]]:
    dr, dc = _actual_vector(grid)
    return _vector_copy(grid, (-dr, -dc))


def _fixed_vector(grid: list[list[int]]) -> list[list[int]]:
    return _vector_copy(grid, (5, 7))


def _move_instead_of_copy(grid: list[list[int]]) -> list[list[int]]:
    return _vector_copy(grid, _actual_vector(grid), erase_source=True)


def _recolor_source_only(grid: list[list[int]]) -> list[list[int]]:
    out = deepcopy(grid)
    for r, row in enumerate(out):
        for c, value in enumerate(row):
            if value == 3:
                out[r][c] = 7
    return out


def _copy_green_as_green(grid: list[list[int]]) -> list[list[int]]:
    return _vector_copy(grid, _actual_vector(grid), copy_color=3)


def _copy_decoration(grid: list[list[int]]) -> list[list[int]]:
    return _vector_copy(grid, _actual_vector(grid), source_color=5)


def _bbox_copy(grid: list[list[int]]) -> list[list[int]]:
    return _vector_copy(grid, _actual_vector(grid), fill_bbox=True)


def _marker_as_answer(grid: list[list[int]]) -> list[list[int]]:
    out = deepcopy(grid)
    blue = next((r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 1)
    out[blue[0]][blue[1]] = 7
    return out


def _count_only(grid: list[list[int]]) -> list[list[int]]:
    out = deepcopy(grid)
    count = sum(value == 3 for row in grid for value in row)
    written = 0
    for r, row in enumerate(out):
        for c, value in enumerate(row):
            if value == 0 and written < count:
                out[r][c] = 7
                written += 1
    return out


def _all_or_nothing(grid: list[list[int]]) -> list[list[int]]:
    vector = _actual_vector(grid)
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 3]
    h, w = len(grid), len(grid[0])
    if not all(0 <= r + vector[0] < h and 0 <= c + vector[1] < w for r, c in cells):
        return deepcopy(grid)
    return _vector_copy(grid, vector)


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "reverse_marker_vector": _reverse_vector,
    "fixed_vector_5_7": _fixed_vector,
    "move_instead_of_copy": _move_instead_of_copy,
    "recolor_source_only": _recolor_source_only,
    "copy_green_as_green": _copy_green_as_green,
    "copy_decoration_instead": _copy_decoration,
    "fill_translated_bbox": _bbox_copy,
    "blue_marker_is_answer": _marker_as_answer,
    "count_only_fixed_zone": _count_only,
    "all_or_nothing_translation": _all_or_nothing,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _witness(name: str) -> Callable[[list[list[int]]], bool]:
    return lambda grid: semantic_observables(grid).get(name) is not None


SEMANTIC_WITNESSES = {
    "lawful_transform": lambda grid: not self_check(grid),
    "down_right_vector": lambda grid: semantic_observables(grid).get("vector", (0, 0))[0] > 0
    and semantic_observables(grid).get("vector", (0, 0))[1] > 0,
    "down_left_vector": lambda grid: semantic_observables(grid).get("vector", (0, 0))[0] > 0
    and semantic_observables(grid).get("vector", (0, 0))[1] < 0,
    "up_right_vector": lambda grid: semantic_observables(grid).get("vector", (0, 0))[0] < 0
    and semantic_observables(grid).get("vector", (0, 0))[1] > 0,
    "up_left_vector": lambda grid: semantic_observables(grid).get("vector", (0, 0))[0] < 0
    and semantic_observables(grid).get("vector", (0, 0))[1] < 0,
    "non_reference_vector": lambda grid: semantic_observables(grid).get("vector") != (5, 7),
    "asymmetric_source": lambda grid: semantic_observables(grid).get("blob_shape") in BLOB_SHAPES,
    "full_translation": lambda grid: semantic_observables(grid).get("clip_profile") == "full",
    "partial_translation": lambda grid: semantic_observables(grid).get("clip_profile") == "partial",
    "marker_edge": lambda grid: semantic_observables(grid).get("marker_anchor") == "edge",
    "marker_interior": lambda grid: semantic_observables(grid).get("marker_anchor") == "interior",
    "decoration_corner": lambda grid: semantic_observables(grid).get("decoration_anchor") == "corner",
    "decoration_edge": lambda grid: semantic_observables(grid).get("decoration_anchor") == "edge",
    "decoration_interior": lambda grid: semantic_observables(grid).get("decoration_anchor") == "interior",
}

# Every witness carries a checked disagreement claim rather than merely counting
# morphology.  The named rival is selected to match the semantic cue.
WITNESS_RIVALS = {
    "lawful_transform": [
        "reverse_marker_vector",
        "move_instead_of_copy",
        "recolor_source_only",
        "copy_green_as_green",
        "blue_marker_is_answer",
        "count_only_fixed_zone",
    ],
    "down_right_vector": ["reverse_marker_vector"],
    "down_left_vector": ["reverse_marker_vector", "fixed_vector_5_7"],
    "up_right_vector": ["reverse_marker_vector", "fixed_vector_5_7"],
    "up_left_vector": ["reverse_marker_vector", "fixed_vector_5_7"],
    "non_reference_vector": ["fixed_vector_5_7"],
    "asymmetric_source": ["fill_translated_bbox"],
    "full_translation": ["reverse_marker_vector"],
    "partial_translation": ["all_or_nothing_translation"],
    "marker_edge": ["blue_marker_is_answer"],
    "marker_interior": ["blue_marker_is_answer"],
    "decoration_corner": ["copy_decoration_instead"],
    "decoration_edge": ["copy_decoration_instead"],
    "decoration_interior": ["copy_decoration_instead"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons where a named plausible rival survives the demonstrations."""
    if not isinstance(demos, list) or not demos:
        return ["lesson has no demonstrations"]
    survivors = set(LESSON_COMPETITORS)
    vectors: set[tuple[int, int]] = set()
    source_positions: set[tuple[tuple[int, int], ...]] = set()
    clip_profiles: set[str] = set()
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            return [f"demo {index} is malformed"]
        findings = self_check(pair["input"])
        if findings:
            return [f"demo {index} input fails self_check: {findings[:2]}"]
        official = _tuple_grid(pair["output"])
        survivors &= {
            name
            for name, competitor in LESSON_COMPETITORS.items()
            if _tuple_grid(competitor(pair["input"])) == official
        }
        facts = semantic_observables(pair["input"])
        vectors.add(tuple(facts["vector"]))
        source_positions.add(tuple(sorted(facts["source"])))
        clip_profiles.add(str(facts["clip_profile"]))

    reasons: list[str] = []
    if len(vectors) < 2:
        reasons.append("demos do not vary the marker vector")
    if len(source_positions) < 2:
        reasons.append("demos do not vary the green source position")
    if not {"full", "partial"}.issubset(clip_profiles):
        reasons.append("demos do not show both full and clipped translations")
    if survivors:
        reasons.append("named rival(s) fit every demo: " + ", ".join(sorted(survivors)))
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        reasons.append("query is malformed")
        return reasons
    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query input fails self_check: {query_errors[:2]}")
    return reasons


def mutation_fixtures() -> list[tuple[str, list[list[int]]]]:
    """Task-local near-misses that the structural checker must reject."""
    base = generate(99173, 2, difficulty="medium")

    missing_blue = deepcopy(base)
    for r, row in enumerate(missing_blue):
        for c, value in enumerate(row):
            if value == 1:
                missing_blue[r][c] = 0

    extra_red = deepcopy(base)
    for r, row in enumerate(extra_red):
        for c, value in enumerate(row):
            if value == 0:
                extra_red[r][c] = 2
                break
        else:
            continue
        break

    disconnected_blob = deepcopy(base)
    source = [(r, c) for r, row in enumerate(disconnected_blob) for c, value in enumerate(row) if value == 3]
    moved = source[-1]
    disconnected_blob[moved[0]][moved[1]] = 0
    for r in range(len(disconnected_blob) - 1, -1, -1):
        for c in range(len(disconnected_blob[0]) - 1, -1, -1):
            if disconnected_blob[r][c] != 0:
                continue
            if all(abs(r - r0) + abs(c - c0) > 1 for r0, c0 in source[:-1]):
                disconnected_blob[r][c] = 3
                break
        else:
            continue
        break

    missing_decoration = deepcopy(base)
    for r, row in enumerate(missing_decoration):
        for c, value in enumerate(row):
            if value == 5:
                missing_decoration[r][c] = 0

    occupied_target = deepcopy(base)
    facts = semantic_observables(occupied_target)
    decoration = tuple(facts["decoration"])[0]
    occupied_target[decoration[0]][decoration[1]] = 0
    target = tuple(facts["in_bounds_target"])[0]
    occupied_target[target[0]][target[1]] = 5

    orange_in_input = deepcopy(base)
    for r, row in enumerate(orange_in_input):
        for c, value in enumerate(row):
            if value == 0:
                orange_in_input[r][c] = 7
                break
        else:
            continue
        break

    return [
        ("missing_blue_marker", missing_blue),
        ("extra_red_marker", extra_red),
        ("disconnected_green_blob", disconnected_blob),
        ("missing_decoration", missing_decoration),
        ("decoration_recombined_into_target", occupied_target),
        ("orange_present_in_input", orange_in_input),
    ]
