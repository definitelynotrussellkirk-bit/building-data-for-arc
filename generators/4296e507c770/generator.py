"""Generator for ARC task 4296e507c770 — transform-coded stamps.

A single color-2 object is the stamp template, normalized to the top-left of
its bounding box.  Every isolated marker anchors a color-8 copy of that
shape on a blank output grid.  Marker colors select the transform:
3 = identity, 4 = horizontal mirror, 5 = vertical mirror, 6 = rotate clockwise.

Every ordinary generated example includes all four marker codes and a connected
asymmetric template that separates identity, both mirrors, clockwise rotation,
and counter-clockwise rotation.  Thus each example is useful evidence for the
code map rather than merely a lawful but ambiguous instance.
"""
from __future__ import annotations

from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "4296e507c770"
TASK_ID = GENERATOR_ID
RULE_HASH = "6c9be515e84b"
VERSION = "3.0.0"
EXAMPLES_NEEDED = 2

SUMMARY = (
    "Find the connected color-2 template.  At every isolated marker, stamp a "
    "color-8 copy on a blank same-size grid: 3 keeps the template, 4 mirrors "
    "left-right, 5 mirrors up-down, and 6 rotates clockwise."
)

INVARIANTS = [
    "background is 0 and the input uses only colors 0, 2, 3, 4, 5, and 6",
    "there is one connected color-2 template containing 4-9 cells inside 4x4",
    "marker colors 3, 4, 5, and 6 all occur; there are 4-6 isolated markers",
    "every marker's transformed stamp fits in the same-size output grid",
]

AXES = {
    "grid_h": {"type": "int", "default": "scheduled", "valid": "12..22"},
    "grid_w": {"type": "int", "default": "scheduled", "valid": "14..24"},
    "template_size": {"type": "int", "default": "difficulty-aware 4..9", "valid": "4..9"},
    "n_markers": {"type": "int", "default": "difficulty-aware 4..6", "valid": "4..6"},
}

# Every cross-product of declared boundary values is constructible.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, Any], ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()

SCHEDULE_PROFILES = ("canonical_12", "canonical_13", "broad")
MIN_STRICT_FRAC = 0.50

_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_MARKER_COLORS = (3, 4, 5, 6)
_ALLOWED_COLORS = {0, 2, 3, 4, 5, 6}

# Connected, <=4x4, and separating for identity/lr/ud/cw/ccw.
_FALLBACK_SHAPES: dict[int, tuple[tuple[int, int], ...]] = {
    4: ((0, 0), (0, 1), (0, 2), (1, 0)),
    5: ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0)),
    6: ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1)),
    7: ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 2)),
    8: ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 2), (2, 0)),
    9: ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 2), (1, 3), (2, 0)),
}


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Stable three-cycle with both canonical dimension profiles in every cycle."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    points = tuple(cells)
    if not points:
        return ()
    top = min(r for r, _ in points)
    left = min(c for _, c in points)
    return tuple(sorted((r - top, c - left) for r, c in points))


def _transform(
    cells: Iterable[tuple[int, int]], operation: str
) -> tuple[tuple[int, int], ...]:
    points = _normalize(cells)
    if not points:
        return ()
    height = max(r for r, _ in points) + 1
    width = max(c for _, c in points) + 1
    transformed: list[tuple[int, int]] = []
    for r, c in points:
        if operation == "flip_lr":
            point = (r, width - 1 - c)
        elif operation == "flip_ud":
            point = (height - 1 - r, c)
        elif operation == "rotate_cw":
            point = (c, height - 1 - r)
        elif operation == "rotate_ccw":
            point = (width - 1 - c, r)
        else:
            point = (r, c)
        transformed.append(point)
    return _normalize(transformed)


_OPERATION_FOR_COLOR = {
    3: "identity",
    4: "flip_lr",
    5: "flip_ud",
    6: "rotate_cw",
}


def _signatures(shape: Iterable[tuple[int, int]]) -> dict[str, tuple[tuple[int, int], ...]]:
    return {
        operation: _transform(shape, operation)
        for operation in ("identity", "flip_lr", "flip_ud", "rotate_cw", "rotate_ccw")
    }


def _is_transform_separating(shape: Iterable[tuple[int, int]]) -> bool:
    values = tuple(_signatures(shape).values())
    return len(set(values)) == len(values)


