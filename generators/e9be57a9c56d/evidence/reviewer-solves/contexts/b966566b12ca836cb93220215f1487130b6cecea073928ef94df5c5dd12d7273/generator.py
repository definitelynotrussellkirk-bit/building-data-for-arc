"""Generator for ARC task e9be57a9c56d.

A uniquely largest 8-connected component is the template.  Singleton markers
lie on one row or column; exactly one marker shares the template colour and
anchors a chain.  The selected Racket rule copies the template at positions
obtained from consecutive marker gaps and recolours each copy to its marker.

The default four-draw schedule anchors every canonical (height, width, palette)
profile and deliberately teaches two distinctions absent from the canonical
examples: the anchor colour need not be 2, and the anchor need not be an end
marker.  Exact public controls are intentionally limited to quantities that can
be recovered from the returned grid.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e9be57a9c56d"
TASK_ID = GENERATOR_ID
RULE_HASH = "f8100feef807"
VERSION = "3.0.0"
EXAMPLES_NEEDED = 3

SUMMARY = (
    "A largest template shape is anchored by the same-colour singleton among "
    "a row/column of markers. Consecutive marker gaps position recoloured "
    "template copies. The cyclic curriculum includes interior anchors and "
    "non-2 template colours while hitting all four canonical profiles."
)

INVARIANTS = [
    "the template is the uniquely largest same-colour 8-connected component",
    "every other component is a singleton marker",
    "markers lie on exactly one row or exactly one column and are at least two cells apart",
    "exactly one marker shares the template colour",
    "every derived non-anchor copy is wholly in-bounds and lands on background",
]

ORIENTATIONS = ("horizontal", "vertical")
AXES = {
    "orientation": {
        "type": "str",
        "default": "four-profile cyclic schedule",
        "valid": "horizontal|vertical",
    },
    "n_markers": {
        "type": "int",
        "default": "4 or 5 from canonical profile",
        "valid": "2..5",
    },
    "template_size": {
        "type": "int",
        "default": "6 or 7 from canonical profile",
        "valid": "3..7",
    },
    "anchor_pos": {
        "type": "int",
        "default": "cyclic first/interior/last schedule",
        "valid": "0..4",
    },
}

# Cross-axis requests with anchor_pos >= n_markers are intentionally rejected.
# Declaring the pair lets the shared override audit classify those rejections.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = (
    {"n_markers": None, "anchor_pos": None},
)

# Public semantic profiles are exactly the quantities recovered by the census.
SCHEDULE_PROFILES = (
    (23, 17, 4),
    (16, 22, 4),
    (23, 14, 4),
    (13, 24, 5),
)

# Internal construction metadata extends those public triples.
# (height, width, total palette size, orientation, marker count, template size)
_LAYOUT_SCHEDULE = (
    (23, 17, 4, "vertical", 4, 6),
    (16, 22, 4, "horizontal", 4, 7),
    (23, 14, 4, "vertical", 4, 7),
    (13, 24, 5, "horizontal", 5, 6),
)

# Any three of four consecutive draws contain an interior-anchor example.
_ANCHOR_PHASES = ("interior_left", "interior_right", "first", "last")

# Horizontal-base marker gaps. Vertical final grids are transposes of the same
# construction. Values vary by difficulty without changing canonical profiles.
_PROFILE_GAPS = {
    "easy": (
        (2, 3, 4),
        (2, 3, 3),
        (3, 2, 3),
        (2, 2, 3, 2),
    ),
    "medium": (
        (2, 4, 5),
        (3, 3, 4),
        (5, 3, 3),
        (3, 4, 3, 2),
    ),
    "hard": (
        (5, 4, 3),
        (4, 4, 4),
        (5, 5, 4),
        (4, 3, 3, 3),
    ),
}

# Connected supports with exact cardinality and horizontal-base width three.
# Reflections supply additional shapes while preserving the chain-axis width.
_SHAPES: dict[int, tuple[tuple[tuple[int, int], ...], ...]] = {
    3: (
        ((0, 0), (0, 1), (0, 2)),
    ),
    4: (
        ((0, 0), (0, 1), (0, 2), (1, 1)),
        ((0, 0), (1, 0), (1, 1), (1, 2)),
    ),
    5: (
        ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
        ((0, 0), (0, 1), (0, 2), (1, 0), (2, 0)),
    ),
    6: (
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0)),
        ((0, 0), (0, 1), (1, 1), (1, 2), (2, 0), (2, 1)),
    ),
    7: (
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1)),
        ((0, 0), (0, 1), (0, 2), (1, 1), (2, 0), (2, 1), (2, 2)),
    ),
}


class IncompatibleOverrides(ValueError):
    """Structured rejection understood by the shared override checker."""

    axes = ("n_markers", "anchor_pos")


def schedule_profile(seed: int, sample_index: int, difficulty: str | None = None) -> tuple[int, int, int]:
    """Public deterministic profile schedule used by tests/audits."""
    del seed, difficulty
    height, width, palette_size, _orientation, _n, _k = _LAYOUT_SCHEDULE[sample_index % 4]
    return height, width, palette_size


def _validate_public_inputs(seed: Any, sample_index: Any, difficulty: Any, overrides: dict[str, Any]) -> None:
    if type(seed) is not int:
        raise TypeError("seed must be an integer")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer")
    if difficulty not in {None, "easy", "medium", "hard"}:
        raise ValueError("difficulty must be easy, medium, or hard")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis: {', '.join(unknown)}")
    if "orientation" in overrides and overrides["orientation"] is not None:
        value = overrides["orientation"]
        if type(value) is not str or value not in ORIENTATIONS:
            raise ValueError(f"orientation must be one of {ORIENTATIONS}, got {value!r}")
    for name, lo, hi in (
        ("n_markers", 2, 5),
        ("template_size", 3, 7),
        ("anchor_pos", 0, 4),
    ):
        if name not in overrides or overrides[name] is None:
            continue
        value = overrides[name]
        if type(value) is not int:
            raise TypeError(f"{name} override must be an integer (not bool)")
        if not lo <= value <= hi:
            raise ValueError(f"{name} override {value} outside [{lo}, {hi}]")


def _draw_scheduled_int(ctx, label: str, lo: int, hi: int, scheduled: int) -> int:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int_strict(label, lo, hi)
    return ctx.draw_int_strict(label, scheduled, scheduled)


def _draw_scheduled_choice(ctx, label: str, choices: tuple[str, ...], scheduled: str) -> str:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_choice(label, choices)
    return ctx.draw_choice(label, (scheduled,))


def _anchor_for_phase(phase: str, n_markers: int) -> int:
    if phase == "first":
        return 0
    if phase == "last":
        return n_markers - 1
    if n_markers <= 2:
        return 0 if phase == "interior_left" else n_markers - 1
    if phase == "interior_left":
        return 1
    return n_markers - 2


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    values = tuple(cells)
    row0 = min(row for row, _ in values)
    col0 = min(col for _, col in values)
    return tuple(sorted((row - row0, col - col0) for row, col in values))


def _shape_for(size: int, rng, difficulty: str) -> tuple[tuple[int, int], ...]:
    options = _SHAPES[size]
    band_offset = {"easy": 0, "medium": 1, "hard": 2}[difficulty]
    shape = list(options[(rng.randrange(len(options)) + band_offset) % len(options)])
    max_row = max(row for row, _ in shape)
    if rng.randrange(2):
        shape = [(row, 2 - col) for row, col in shape]
    if rng.randrange(2):
        shape = [(max_row - row, col) for row, col in shape]
    return _normalize(shape)


def _palette(rng, *, palette_size: int, n_markers: int, template_is_two: bool) -> tuple[int, list[int]]:
    # At most n_markers foreground colours can be visible (template plus one
    # role per marker), so override cases with two markers use a smaller lawful
    # palette while default canonical-profile cases retain their exact size.
    foreground_count = min(palette_size - 1, n_markers)
    non_two = [1, 3, 4, 5, 6, 7, 8, 9]
    rng.shuffle(non_two)
    if template_is_two:
        template_color = 2
        other_colors = non_two[: foreground_count - 1]
    else:
        template_color = non_two.pop()
        other_colors = [2, *non_two[: foreground_count - 2]]
    return template_color, other_colors


def _marker_colors(n_markers: int, anchor: int, template_color: int, other_colors: list[int]) -> list[int]:
    colors = [template_color] * n_markers
    positions = [index for index in range(n_markers) if index != anchor]
    if not other_colors:
        raise ValueError("at least one non-template marker color is required")
    # Use every other palette colour once. If positions remain, repeat the last
    # non-2 colour where possible so a non-2 template has exactly one color-2
    # marker, making the fixed-color shortcut's disagreement unambiguous.
    assignments = list(other_colors)
    filler = next((color for color in reversed(other_colors) if color != 2), other_colors[-1])
    assignments.extend([filler] * (len(positions) - len(assignments)))
    for position, color in zip(positions, assignments):
        colors[position] = color
    return colors


def _offsets(n_markers: int, anchor: int, gaps: tuple[int, ...], template_w: int) -> list[int]:
    offsets = [0] * n_markers
    for index in range(anchor + 1, n_markers):
        offsets[index] = offsets[index - 1] + template_w - 1 + gaps[index - 1]
    for index in range(anchor - 1, -1, -1):
        offsets[index] = offsets[index + 1] - template_w + 1 - gaps[index]
    return offsets


def _custom_gaps(
    n_markers: int, rng, difficulty: str, template_w: int
) -> tuple[int, ...]:
    ranges = {"easy": (2, 3), "medium": (2, 4), "hard": (3, 5)}
    lo, hi = ranges[difficulty]
    gaps = [rng.randint(lo, hi) for _ in range(n_markers - 1)]
    # Leave two columns of placement slack. Shrinking the largest gap first
    # preserves every exact public axis while making all valid single-axis
    # requests constructive inside ARC's 30-column limit.
    def chain_span() -> int:
        return template_w + sum(template_w - 1 + gap for gap in gaps)

    while chain_span() > 28:
        index = max(range(len(gaps)), key=gaps.__getitem__)
        if gaps[index] <= 2:
            raise ValueError("requested marker/template axes cannot fit in 30 columns")
        gaps[index] -= 1
    return tuple(gaps)


def _fit_custom_dimensions(shape: tuple[tuple[int, int], ...], gaps: tuple[int, ...]) -> tuple[int, int]:
    template_h = max(row for row, _ in shape) + 1
    template_w = max(col for _, col in shape) + 1
    chain_span = template_w + sum(template_w - 1 + gap for gap in gaps)
    marker_span = sum(gaps) + 1
    height = max(9, template_h + 6)
    width = max(10, chain_span + 2, marker_span + 2)
    if height > 30 or width > 30:
        raise ValueError(f"requested axes require {height}x{width}, outside ARC's 30x30 limit")
    return height, width


def _build_horizontal(
    rng,
    *,
    height: int,
    width: int,
    shape: tuple[tuple[int, int], ...],
    gaps: tuple[int, ...],
    anchor: int,
    template_color: int,
    marker_colors: list[int],
) -> list[list[int]]:
    template_h = max(row for row, _ in shape) + 1
    template_w = max(col for _, col in shape) + 1
    offsets = _offsets(len(marker_colors), anchor, gaps, template_w)
    chain_span = max(offsets) - min(offsets) + template_w
    if chain_span > width:
        raise ValueError(f"copy chain width {chain_span} exceeds canvas width {width}")
    marker_span = sum(gaps)
    if marker_span >= width:
        raise ValueError(f"marker span {marker_span} exceeds canvas width {width}")

    leftmost = rng.randint(0, width - chain_span)
    template_col = leftmost - min(offsets)
    marker_start = rng.randint(0, width - marker_span - 1)
    marker_row = rng.randint(0, min(2, height - template_h - 3))
    min_template_row = marker_row + 3
    max_template_row = height - template_h
    if min_template_row > max_template_row:
        raise ValueError("canvas has no separated template band")
    template_row = rng.randint(min_template_row, max_template_row)

    grid = full_grid(height, width, 0)
    for dr, dc in shape:
        grid[template_row + dr][template_col + dc] = template_color
    marker_col = marker_start
    for index, color in enumerate(marker_colors):
        grid[marker_row][marker_col] = color
        if index < len(gaps):
            marker_col += gaps[index]
    return grid


def _transpose(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid)]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Generate one lawful input grid with exact-or-loud public controls."""
    _validate_public_inputs(seed, sample_index, difficulty, overrides)
    band = difficulty or "medium"
    profile_index = sample_index % 4
    final_h, final_w, target_palette, scheduled_orientation, scheduled_n, scheduled_size = (
        _LAYOUT_SCHEDULE[profile_index]
    )

    # A lone anchor override remains constructive by raising the default marker
    # count as needed. An explicit incompatible pair is rejected structurally.
    requested_anchor = overrides.get("anchor_pos")
    if "n_markers" not in overrides and requested_anchor is not None:
        scheduled_n = max(scheduled_n, requested_anchor + 1)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    orientation = _draw_scheduled_choice(ctx, "orientation", ORIENTATIONS, scheduled_orientation)
    n_markers = _draw_scheduled_int(ctx, "n_markers", 2, 5, scheduled_n)
    template_size = _draw_scheduled_int(ctx, "template_size", 3, 7, scheduled_size)
    scheduled_anchor = _anchor_for_phase(_ANCHOR_PHASES[profile_index], n_markers)
    anchor_pos = _draw_scheduled_int(ctx, "anchor_pos", 0, n_markers - 1, scheduled_anchor)
    if anchor_pos >= n_markers:
        raise IncompatibleOverrides(
            f"anchor_pos={anchor_pos} is incompatible with n_markers={n_markers}"
        )

    rng = ctx.draw_rng(f"layout:{band}")
    shape = _shape_for(template_size, rng, band)
    default_path = not overrides
    if default_path:
        gaps = tuple(_PROFILE_GAPS[band][profile_index])
        base_height, base_width = (
            (final_h, final_w) if orientation == "horizontal" else (final_w, final_h)
        )
    else:
        template_w = max(col for _, col in shape) + 1
        gaps = _custom_gaps(n_markers, rng, band, template_w)
        base_height, base_width = _fit_custom_dimensions(shape, gaps)

    template_color, other_colors = _palette(
        rng,
        palette_size=target_palette,
        n_markers=n_markers,
        template_is_two=(profile_index == 3),
    )
    marker_colors = _marker_colors(
        n_markers, anchor_pos, template_color, other_colors
    )
    grid = _build_horizontal(
        rng,
        height=base_height,
        width=base_width,
        shape=shape,
        gaps=gaps,
        anchor=anchor_pos,
        template_color=template_color,
        marker_colors=marker_colors,
    )
    return grid if orientation == "horizontal" else _transpose(grid)