def _random_shape(rng: Any, size: int) -> tuple[tuple[int, int], ...]:
    """Draw an exact-size connected shape whose five relevant transforms differ."""
    for _ in range(200):
        cells = {(0, 0)}
        attempts = 0
        while len(cells) < size and attempts < 1000:
            attempts += 1
            r, c = rng.choice(sorted(cells))
            dr, dc = rng.choice(_CARDINAL)
            trial = set(cells)
            trial.add((r + dr, c + dc))
            normalized = _normalize(trial)
            if max(rr for rr, _ in normalized) < 4 and max(cc for _, cc in normalized) < 4:
                cells = trial
        if len(cells) == size:
            shape = _normalize(cells)
            if _is_transform_separating(shape):
                return shape
    return _FALLBACK_SHAPES[size]


def _axis_int(ctx: Any, label: str, low: int, high: int, default: int) -> int:
    """Record scheduled defaults while honoring every exact declared override."""
    if label in ctx.overrides:
        return ctx.draw_int(label, low, high)
    return ctx.draw_int(label, default, default)


def _validate_request(difficulty: Any, overrides: dict[str, Any]) -> dict[str, int]:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")
    bounds = {
        "grid_h": (12, 22),
        "grid_w": (14, 24),
        "template_size": (4, 9),
        "n_markers": (4, 6),
    }
    clean: dict[str, int] = {}
    for name, value in overrides.items():
        if value is None:
            continue
        low, high = bounds[name]
        if type(value) is not int or not low <= value <= high:
            raise ValueError(f"{name} must be an integer in {low}..{high}")
        clean[name] = value
    return clean


def _scheduled_defaults(profile: str, difficulty: Any, rng: Any) -> tuple[int, int, int, int]:
    if profile == "canonical_12":
        return 12, 18, 5, 4
    if profile == "canonical_13":
        return 13, 18, 5, 4
    if difficulty == "easy":
        return rng.randint(12, 15), rng.randint(14, 18), rng.randint(4, 5), 4
    if difficulty == "hard":
        return rng.randint(18, 22), rng.randint(20, 24), rng.randint(7, 9), 6
    return rng.randint(14, 19), rng.randint(16, 21), rng.randint(5, 7), rng.randint(4, 5)


def _construct_layout(
    rng: Any,
    height: int,
    width: int,
    shape: tuple[tuple[int, int], ...],
    marker_colors: list[int],
) -> tuple[list[tuple[int, int, int]], tuple[int, int]]:
    """Pack clean footprints quickly, with exhaustive fallback for safety."""
    signatures = _signatures(shape)
    all_variants = tuple(signatures.values())
    all_variant_h = max(max(r for r, _ in offsets) + 1 for offsets in all_variants)
    all_variant_w = max(max(c for _, c in offsets) + 1 for offsets in all_variants)
    max_marker_row = height - all_variant_h
    max_marker_col = width - all_variant_w
    shape_h = max(r for r, _ in shape) + 1
    shape_w = max(c for _, c in shape) + 1

    def conflicts(
        row: int,
        col: int,
        footprint: set[tuple[int, int]] | frozenset[tuple[int, int]],
        selected: list[tuple[int, int, set[tuple[int, int]] | frozenset[tuple[int, int]]]],
    ) -> bool:
        for prev_row, prev_col, prev_footprint in selected:
            if abs(row - prev_row) + abs(col - prev_col) <= 1:
                return True
            if (
                footprint & prev_footprint
                or (row, col) in prev_footprint
                or (prev_row, prev_col) in footprint
            ):
                return True
        return False

    def template_position(
        selected: list[tuple[int, int, set[tuple[int, int]] | frozenset[tuple[int, int]]]],
        used_footprints: set[tuple[int, int]] | frozenset[tuple[int, int]],
        *,
        random_tries: int,
    ) -> tuple[int, int] | None:
        anchors = {(row, col) for row, col, _ in selected}

        def valid(row: int, col: int) -> bool:
            cells = {(row + dr, col + dc) for dr, dc in shape}
            if cells & used_footprints or cells & anchors:
                return False
            return not any(
                (anchor_r + dr, anchor_c + dc) in cells
                for anchor_r, anchor_c in anchors
                for dr, dc in _CARDINAL
            )

        for _ in range(random_tries):
            row = rng.randint(0, height - shape_h)
            col = rng.randint(0, width - shape_w)
            if valid(row, col):
                return row, col
        for row in range(height - shape_h + 1):
            for col in range(width - shape_w + 1):
                if valid(row, col):
                    return row, col
        return None

    # The ordinary path samples only the handful of candidates it needs.  The
    # former implementation shuffled every legal anchor (hundreds per marker),
    # making the 33k-draw override gate exceed its five-minute stage budget.
    for _layout_attempt in range(48):
        selected: list[tuple[int, int, set[tuple[int, int]]]] = []
        used: set[tuple[int, int]] = set()
        for color in marker_colors:
            offsets = signatures[_OPERATION_FOR_COLOR[color]]
            placed = False
            for _candidate_attempt in range(96):
                row = rng.randint(0, max_marker_row)
                col = rng.randint(0, max_marker_col)
                footprint = {(row + dr, col + dc) for dr, dc in offsets}
                if conflicts(row, col, footprint, selected):
                    continue
                selected.append((row, col, footprint))
                used.update(footprint)
                placed = True
                break
            if not placed:
                break
        if len(selected) != len(marker_colors):
            continue
        template = template_position(selected, used, random_tries=96)
        if template is not None:
            markers = [
                (row, col, marker_colors[index])
                for index, (row, col, _) in enumerate(selected)
            ]
            return markers, template

    # Deterministic exhaustive fallback: expected to be unreachable for the
    # declared domain, but keeps every legal boundary combination constructive.
    candidates_by_marker: list[list[tuple[int, int, frozenset[tuple[int, int]]]]] = []
    for color in marker_colors:
        offsets = signatures[_OPERATION_FOR_COLOR[color]]
        candidates = []
        for row in range(max_marker_row + 1):
            for col in range(max_marker_col + 1):
                footprint = frozenset((row + dr, col + dc) for dr, dc in offsets)
                candidates.append((row, col, footprint))
        candidates_by_marker.append(candidates)

    nodes = 0
    node_limit = 100_000

    def search(
        index: int,
        selected: list[tuple[int, int, frozenset[tuple[int, int]]]],
        used_footprints: frozenset[tuple[int, int]],
    ) -> tuple[list[tuple[int, int, int]], tuple[int, int]] | None:
        nonlocal nodes
        if index == len(marker_colors):
            template = template_position(selected, used_footprints, random_tries=0)
            if template is None:
                return None
            markers = [
                (row, col, marker_colors[i])
                for i, (row, col, _) in enumerate(selected)
            ]
            return markers, template

        for candidate in candidates_by_marker[index]:
            nodes += 1
            if nodes > node_limit:
                return None
            row, col, footprint = candidate
            if conflicts(row, col, footprint, selected):
                continue
            result = search(
                index + 1,
                selected + [candidate],
                used_footprints | footprint,
            )
            if result is not None:
                return result
        return None

    result = search(0, [], frozenset())
    if result is None:
        raise RuntimeError(
            f"could not construct layout for {height}x{width}, "
            f"template_size={len(shape)}, n_markers={len(marker_colors)}"
        )
    return result

def generate(
    seed: int,
    sample_index: int,
    *,
    difficulty: Any = None,
    **overrides: Any,
) -> list[list[int]]:
    clean_overrides = _validate_request(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=clean_overrides,
    )
    rng = ctx.draw_rng("layout")
    profile = schedule_profile(seed, sample_index, difficulty)
    default_h, default_w, default_size, default_markers = _scheduled_defaults(
        profile, difficulty, rng
    )
    height = _axis_int(ctx, "grid_h", 12, 22, default_h)
    width = _axis_int(ctx, "grid_w", 14, 24, default_w)
    template_size = _axis_int(ctx, "template_size", 4, 9, default_size)
    n_markers = _axis_int(ctx, "n_markers", 4, 6, default_markers)

    shape = _random_shape(rng, template_size)
    marker_colors = list(_MARKER_COLORS)
    marker_colors.extend(rng.choice(_MARKER_COLORS) for _ in range(n_markers - 4))
    rng.shuffle(marker_colors)
    markers, (template_row, template_col) = _construct_layout(
        rng, height, width, shape, marker_colors
    )

    grid = full_grid(height, width, 0)
    for dr, dc in shape:
        grid[template_row + dr][template_col + dc] = 2
    for row, col, color in markers:
        grid[row][col] = color
    return grid