def _validated_grid(grid: Any) -> list[list[int]]:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        raise ValueError("grid must be a nonempty rectangular list")
    width = len(grid[0])
    if not 1 <= len(grid) <= 30 or not 1 <= width <= 30:
        raise ValueError(f"grid dimensions must be in 1..30, got {len(grid)}x{width}")
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("grid rows must be rectangular lists")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("grid values must be integer colors 0..9 (not bool)")
    return [list(row) for row in grid]


def _components8_by_color(grid: list[list[int]]) -> list[dict[str, Any]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[dict[str, Any]] = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr == dc == 0:
                            continue
                        nr, nc = rr + dr, cc + dc
                        if (0 <= nr < height and 0 <= nc < width
                                and (nr, nc) not in seen and grid[nr][nc] == color):
                            seen.add((nr, nc))
                            stack.append((nr, nc))
            components.append({"color": color, "cells": tuple(sorted(cells)), "size": len(cells)})
    return components


def _analyze(grid: Any, *, require_background_targets: bool = True) -> dict[str, Any]:
    normalized = _validated_grid(grid)
    height, width = len(normalized), len(normalized[0])
    components = sorted(
        _components8_by_color(normalized),
        key=lambda component: component["size"],
        reverse=True,
    )
    if len(components) < 3:
        raise ValueError("expected one template and at least two singleton markers")
    template = components[0]
    if template["size"] < 3:
        raise ValueError(f"template has only {template['size']} cells")
    if components[1]["size"] >= template["size"]:
        raise ValueError("largest template component is not unique")
    if any(component["size"] != 1 for component in components[1:]):
        raise ValueError("every non-template component must be a singleton marker")

    markers = [
        {"color": component["color"], "row": component["cells"][0][0], "col": component["cells"][0][1]}
        for component in components[1:]
    ]
    same_row = len({marker["row"] for marker in markers}) == 1
    same_col = len({marker["col"] for marker in markers}) == 1
    if same_row == same_col:
        raise ValueError("markers must be collinear on exactly one row or one column")
    orientation = "horizontal" if same_row else "vertical"
    key: Callable[[dict[str, int]], int] = (
        (lambda marker: marker["col"]) if same_row else (lambda marker: marker["row"])
    )
    markers.sort(key=key)
    coordinates = [key(marker) for marker in markers]
    gaps = tuple(right - left for left, right in zip(coordinates, coordinates[1:]))
    if any(gap < 2 for gap in gaps):
        raise ValueError(f"marker gaps must be at least two, got {gaps}")

    anchors = [index for index, marker in enumerate(markers)
               if marker["color"] == template["color"]]
    if len(anchors) != 1:
        raise ValueError(
            f"expected exactly one template-colour marker, found {len(anchors)}"
        )
    anchor_pos = anchors[0]
    row0 = min(row for row, _ in template["cells"])
    col0 = min(col for _, col in template["cells"])
    row1 = max(row for row, _ in template["cells"])
    col1 = max(col for _, col in template["cells"])
    pattern = _normalize(template["cells"])
    template_h, template_w = row1 - row0 + 1, col1 - col0 + 1

    if orientation == "horizontal":
        relative = _offsets(len(markers), anchor_pos, gaps, template_w)
        positions = [(row0, col0 + offset) for offset in relative]
    else:
        relative = _offsets(len(markers), anchor_pos, gaps, template_h)
        positions = [(row0 + offset, col0) for offset in relative]

    copy_cells: list[tuple[tuple[int, int], ...]] = []
    for index, (copy_row, copy_col) in enumerate(positions):
        cells = tuple((copy_row + dr, copy_col + dc) for dr, dc in pattern)
        if any(not (0 <= row < height and 0 <= col < width) for row, col in cells):
            raise ValueError(f"derived copy {index} leaves the grid")
        if index != anchor_pos and require_background_targets:
            occupied = [(row, col) for row, col in cells if normalized[row][col] != 0]
            if occupied:
                raise ValueError(f"derived copy {index} overlaps input foreground at {occupied[:3]}")
        copy_cells.append(cells)

    return {
        "grid": normalized,
        "height": height,
        "width": width,
        "template": template,
        "template_color": template["color"],
        "template_size": template["size"],
        "template_h": template_h,
        "template_w": template_w,
        "pattern": pattern,
        "markers": markers,
        "n_markers": len(markers),
        "orientation": orientation,
        "anchor_pos": anchor_pos,
        "gaps": gaps,
        "positions": positions,
        "copy_cells": copy_cells,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Return diagnostics instead of raising for malformed task inputs."""
    del difficulty, meta
    try:
        _analyze(grid)
    except (TypeError, ValueError, IndexError) as exc:
        return [str(exc)]
    return []


def strict_canonical_like(grid) -> list[str]:
    """Narrow task-family contract shared by canonical and generated inputs."""
    errors = self_check(grid)
    if errors:
        return errors
    scene = _analyze(grid)
    reasons: list[str] = []
    if not 8 <= scene["height"] <= 30 or not 8 <= scene["width"] <= 30:
        reasons.append("canvas is outside the 8..30 task-family envelope")
    if not 2 <= scene["n_markers"] <= 5:
        reasons.append("marker count is outside 2..5")
    if not 3 <= scene["template_size"] <= 7:
        reasons.append("template size is outside 3..7")
    if scene["template_h"] > 3 or scene["template_w"] > 3:
        reasons.append("template bounding box exceeds 3x3")
    if any(not 2 <= gap <= 5 for gap in scene["gaps"]):
        reasons.append("marker gap is outside 2..5")
    palette_size = len({value for row in scene["grid"] for value in row})
    if not 3 <= palette_size <= 5:
        reasons.append(f"palette size {palette_size} is outside 3..5")
    return reasons


def observe_overrides(grid) -> dict[str, int | str]:
    scene = _analyze(grid)
    return {
        "orientation": scene["orientation"],
        "n_markers": scene["n_markers"],
        "template_size": scene["template_size"],
        "anchor_pos": scene["anchor_pos"],
    }


def semantic_observables(grid) -> dict[str, Any]:
    scene = _analyze(grid)
    return {
        **observe_overrides(grid),
        "height": scene["height"],
        "width": scene["width"],
        "palette_size": len({value for row in scene["grid"] for value in row}),
        "template_color": scene["template_color"],
        "gaps": list(scene["gaps"]),
    }


def _solve_with_anchor(
    grid, anchor_pos: int, *, clip_out_of_bounds: bool = False
) -> list[list[int]]:
    scene = _analyze(grid)
    if type(anchor_pos) is not int or not 0 <= anchor_pos < scene["n_markers"]:
        raise ValueError("rival anchor is outside the marker range")
    # Recompute positions around the rival's assumed anchor while retaining the
    # actual template origin, exactly as the Racket chain construction does.
    template_cells = scene["template"]["cells"]
    row0 = min(row for row, _ in template_cells)
    col0 = min(col for _, col in template_cells)
    axis_size = scene["template_w"] if scene["orientation"] == "horizontal" else scene["template_h"]
    relative = _offsets(scene["n_markers"], anchor_pos, scene["gaps"], axis_size)
    positions = (
        [(row0, col0 + offset) for offset in relative]
        if scene["orientation"] == "horizontal"
        else [(row0 + offset, col0) for offset in relative]
    )
    output = deepcopy(scene["grid"])
    for index, marker in enumerate(scene["markers"]):
        if index == anchor_pos:
            continue
        copy_row, copy_col = positions[index]
        for dr, dc in scene["pattern"]:
            row, col = copy_row + dr, copy_col + dc
            if not (0 <= row < scene["height"] and 0 <= col < scene["width"]):
                if clip_out_of_bounds:
                    continue
                raise ValueError("derived copy leaves the grid")
            output[row][col] = marker["color"]
    return output


def rule_mirror(grid) -> list[list[int]]:
    """Supplementary Python mirror; selected Racket remains label authority."""
    scene = _analyze(grid)
    return _solve_with_anchor(grid, scene["anchor_pos"])


def _rival_fixed_color_two_anchor(grid):
    scene = _analyze(grid)
    assumed = next(
        (index for index, marker in enumerate(scene["markers"]) if marker["color"] == 2),
        scene["anchor_pos"],
    )
    return _solve_with_anchor(grid, assumed, clip_out_of_bounds=True)


def _rival_endpoint_only_anchor(grid):
    scene = _analyze(grid)
    assumed = (
        scene["anchor_pos"]
        if scene["anchor_pos"] in {0, scene["n_markers"] - 1}
        else 0
    )
    return _solve_with_anchor(grid, assumed, clip_out_of_bounds=True)


SEMANTIC_RIVALS = {
    "fixed_color_two_anchor": _rival_fixed_color_two_anchor,
    "endpoint_only_anchor": _rival_endpoint_only_anchor,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _witness(grid, rival_name: str, predicate: Callable[[dict[str, Any]], bool]) -> bool:
    try:
        scene = _analyze(grid)
        return bool(predicate(scene) and SEMANTIC_RIVALS[rival_name](grid) != rule_mirror(grid))
    except (TypeError, ValueError, IndexError):
        return False


SEMANTIC_WITNESSES = {
    "non_two_template_anchor": lambda grid: _witness(
        grid,
        "fixed_color_two_anchor",
        lambda scene: scene["template_color"] != 2
        and any(marker["color"] == 2 for marker in scene["markers"]),
    ),
    "interior_anchor": lambda grid: _witness(
        grid,
        "endpoint_only_anchor",
        lambda scene: 0 < scene["anchor_pos"] < scene["n_markers"] - 1,
    ),
}
WITNESS_RIVALS = {
    "non_two_template_anchor": ["fixed_color_two_anchor"],
    "interior_anchor": ["endpoint_only_anchor"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Report surviving declared rivals for a materialized demonstration set."""
    reasons: list[str] = []
    for index, demo in enumerate(demos):
        try:
            expected = rule_mirror(demo["input"])
        except (KeyError, TypeError, ValueError) as exc:
            reasons.append(f"demo {index} is outside the task grammar: {exc}")
            continue
        if demo.get("output") != expected:
            reasons.append(f"demo {index} output disagrees with the template-chain rule")
    try:
        query_expected = rule_mirror(query["input"])
    except (KeyError, TypeError, ValueError) as exc:
        reasons.append(f"query is outside the task grammar: {exc}")
        return reasons
    if query.get("output") is not None and query.get("output") != query_expected:
        reasons.append("query output disagrees with the template-chain rule")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        try:
            fits = all(competitor(demo["input"]) == demo["output"] for demo in demos)
            changes_query = competitor(query["input"]) != query_expected
        except (KeyError, TypeError, ValueError):
            continue
        if fits and changes_query:
            reasons.append(
                f"competitor {name!r} fits every demonstration but changes the query"
            )
    return reasons


def mutation_fixtures() -> list[tuple[str, list[list[int]]]]:
    """Task-linked malformed inputs that structural validation must reject."""
    valid = generate(8162, 1, difficulty="medium")
    scene = _analyze(valid)
    height, width = len(valid), len(valid[0])

    blank = full_grid(height, width, 0)

    template_only = deepcopy(valid)
    for marker in scene["markers"]:
        template_only[marker["row"]][marker["col"]] = 0

    markers_only = deepcopy(valid)
    for row, col in scene["template"]["cells"]:
        markers_only[row][col] = 0

    noncollinear = deepcopy(valid)
    marker = scene["markers"][0]
    new_row = marker["row"] + (2 if marker["row"] + 2 < height else -2)
    noncollinear[marker["row"]][marker["col"]] = 0
    noncollinear[new_row][marker["col"]] = marker["color"]

    duplicate_anchor = deepcopy(valid)
    marker = next(marker for index, marker in enumerate(scene["markers"])
                  if index != scene["anchor_pos"])
    duplicate_anchor[marker["row"]][marker["col"]] = scene["template_color"]

    close_markers = deepcopy(valid)
    first, second = scene["markers"][:2]
    close_markers[second["row"]][second["col"]] = 0
    if scene["orientation"] == "horizontal":
        close_markers[first["row"]][first["col"] + 1] = second["color"]
    else:
        close_markers[first["row"] + 1][first["col"]] = second["color"]

    bad_color = deepcopy(valid)
    bad_color[0][0] = 10

    return [
        ("blank_grid", blank),
        ("template_without_markers", template_only),
        ("markers_without_template", markers_only),
        ("noncollinear_markers", noncollinear),
        ("two_template_colour_markers", duplicate_anchor),
        ("adjacent_markers", close_markers),
        ("out_of_range_colour", bad_color),
    ]