def _components(cells: set[tuple[int, int]]) -> list[set[tuple[int, int]]]:
    remaining = set(cells)
    result: list[set[tuple[int, int]]] = []
    while remaining:
        seed = remaining.pop()
        component = {seed}
        stack = [seed]
        while stack:
            row, col = stack.pop()
            for dr, dc in _CARDINAL:
                neighbor = (row + dr, col + dc)
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    component.add(neighbor)
                    stack.append(neighbor)
        result.append(component)
    return result


def _analyze(grid: Any) -> dict[str, Any]:
    info: dict[str, Any] = {"errors": []}
    if not isinstance(grid, list) or not grid:
        info["errors"].append("grid must be a non-empty list of rows")
        return info
    if not isinstance(grid[0], list) or not grid[0]:
        info["errors"].append("grid rows must be non-empty lists")
        return info
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        info["errors"].append("grid must be rectangular")
        return info
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        info["errors"].append("grid values must be integer colors 0..9")
        return info

    height = len(grid)
    template_cells = {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 2
    }
    template_components = _components(template_cells)
    shape = _normalize(template_cells) if template_cells else ()
    markers = [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value in _MARKER_COLORS
    ]
    marker_colors = {value for _, _, value in markers}
    bbox_h = max((r for r, _ in shape), default=-1) + 1
    bbox_w = max((c for _, c in shape), default=-1) + 1
    other_nonzero = [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value not in _ALLOWED_COLORS
    ]
    info.update(
        {
            "grid_h": height,
            "grid_w": width,
            "template_cells": template_cells,
            "template_components": template_components,
            "template_size": len(template_cells),
            "shape": shape,
            "bbox_h": bbox_h,
            "bbox_w": bbox_w,
            "markers": markers,
            "marker_colors": marker_colors,
            "n_markers": len(markers),
            "other_nonzero": other_nonzero,
            "transform_signatures": _signatures(shape) if shape else {},
        }
    )
    return info


def observe_overrides(grid: Any) -> dict[str, int]:
    info = _analyze(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    return {
        "grid_h": int(info["grid_h"]),
        "grid_w": int(info["grid_w"]),
        "template_size": int(info["template_size"]),
        "n_markers": int(info["n_markers"]),
    }


def self_check(
    grid: Any,
    *,
    difficulty: Any = None,
    meta: dict[str, Any] | None = None,
) -> list[str]:
    del difficulty
    info = _analyze(grid)
    errors = list(info["errors"])
    if errors:
        return errors

    if info["other_nonzero"]:
        errors.append("input may contain only colors 0, 2, 3, 4, 5, and 6")
    if not 12 <= info["grid_h"] <= 22 or not 14 <= info["grid_w"] <= 24:
        errors.append("grid dimensions must be grid_h 12..22 and grid_w 14..24")
    if len(info["template_components"]) != 1:
        errors.append(
            f"expected exactly one connected color-2 template object, "
            f"got {len(info['template_components'])}"
        )
    if not 4 <= info["template_size"] <= 9:
        errors.append(f"template must contain 4-9 cells, got {info['template_size']}")
    if info["bbox_h"] > 4 or info["bbox_w"] > 4:
        errors.append("template bounding box must fit inside 4x4")
    if not 4 <= info["n_markers"] <= 6:
        errors.append(f"expected 4-6 transform markers, got {info['n_markers']}")
    if info["marker_colors"] != set(_MARKER_COLORS):
        errors.append("expected marker colors 3, 4, 5, and 6 at least once each")

    height, width = info["grid_h"], info["grid_w"]
    for marker_row, marker_col, color in info["markers"]:
        if any(
            0 <= marker_row + dr < height
            and 0 <= marker_col + dc < width
            and grid[marker_row + dr][marker_col + dc] != 0
            for dr, dc in _CARDINAL
        ):
            errors.append("marker cells must be 4-neighbor isolated in the input")
            break
        if info["shape"]:
            offsets = _transform(info["shape"], _OPERATION_FOR_COLOR[color])
            if any(
                not (0 <= marker_row + dr < height and 0 <= marker_col + dc < width)
                for dr, dc in offsets
            ):
                errors.append("every marker's transformed stamp must fit in bounds")
                break

    if meta and isinstance(meta, dict):
        requested = meta.get("overrides", meta)
        if isinstance(requested, dict):
            observed = observe_overrides(grid)
            for axis, value in requested.items():
                if axis in AXES and value is not None and observed[axis] != value:
                    errors.append(
                        f"{axis} requested {value!r}, observed {observed[axis]!r}"
                    )
    return errors


def strict_canonical_like(grid: Any) -> list[str]:
    info = _analyze(grid)
    reasons = self_check(grid)
    if reasons:
        return reasons
    if (info["grid_h"], info["grid_w"]) not in {(12, 18), (13, 18)}:
        reasons.append("canonical inputs are 12x18 or 13x18")
    if info["template_size"] != 5:
        reasons.append("canonical template contains exactly 5 cells")
    if info["n_markers"] != 4 or info["marker_colors"] != set(_MARKER_COLORS):
        reasons.append("canonical inputs contain one marker of each color 3-6")
    return reasons


def _facts(grid: Any) -> dict[str, Any]:
    info = _analyze(grid)
    errors = self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return info


def _mapped_output(
    grid: list[list[int]], mapping: dict[int, str]
) -> list[list[int]]:
    info = _facts(grid)
    output = full_grid(info["grid_h"], info["grid_w"], 0)
    for marker_row, marker_col, color in info["markers"]:
        for dr, dc in _transform(info["shape"], mapping[color]):
            output[marker_row + dr][marker_col + dc] = 8
    return output


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Pure Python mirror for semantic probes; Racket remains label authority."""
    return _mapped_output(grid, _OPERATION_FOR_COLOR)


def _identity_everywhere(grid: list[list[int]]) -> list[list[int]]:
    return _mapped_output(grid, {color: "identity" for color in _MARKER_COLORS})


def _swap_mirrors(grid: list[list[int]]) -> list[list[int]]:
    return _mapped_output(
        grid,
        {3: "identity", 4: "flip_ud", 5: "flip_lr", 6: "rotate_cw"},
    )


def _rotate_counterclockwise(grid: list[list[int]]) -> list[list[int]]:
    return _mapped_output(
        grid,
        {3: "identity", 4: "flip_lr", 5: "flip_ud", 6: "rotate_ccw"},
    )


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "ignore_marker_colors": _identity_everywhere,
    "swap_horizontal_vertical_mirrors": _swap_mirrors,
    "color6_rotates_counterclockwise": _rotate_counterclockwise,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {}


def _nonidentity_codes_witness(grid: Any) -> bool:
    info = _facts(grid)
    signatures = info["transform_signatures"]
    return info["marker_colors"] == set(_MARKER_COLORS) and all(
        signatures["identity"] != signatures[operation]
        for operation in ("flip_lr", "flip_ud", "rotate_cw")
    )


def _mirror_mapping_witness(grid: Any) -> bool:
    info = _facts(grid)
    signatures = info["transform_signatures"]
    return {4, 5} <= info["marker_colors"] and signatures["flip_lr"] != signatures["flip_ud"]


def _rotation_direction_witness(grid: Any) -> bool:
    info = _facts(grid)
    signatures = info["transform_signatures"]
    return 6 in info["marker_colors"] and signatures["rotate_cw"] != signatures["rotate_ccw"]


SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "nonidentity_marker_codes": _nonidentity_codes_witness,
    "horizontal_vertical_code_map": _mirror_mapping_witness,
    "clockwise_rotation_direction": _rotation_direction_witness,
}

WITNESS_RIVALS = {
    "nonidentity_marker_codes": ["ignore_marker_colors"],
    "horizontal_vertical_code_map": ["swap_horizontal_vertical_mirrors"],
    "clockwise_rotation_direction": ["color6_rotates_counterclockwise"],
}


def lesson_identifiable(
    demos: list[dict[str, Any]], query: dict[str, Any]
) -> list[str]:
    reasons: list[str] = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query["output"]:
                reasons.append(f"competing rule survives demonstrations: {name}")
    return reasons
